"""
World Bank Chatbot - FastAPI Application Main
(Pattern aligné sur le projet AAA)
"""

import uuid
import os
import re
from datetime import datetime, timedelta
import asyncio
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import logging

from core.config_loader import load_config
from core.embeddings_loader import load_vector_store
from core.llm_handler import setup_llm
from core.memory_manager import conversation_memory, cleanup_task, build_chat_history
from core.system_prompt import SYSTEM_PROMPT
from core.agent_orchestrator import create_agent_executor, invoke_agent_with_retry
from core.faq_handler import faq_handler
from models.request_models import QueryRequest

# -----------------------------
# Load config
# -----------------------------
config = load_config("config.json")

# logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("worldbank")

# -----------------------------
# Rate limiter
# -----------------------------
limiter = Limiter(key_func=get_remote_address)

# -----------------------------
# Fallback HTML (FR / EN)
# -----------------------------
FALLBACK_HTML_FR = (
    "<p>Je n'ai pas trouvé cette information dans ma base actuelle.</p>"
    "<p>Souhaitez-vous :</p>"
    "<ul>"
    "<li>📊 Consulter directement <a href=\"https://data.worldbank.org\">data.worldbank.org</a></li>"
    "<li>Reformuler votre question ?</li>"
    "</ul>"
)

FALLBACK_HTML_EN = (
    "<p>I couldn't find that information in my current database.</p>"
    "<p>Would you like to:</p>"
    "<ul>"
    "<li>📊 Check directly on <a href=\"https://data.worldbank.org\">data.worldbank.org</a></li>"
    "<li>Rephrase your question?</li>"
    "</ul>"
)

# -----------------------------
# Initialize components
# -----------------------------
retriever = load_vector_store(config)
model = setup_llm(config)
agent_executor = create_agent_executor(model, retriever, SYSTEM_PROMPT)

INACTIVITY_TIMEOUT = timedelta(minutes=config.get("inactivity_timeout_minutes", 5))
CHECK_INTERVAL = config.get("inactivity_check_interval_seconds", 360)
MAX_PAIRS = config.get("max_pairs", 5)
DATA_FILE = config.get("data_file", "data/world_bank_data.json")
last_modified_time = os.path.getmtime(DATA_FILE) if os.path.exists(DATA_FILE) else 0
NORMALIZATION_MAP = config.get("NORMALIZATION_MAP", {})


# -----------------------------
# FastAPI app
# -----------------------------
app = FastAPI(title="World Bank RAG Chatbot API")
app.state.limiter = limiter

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"answer": "<p>Too many requests. Please wait a minute before retrying.</p>"}
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    logger.info("🟢 Starting up: launching cleanup task")
    asyncio.create_task(cleanup_task(INACTIVITY_TIMEOUT, CHECK_INTERVAL))


def check_and_reload_vector_store():
    """Reload FAISS retriever if data file has changed."""
    global retriever, last_modified_time, agent_executor
    try:
        if not os.path.exists(DATA_FILE):
            return
        current_mtime = os.path.getmtime(DATA_FILE)
        if current_mtime != last_modified_time:
            logger.info("Detected update in %s, reloading vector store...", DATA_FILE)
            retriever = load_vector_store(config)
            agent_executor = create_agent_executor(model, retriever, SYSTEM_PROMPT)
            last_modified_time = current_mtime
            logger.info("Vector store reloaded successfully")
    except FileNotFoundError:
        logger.warning("Data file not found: %s", DATA_FILE)
    except Exception as e:
        logger.error("Failed to reload vector store: %s", e)


def normalize_query(query: str) -> str:
    """Normalize user query safely, avoiding replacements inside words."""
    query_clean = re.sub(r"[/\\|]", " ", query)
    query_lower = query_clean.lower()
    for key, value in NORMALIZATION_MAP.items():
        pattern = r"\b" + re.escape(key) + r"\b"
        query_lower = re.sub(pattern, value.lower(), query_lower)
    return query_lower


@app.post("/query")
@limiter.limit("20/minute")
async def ask_question(request: Request, body: QueryRequest):
    now = datetime.utcnow()
    user_id = body.user_id or str(uuid.uuid4())
    logger.info("Request from user_id: %s", user_id)
    check_and_reload_vector_store()

    normalized_query = normalize_query(body.query)
    logger.info("Normalized Query: %s", normalized_query)

    # --- Check FAQ for deterministic responses ---
    lang = (body.lang or "fr").lower()
    faq_response = faq_handler.check_faq(body.query, lang)
    if faq_response:
        history_pairs = conversation_memory.get(user_id, {}).get("history", [])
        history_pairs.append({"A": body.query, "B": faq_response})
        conversation_memory[user_id] = {"history": history_pairs[-MAX_PAIRS:], "last_active": now}
        return JSONResponse({"answer": faq_response, "user_id": user_id})

    # --- Language ---
    lang_name = "English" if lang.startswith("en") else "French"
    query_with_lang = f"[Language: {lang}] Please answer in {lang_name}. {normalized_query}"

    # --- History ---
    history_pairs = conversation_memory.get(user_id, {}).get("history", [])
    chat_history = build_chat_history(history_pairs)

    # --- Agent call ---
    try:
        response = invoke_agent_with_retry(agent_executor, query_with_lang, chat_history)
    except Exception as e:
        logger.exception("LLM invocation failed")
        raise HTTPException(status_code=500, detail=str(e))

    # --- Fallback / Enforcement ---
    req_lang = (body.lang or "fr").lower()
    fallback_full = FALLBACK_HTML_EN if req_lang.startswith("en") else FALLBACK_HTML_FR
    cta_only_fr = '<p>Pour plus d\'informations : <a href="https://data.worldbank.org">data.worldbank.org</a></p>'
    cta_only_en = '<p>For more information: <a href="https://data.worldbank.org">data.worldbank.org</a></p>'
    cta_only = cta_only_en if req_lang.startswith("en") else cta_only_fr

    REFUSAL_PATTERNS = [
        "je ne peux pas fournir",
        "i cannot provide",
        "je ne suis pas autoris",
        "i am not authorized",
        "je suis prêt à répondre",
        "i'm ready to answer",
        "i am ready to answer",
        "⚠️ pour votre sécurité",
    ]

    if not response or not response.strip():
        answer = fallback_full
    else:
        resp_lower = response.lower()
        is_refusal = any(p in resp_lower for p in REFUSAL_PATTERNS)
        has_wb_link = 'data.worldbank.org' in resp_lower

        if is_refusal:
            answer = response
        elif has_wb_link:
            answer = response
        else:
            if len(response.strip()) > 50:
                answer = response + "\n\n" + cta_only
            else:
                answer = response + "\n\n" + fallback_full

    # --- Update memory ---
    history_pairs.append({"A": body.query, "B": answer})
    conversation_memory[user_id] = {
        "history": history_pairs[-MAX_PAIRS:],
        "last_active": now
    }
    logger.info("Memory size: %d active sessions", len(conversation_memory))

    return JSONResponse({"answer": answer, "user_id": user_id})


@app.get("/health")
async def health_check():
    return {"status": "healthy", "project": "World Bank Chatbot", "timestamp": datetime.utcnow().isoformat()}


if __name__ == "__main__":
    import uvicorn
    server_cfg = config.get("server", {})
    uvicorn.run(
        "app:app",
        host=server_cfg.get("host", "0.0.0.0"),
        port=server_cfg.get("port", 8000),
        reload=server_cfg.get("reload", True)
    )
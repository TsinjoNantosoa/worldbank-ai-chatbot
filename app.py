"""
World Bank Chatbot - FastAPI Application Main

Portfolio project: RAG chatbot for World Bank development data
"""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from core import (
    load_config,
    load_vector_store,
    setup_llm,
    conversation_memory,
    build_chat_history,
    cleanup_task,
    create_agent_executor,
    invoke_agent_with_retry,
    SYSTEM_PROMPT,
    normalize_query
)
from models import QueryRequest, QueryResponse

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

# ========== INITIALIZATION ==========

logger.info("🚀 Starting World Bank Chatbot...")

# Load configuration
config = load_config()
logger.info(f"✅ Configuration loaded: {config.get('project_name')}")

# Load vector store
vector_store = load_vector_store(config)
retriever = vector_store.as_retriever(search_kwargs={"k": 4})
logger.info("✅ Vector store loaded")

# Setup LLM
llm = setup_llm(config)
logger.info("✅ LLM configured")

# Create agent executor
agent_executor = create_agent_executor(llm, retriever, SYSTEM_PROMPT)
logger.info("✅ Agent executor ready")

# ========== FASTAPI APP ==========

app = FastAPI(
    title="World Bank Data Chatbot",
    description="Portfolio project: Ask questions about World Bank development indicators",
    version="1.0.0"
)

# CORS (development: allow all, production: restrict)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Static files
STATIC_DIR = Path(__file__).parent / "static"
STATIC_DIR.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Templates
TEMPLATES_DIR = Path(__file__).parent / "templates"
TEMPLATES_DIR.mkdir(exist_ok=True)
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# ========== STARTUP/SHUTDOWN ==========

@app.on_event("startup")
async def startup_event():
    """
    Démarre les tâches de fond au démarrage
    """
    logger.info("🔧 Starting background tasks...")
    
    # Cleanup task pour memory management
    inactivity_timeout = timedelta(minutes=5)
    asyncio.create_task(cleanup_task(inactivity_timeout, check_interval=60))
    
    logger.info("✅ Background tasks started")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Cleanup au shutdown
    """
    logger.info("🛑 Shutting down...")


# ========== ROUTES ==========

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """
    Page d'accueil avec interface chatbot
    """
    return templates.TemplateResponse("base.html", {
        "request": request,
        "project_name": config.get("project_name", "World Bank Chatbot")
    })


@app.post("/query", response_model=QueryResponse)
async def query_endpoint(query_request: QueryRequest):
    """
    Endpoint principal: traite les questions utilisateurs
    
    Args:
        query_request: QueryRequest avec query et user_id optionnel
        
    Returns:
        QueryResponse avec answer HTML
    """
    try:
        # User ID
        user_id = query_request.user_id or str(uuid.uuid4())
        
        logger.info(f"📩 Query from {user_id}: {query_request.query[:100]}")
        
        # Normaliser query
        normalized_query = normalize_query(
            query_request.query,
            config.get("normalization_map")
        )
        
        # Récupérer historique conversation
        chat_history = build_chat_history(user_id)
        
        # Invoquer agent
        answer = invoke_agent_with_retry(
            agent_executor,
            normalized_query,
            chat_history
        )
        
        # Sauvegarder dans mémoire
        if user_id not in conversation_memory:
            conversation_memory[user_id] = {"history": [], "last_active": datetime.utcnow()}
        
        conversation_memory[user_id]["history"].append({
            "user": query_request.query,
            "assistant": answer
        })
        conversation_memory[user_id]["last_active"] = datetime.utcnow()
        
        logger.info(f"✅ Response sent to {user_id} ({len(answer)} chars)")
        
        return QueryResponse(
            answer=answer,
            user_id=user_id,
            success=True
        )
        
    except Exception as e:
        logger.error(f"❌ Error processing query: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.get("/health")
async def health_check():
    """
    Health check endpoint pour Docker/monitoring
    """
    return {
        "status": "healthy",
        "project": config.get("project_name"),
        "timestamp": datetime.utcnow().isoformat()
    }


# ========== MAIN (local dev) ==========

if __name__ == "__main__":
    import uvicorn
    
    host = config.get("server", {}).get("host", "0.0.0.0")
    port = config.get("server", {}).get("port", 8000)
    
    logger.info(f"🌐 Starting server at http://{host}:{port}")
    
    uvicorn.run(
        "app:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )

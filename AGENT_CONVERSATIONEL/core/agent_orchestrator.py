"""
Agent Orchestrator - Crée et invoque l'agent LangChain avec outils RAG

Construction de l'agent avec retrieval tools et gestion des retries
(Pattern aligné sur le projet AAA)
"""

from __future__ import annotations

import time
import logging
from typing import Any, Dict, List

from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import Tool
from langchain_openai import ChatOpenAI
from langchain.schema import Document

logger = logging.getLogger(__name__)


def _format_docs(docs: List[Document]) -> str:
    """Compact text snippets with their source identifiers."""
    formatted_chunks = []
    for doc in docs:
        source = doc.metadata.get("source") or doc.metadata.get("source_key") or "World Bank Knowledge Base"
        snippet = doc.page_content.strip()
        if len(snippet) > 900:
            snippet = snippet[:900].rstrip() + "..."
        formatted_chunks.append(f"Source: {source}\n{snippet}")
    return "\n\n".join(formatted_chunks)


def _collect_sources(docs: List[Document]) -> str:
    """Return a bullet list of unique source links referenced by the retriever."""
    urls = []
    seen = set()
    for doc in docs:
        url = doc.metadata.get("source")
        if url and url not in seen:
            seen.add(url)
            urls.append(f"- {url}")
    if not urls:
        return "No explicit links detected in the retrieved context."
    return "Cite the following official URLs in your HTML response:\n" + "\n".join(urls)


def _build_retrieval_tool(retriever) -> Tool:
    def search(query: str) -> str:
        docs = retriever.get_relevant_documents(query)
        if not docs:
            return (
                "No context found. If this happens, fall back to the policy-compliant "
                "contact redirection specified in the system prompt."
            )
        return _format_docs(docs)

    return Tool(
        name="WB_Knowledge_Search",
        description=(
            "Use this to research any factual detail about World Bank development indicators, "
            "countries, economic data, social data, and environmental statistics. Always call this "
            "tool before finalizing an answer that requires grounded data."
        ),
        func=search,
    )


def _build_source_tool(retriever) -> Tool:
    def collect(query: str) -> str:
        docs = retriever.get_relevant_documents(query)
        return _collect_sources(docs)

    return Tool(
        name="WB_Source_Collector",
        description=(
            "Use after retrieving knowledge to list the official World Bank URLs you must cite in the final HTML. "
            "Mandatory whenever you mention an indicator, country, or statistic."
        ),
        func=collect,
    )


def create_agent_executor(model: ChatOpenAI, retriever, system_prompt: str) -> AgentExecutor:
    """Create a LangChain tools agent that separates research and response duties."""
    tools = [_build_retrieval_tool(retriever), _build_source_tool(retriever)]

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                system_prompt
                + "\n\nYou are the orchestrator. Call tools whenever you need facts or sources before answering.",
            ),
            MessagesPlaceholder(variable_name="chat_history"),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )

    agent = create_openai_tools_agent(model, tools, prompt)
    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=False,
        handle_parsing_errors=True,
        max_iterations=7,
        max_execution_time=20,
        early_stopping_method="force",
        return_intermediate_steps=False,
    )


# Bilingual fallback returned when the agent hits max_iterations or execution timeout
_ITERATION_FALLBACK_FR = (
    "<p>Je n'ai pas pu finaliser ma réponse dans le temps imparti.<br>"
    "Pour plus d'informations, consultez : "
    "<a href=\"https://data.worldbank.org\">le site de la Banque Mondiale</a>.</p>"
)
_ITERATION_FALLBACK_EN = (
    "<p>I was unable to finalize a response within the allowed time.<br>"
    "For more information, please visit: "
    "<a href=\"https://data.worldbank.org\">the World Bank website</a>.</p>"
)

# Patterns that indicate LangChain stopped the agent without a real answer
_AGENT_STOPPED_SIGNALS = [
    "agent stopped due to max iterations",
    "agent stopped due to max execution time",
    "agent stopped due to iteration limit",
    "stopped agent prematurely",
]


def _is_iteration_stop(output: str) -> bool:
    low = output.lower()
    return any(sig in low for sig in _AGENT_STOPPED_SIGNALS)


def invoke_agent_with_retry(
    agent_executor: AgentExecutor,
    input_query: str,
    chat_history: List[Dict[str, str]] | None = None,
    max_retries: int = 2,
    wait_time: int = 1,
) -> str:
    """Invoke the orchestrated agent, retrying on transient errors."""
    chat_history = chat_history or []

    # Language detection → inject system message for the agent
    try:
        lower_q = input_query.lower()
        if "please answer in english" in lower_q or "[language: en]" in lower_q:
            chat_history.insert(0, {"role": "system", "content": "Please answer in English."})
        elif "please answer in french" in lower_q or "[language: fr]" in lower_q:
            chat_history.insert(0, {"role": "system", "content": "Veuillez répondre en français."})
    except Exception:
        pass

    for attempt in range(max_retries):
        try:
            result = agent_executor.invoke({"input": input_query, "chat_history": chat_history})
            output = result.get("output")
            if not isinstance(output, str):
                output = str(output)

            # Replace LangChain's internal stop message with a friendly bilingual fallback
            if _is_iteration_stop(output):
                is_en = (
                    "[language: en]" in input_query.lower()
                    or "please answer in english" in input_query.lower()
                )
                return _ITERATION_FALLBACK_EN if is_en else _ITERATION_FALLBACK_FR
            return output

        except Exception as exc:
            err_msg = str(exc)
            if "429" in err_msg or "Timeout" in err_msg or "timeout" in err_msg.lower():
                time.sleep(wait_time * (2 ** attempt))
                continue
            # For iteration / execution-time exceptions raised by LangChain
            if "max iterations" in err_msg.lower() or "max execution" in err_msg.lower():
                is_en = (
                    "[language: en]" in input_query.lower()
                    or "please answer in english" in input_query.lower()
                )
                return _ITERATION_FALLBACK_EN if is_en else _ITERATION_FALLBACK_FR
            raise

    raise RuntimeError("Max retries exceeded for agent invocation.")

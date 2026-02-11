"""
Agent Orchestrator - Crée et invoque l'agent LangChain avec outils RAG

Construction de l'agent avec retrieval tools et gestion des retries
"""

import logging
from typing import Any, Dict, List
from tenacity import retry, stop_after_attempt, wait_exponential

from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.tools import Tool
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import Document

logger = logging.getLogger(__name__)


def _format_docs(docs: List[Document]) -> str:
    """
    Formate les documents récupérés pour le prompt
    
    Args:
        docs: Documents depuis retriever
        
    Returns:
        String formaté
    """
    if not docs:
        return "No relevant information found in the knowledge base."
    
    formatted = []
    for i, doc in enumerate(docs, 1):
        content = doc.page_content[:500]  # Tronquer si trop long
        source = doc.metadata.get("source", "Unknown")
        formatted.append(f"[{i}] {content}\n    Source: {source}")
    
    return "\n\n".join(formatted)


def _collect_sources(docs: List[Document]) -> str:
    """
    Collecte les URLs sources des documents
    
    Args:
        docs: Documents
        
    Returns:
        String avec URLs uniques
    """
    sources = set()
    for doc in docs:
        source_url = doc.metadata.get("source")
        if source_url:
            sources.add(source_url)
    
    return "\n".join(f"- {url}" for url in sorted(sources))


def _build_retrieval_tool(retriever) -> Tool:
    """
    Crée l'outil de recherche knowledge base
    
    Args:
        retriever: FAISS retriever
        
    Returns:
        Tool LangChain
    """
    def search_knowledge_base(query: str) -> str:
        """Search World Bank data for relevant information"""
        docs = retriever.get_relevant_documents(query)
        return _format_docs(docs)
    
    return Tool(
        name="WB_Knowledge_Search",
        func=search_knowledge_base,
        description="Search the World Bank knowledge base for indicators, country data, methodologies. Input should be a search query."
    )


def _build_source_tool(retriever) -> Tool:
    """
    Crée l'outil de collecte des sources
    
    Args:
        retriever: FAISS retriever
        
    Returns:
        Tool LangChain
    """
    def get_sources(query: str) -> str:
        """Get source URLs for citations"""
        docs = retriever.get_relevant_documents(query)
        return _collect_sources(docs)
    
    return Tool(
        name="WB_Source_Collector",
        func=get_sources,
        description="Collect source URLs for citation. Input should be the same query used in knowledge search."
    )


def create_agent_executor(model, retriever, system_prompt: str) -> AgentExecutor:
    """
    Crée l'agent executor avec outils RAG
    
    Args:
        model: ChatOpenAI instance
        retriever: FAISS retriever
        system_prompt: System prompt
        
    Returns:
        AgentExecutor configuré
    """
    logger.info("Creating agent executor...")
    
    # Outils disponibles
    tools = [
        _build_retrieval_tool(retriever),
        _build_source_tool(retriever)
    ]
    
    # Prompt template
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="chat_history", optional=True),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad")
    ])
    
    # Créer agent
    agent = create_openai_tools_agent(model, tools, prompt)
    
    # Executor
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        max_iterations=5,
        early_stopping_method="generate"
    )
    
    logger.info("✅ Agent executor created")
    
    return agent_executor


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def invoke_agent_with_retry(
    agent_executor: AgentExecutor,
    input_query: str,
    chat_history: str = ""
) -> str:
    """
    Invoque l'agent avec retry automatique
    
    Args:
        agent_executor: Agent
        input_query: Query normalisée
        chat_history: Historique formaté
        
    Returns:
        Réponse de l'agent
    """
    logger.info(f"Invoking agent with query: {input_query[:100]}...")
    
    try:
        result = agent_executor.invoke({
            "input": input_query,
            "chat_history": chat_history
        })
        
        answer = result.get("output", "")
        logger.info(f"Agent returned {len(answer)} chars")
        
        return answer
        
    except Exception as e:
        logger.error(f"Agent invocation failed: {e}")
        raise

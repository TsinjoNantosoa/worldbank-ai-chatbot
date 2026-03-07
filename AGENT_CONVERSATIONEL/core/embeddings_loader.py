"""
Embeddings Loader - Charge/Crée index FAISS depuis world_bank_data.json

Gestion du vector store et des embeddings OpenAI
(Pattern aligné sur le projet AAA)
"""

import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any

from langchain_community.vectorstores import FAISS
from langchain.schema import Document
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

api_key = os.getenv("OPENAI_API_KEY")


class DummyRetriever:
    """Fallback retriever that returns no documents."""

    def get_relevant_documents(self, query: str):
        return []


def load_vector_store(config: dict):
    """
    Build a FAISS retriever from the JSON data file.
    Supports both list-of-categories format (AAA style) and dict-based format.
    """
    embeddings = OpenAIEmbeddings(
        model=config.get("embedding_model", "text-embedding-3-large"),
        openai_api_key=config.get("openai_api_key") or os.getenv("OPENAI_API_KEY")
    )

    vector_store = None
    data_file = config.get("data_file", "data/world_bank_data.json")

    # Try several locations for the data file: as given, relative to project, and CWD
    pf = Path(data_file)
    resolved = None
    if pf.exists():
        resolved = pf
    else:
        # relative to repository package root (one level above core/)
        repo_rel = Path(__file__).resolve().parents[1] / data_file
        if repo_rel.exists():
            resolved = repo_rel
        else:
            cwd_rel = Path.cwd() / data_file
            if cwd_rel.exists():
                resolved = cwd_rel

    if resolved is None:
        logger.warning("Data file not found: %s. Returning empty retriever.", data_file)
        return DummyRetriever()

    with open(resolved, "r", encoding="utf-8") as f:
        json_data = json.load(f)

    logger.info(f"Loading data from {data_file}")

    # Support list-of-categories format (like AAA: [{category, pages: [{content, url}]}])
    if isinstance(json_data, list):
        for item in json_data:
            key = item.get("category", "unknown")
            pages = item.get("pages", [])

            docs = [
                Document(
                    page_content=page.get("content", ""),
                    metadata={"source": page.get("url", ""), "source_key": key}
                )
                for page in pages
                if page.get("content", "")
            ]

            if docs:
                if vector_store is None:
                    vector_store = FAISS.from_documents(docs, embeddings)
                else:
                    vector_store.add_documents(docs)

    # Support dict-based format (with categories/country_data keys)
    elif isinstance(json_data, dict):
        docs = _create_documents_from_dict(json_data)
        if docs:
            vector_store = FAISS.from_documents(docs, embeddings)

    if vector_store is None:
        raise ValueError("No documents found in data file — cannot build vector store")

    logger.info("✅ Vector store built successfully")
    return vector_store.as_retriever(search_kwargs={"k": 5})


def _create_documents_from_dict(data: Dict) -> List[Document]:
    """
    Convertit un dict JSON en liste de Documents LangChain.
    Supports 'categories' and 'country_data' structures.
    """
    documents = []

    if "categories" in data:
        for category in data.get("categories", []):
            cat_name = category.get("category", "unknown")
            for page in category.get("pages", []):
                content = page.get("content", "")
                url = page.get("url", "")
                if not content or len(content) < 20:
                    continue
                doc = Document(
                    page_content=content,
                    metadata={"source": url, "source_key": cat_name}
                )
                documents.append(doc)

    if "country_data" in data:
        for row in data.get("country_data", []):
            snippet = row.get("snippet") or str(row.get("value") or "")
            if not snippet or len(snippet) < 10:
                continue
            metadata = {
                "source": row.get("source_url", ""),
                "source_key": "country_data",
                "indicator_code": row.get("indicator_code"),
                "country_code": row.get("country_code"),
                "year": row.get("year")
            }
            doc = Document(page_content=snippet, metadata=metadata)
            documents.append(doc)

    return documents
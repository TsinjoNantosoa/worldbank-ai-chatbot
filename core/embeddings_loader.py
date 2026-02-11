"""
Embeddings Loader - Charge/Crée index FAISS depuis world_bank_data.json

Gestion du vector store et des embeddings OpenAI
"""

import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any

from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
from langchain.schema import Document

logger = logging.getLogger(__name__)


def load_vector_store(config: Dict[str, Any]):
    """
    Charge ou crée le vector store FAISS depuis data.json
    
    Args:
        config: Configuration dict (doit contenir openai_api_key, embedding_model, data_file)
        
    Returns:
        FAISS retriever configuré
    """
    data_file = Path(config.get("data_file", "data/world_bank_data.json"))
    faiss_index_path = Path("data/faiss_index")
    
    # Initialiser embeddings
    embeddings = OpenAIEmbeddings(
        openai_api_key=config["openai_api_key"],
        model=config.get("embedding_model", "text-embedding-3-large")
    )
    
    logger.info(f"Using embedding model: {config.get('embedding_model')}")
    
    # Charger données
    if not data_file.exists():
        logger.error(f"Data file not found: {data_file}")
        raise FileNotFoundError(f"Data file required: {data_file}")
    
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    logger.info(f"Loaded {len(data.get('categories', []))} categories from {data_file}")
    
    # Convertir en Documents LangChain
    documents = _create_documents_from_data(data)
    
    logger.info(f"Created {len(documents)} documents for indexing")
    
    # Créer ou charger index FAISS
    if faiss_index_path.exists() and (faiss_index_path / "index.faiss").exists():
        logger.info("Loading existing FAISS index...")
        try:
            vector_store = FAISS.load_local(
                str(faiss_index_path),
                embeddings,
                allow_dangerous_deserialization=True
            )
            logger.info("✅ FAISS index loaded successfully")
        except Exception as e:
            logger.warning(f"Failed to load FAISS index: {e}, rebuilding...")
            vector_store = _build_faiss_index(documents, embeddings, faiss_index_path)
    else:
        logger.info("Building new FAISS index...")
        vector_store = _build_faiss_index(documents, embeddings, faiss_index_path)
    
    # Retourner retriever
    retriever = vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 4}  # Top 4 résultats
    )
    
    logger.info("✅ Vector store ready")
    return retriever


def _create_documents_from_data(data: Dict) -> List[Document]:
    """
    Convertit data.json en liste de Documents LangChain
    
    Args:
        data: Dict depuis world_bank_data.json
        
    Returns:
        Liste Documents avec métadonnées
    """
    documents = []
    
    for category in data.get("categories", []):
        cat_name = category.get("category", "unknown")
        cat_description = category.get("description", "")
        
        for page in category.get("pages", []):
            content = page.get("content", "")
            url = page.get("url", "")
            metadata = page.get("metadata", {})
            
            if not content or len(content) < 20:
                continue
            
            # Enrichir métadonnées
            full_metadata = {
                "source": url,
                "category": cat_name,
                "type": metadata.get("type", "data"),
                **metadata
            }
            
            doc = Document(
                page_content=content,
                metadata=full_metadata
            )
            
            documents.append(doc)
    
    return documents


def _build_faiss_index(
    documents: List[Document],
    embeddings: OpenAIEmbeddings,
    save_path: Path
) -> FAISS:
    """
    Construit index FAISS depuis documents et le sauvegarde
    
    Args:
        documents: Liste Documents
        embeddings: Embeddings model
        save_path: Chemin sauvegarde
        
    Returns:
        FAISS vector store
    """
    if len(documents) == 0:
        raise ValueError("Cannot build FAISS index: no documents provided")
    
    logger.info(f"Building FAISS index from {len(documents)} documents...")
    
    # Créer index
    vector_store = FAISS.from_documents(documents, embeddings)
    
    # Sauvegarder
    save_path.mkdir(parents=True, exist_ok=True)
    vector_store.save_local(str(save_path))
    
    logger.info(f"✅ FAISS index saved to {save_path}")
    
    return vector_store


def reload_vector_store_if_needed(
    config: Dict,
    data_file_mtime: float,
    current_retriever
):
    """
    Recharge le vector store si data.json a changé
    
    Args:
        config: Configuration
        data_file_mtime: Timestamp dernière modif connue
        current_retriever: Retriever actuel
        
    Returns:
        (nouveau_retriever, nouveau_mtime) ou (current_retriever, data_file_mtime)
    """
    data_file = Path(config.get("data_file"))
    
    if not data_file.exists():
        return current_retriever, data_file_mtime
    
    current_mtime = data_file.stat().st_mtime
    
    if current_mtime != data_file_mtime:
        logger.info("Data file changed, reloading vector store...")
        new_retriever = load_vector_store(config)
        return new_retriever, current_mtime
    
    return current_retriever, data_file_mtime

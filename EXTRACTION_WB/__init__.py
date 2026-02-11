"""
EXTRACTION_WB - World Bank Data Extraction Module

Collecte et traite les données depuis l'API World Bank
pour alimenter le chatbot RAG.
"""

__version__ = "1.0.0"
__author__ = "Tsinjo"

from .collector import WorldBankCollector
from .processors import (
    clean_text,
    chunk_methodology_text,
    create_data_point_snippet,
    merge_data_incrementally
)
from .utils_http import create_session_with_retries

__all__ = [
    "WorldBankCollector",
    "clean_text",
    "chunk_methodology_text",
    "create_data_point_snippet",
    "merge_data_incrementally",
    "create_session_with_retries"
]

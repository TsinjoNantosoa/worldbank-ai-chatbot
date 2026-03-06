"""
Request/Response Models - Pydantic schemas pour validation FastAPI
(Pattern aligné sur le projet AAA)
"""

from pydantic import BaseModel
from typing import Optional


class QueryRequest(BaseModel):
    """Requête utilisateur vers /query"""
    query: str
    user_id: Optional[str] = None
    lang: Optional[str] = "fr"


class QueryResponse(BaseModel):
    """Réponse du chatbot"""
    answer: str
    user_id: str
    success: bool = True

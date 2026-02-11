"""
Request/Response Models - Pydantic schemas pour validation FastAPI
"""

from pydantic import BaseModel, Field
from typing import Optional


class QueryRequest(BaseModel):
    """
    Requête utilisateur vers /query
    """
    query: str = Field(
        ...,
        description="User question about World Bank data",
        min_length=1,
        max_length=500
    )
    
    user_id: Optional[str] = Field(
        default=None,
        description="Unique user ID for conversation memory (auto-generated if None)"
    )


class QueryResponse(BaseModel):
    """
    Réponse du chatbot
    """
    answer: str = Field(
        ...,
        description="Agent's answer in HTML format"
    )
    
    user_id: str = Field(
        ...,
        description="User ID for this conversation"
    )
    
    success: bool = Field(
        default=True,
        description="Whether the query succeeded"
    )

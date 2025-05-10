"""
Pydantic models for request and response schemas.
"""
from typing import List, Dict, Any
from pydantic import BaseModel

class QuestionRequest(BaseModel):
    """Request model for asking questions."""
    question: str
    session_id: str
    top_k: int = 5
    file_paths: List[str] = []

class QuestionResponse(BaseModel):
    """Response model for question answers."""
    answer: str
    sources: List[Dict[str, Any]] = []
    session_id: str

class DocumentInfo(BaseModel):
    """Model for document information."""
    filename: str
    upload_time: str
    file_path: str
    size: int
    type: str  # Tipo de documento (PDF, TXT, MD, etc.)

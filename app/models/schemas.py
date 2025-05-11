"""
Modelos Pydantic para esquemas de requisição e resposta.
"""
from typing import List, Dict, Any
from pydantic import BaseModel

class QuestionRequest(BaseModel):
    """Modelo de requisição para fazer perguntas."""
    question: str
    session_id: str
    top_k: int = 5
    file_paths: List[str] = []

class QuestionResponse(BaseModel):
    """Modelo de resposta para respostas de perguntas."""
    answer: str
    sources: List[Dict[str, Any]] = []
    session_id: str

class DocumentInfo(BaseModel):
    """Modelo para informações de documentos."""
    filename: str
    upload_time: str
    file_path: str
    size: int
    type: str  # Tipo de documento (PDF, TXT, MD, etc.)

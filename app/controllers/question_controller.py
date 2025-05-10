"""
Question controller for handling question-related endpoints.
"""
from fastapi import APIRouter, HTTPException
from app.models.schemas import QuestionRequest, QuestionResponse
from app.services.ai_service import generate_answer
from app.utils.vector_db import query_vector_db
from app.config.settings import logger

# Create router
router = APIRouter(prefix="/questions", tags=["questions"])

@router.post("/ask", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest) -> QuestionResponse:
    """
    Ask a question and get an answer based on document context.
    
    Args:
        request: Question request
        
    Returns:
        Question response with answer and sources
    """
    try:
        # Extrair parâmetros da requisição
        question = request.question
        session_id = request.session_id
        top_k = request.top_k
        file_paths = request.file_paths
        
        # Verificar se a pergunta foi fornecida
        if not question:
            raise HTTPException(status_code=400, detail="Pergunta não fornecida")
        
        # Consultar banco de dados de vetores para documentos relevantes
        docs = await query_vector_db(question, top_k, file_paths)
        
        # Gerar resposta
        answer = await generate_answer(question, docs)
        
        # Preparar informações de fontes
        sources = [{"content": doc.page_content, "metadata": doc.metadata} for doc in docs]
        
        # Criar resposta
        response = QuestionResponse(
            answer=answer,
            sources=sources,
            session_id=session_id
        )
        
        logger.info(f"Resposta gerada para a pergunta: {question[:50]}...")
        return response
        
    except ValueError as e:
        logger.error(f"Erro de valor: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except Exception as e:
        logger.error(f"Erro ao processar pergunta: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao processar pergunta: {str(e)}")

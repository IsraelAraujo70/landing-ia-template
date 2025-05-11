"""
Controlador de perguntas para manipulação de endpoints relacionados a perguntas.
"""
from fastapi import APIRouter, HTTPException
from app.models.schemas import QuestionRequest, QuestionResponse
from app.services.ai_service import generate_answer
from app.utils.vector_db import query_vector_db
from app.config.settings import logger

# Cria o router - sem prefixo para permitir rotas diretas
router = APIRouter(tags=["questions"])

@router.post("/ask", response_model=QuestionResponse)
@router.post("/questions/ask", response_model=QuestionResponse)  # Rota com prefixo /questions
async def ask_question(request: QuestionRequest) -> QuestionResponse:
    """
    Faz uma pergunta e obtém uma resposta baseada no contexto dos documentos.
    
    Args:
        request: Requisição de pergunta
        
    Retorna:
        Resposta à pergunta com resposta e fontes
    """
    try:
        question = request.question
        session_id = request.session_id
        top_k = request.top_k
        file_paths = request.file_paths
        
        if not question:
            raise HTTPException(status_code=400, detail="Pergunta não fornecida")
        
        docs = await query_vector_db(question, top_k, file_paths)
        
        answer = await generate_answer(question, docs)
        
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

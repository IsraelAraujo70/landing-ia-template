"""
Controlador WebSocket para manipulação de chat em tempo real.
"""
import json
import time
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.models.connection import ConnectionManager
from app.services.ai_service import generate_answer
from app.utils.vector_db import query_vector_db
from app.config.settings import logger

# Cria o router
router = APIRouter(tags=["websocket"])

# Cria o gerenciador de conexões
manager = ConnectionManager()

@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    Endpoint WebSocket para chat em tempo real.
    
    Args:
        websocket: Conexão WebSocket
        session_id: ID da sessão
    """
    logger.info(f"Tentativa de conexão WebSocket em /ws/{session_id}")
    try:
        await manager.connect(websocket, session_id)
        logger.info(f"Conexão WebSocket estabelecida com sucesso em /ws/{session_id}")
    except Exception as e:
        logger.error(f"Erro ao conectar WebSocket em /ws/{session_id}: {str(e)}")
        raise
    
    try:
        while True:
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                
                question = None
                top_k = 5
                file_paths = []
                
                # Suportar ambos os formatos de mensagem
                if message.get("role") == "user" and message.get("content"):
                    question = message["content"]
                    top_k = message.get("top_k", 5)
                    file_paths = message.get("file_paths", [])
                elif message.get("question"):
                    question = message["question"]
                    top_k = message.get("top_k", 5)
                    file_paths = message.get("file_paths", [])
                    
                if question:
                    
                    await manager.send_personal_message(
                        {
                            "role": "user",
                            "content": question,
                            "timestamp": time.time()
                        },
                        session_id
                    )
                    
                    await manager.send_personal_message(
                        {
                            "role": "system",
                            "content": "typing",
                            "typing": True
                        },
                        session_id
                    )
                    
                    try:
                        docs = await query_vector_db(question, top_k, file_paths)
                        
                        chat_history = manager.get_chat_history(session_id)
                        
                        answer = await generate_answer(question, docs, chat_history)
                        
                        sources = [{"content": doc.page_content, "metadata": doc.metadata} for doc in docs]
                        
                        await manager.send_personal_message(
                            {
                                "role": "assistant",
                                "content": answer,
                                "sources": sources,
                                "timestamp": time.time()
                            },
                            session_id
                        )
                        
                    except ValueError as e:
                        logger.error(f"Erro de valor durante o processamento: {str(e)}")
                        await manager.send_personal_message(
                            {
                                "role": "system",
                                "content": str(e),
                                "error": True
                            },
                            session_id
                        )
                        
                    except Exception as e:
                        logger.error(f"Exceção durante o processamento: {str(e)}", exc_info=True)
                        await manager.send_personal_message(
                            {
                                "role": "system",
                                "content": f"Erro ao gerar resposta: {str(e)}",
                                "error": True
                            },
                            session_id
                        )
                
            except json.JSONDecodeError as e:
                logger.error(f"Erro de decodificação JSON: {str(e)}")
                await manager.send_personal_message(
                    {
                        "role": "system",
                        "content": f"Formato JSON inválido: {str(e)}",
                        "error": True
                    },
                    session_id
                )
                
            except Exception as e:
                logger.error(f"Erro inesperado: {str(e)}", exc_info=True)
                await manager.send_personal_message(
                    {
                        "role": "system",
                        "content": f"Erro inesperado: {str(e)}",
                        "error": True
                    },
                    session_id
                )
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket desconectado para a sessão {session_id}")
        manager.disconnect(session_id)

@router.websocket("/ws/chat/{session_id}")
async def websocket_chat_endpoint(websocket: WebSocket, session_id: str):
    """
    Endpoint WebSocket para chat em tempo real (rota compatível com o frontend).
    
    Args:
        websocket: Conexão WebSocket
        session_id: ID da sessão
    """
    logger.info(f"Tentativa de conexão WebSocket em /ws/chat/{session_id}")
    try:
        await websocket_endpoint(websocket, session_id)
    except Exception as e:
        logger.error(f"Erro ao conectar WebSocket em /ws/chat/{session_id}: {str(e)}")
        raise

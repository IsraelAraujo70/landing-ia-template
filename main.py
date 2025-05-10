"""
Main entry point for the Ada Assistant application.
"""
import os
import json
import time
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any

# Importar os controllers e serviços
from app.models.schemas import QuestionRequest, QuestionResponse, DocumentInfo
from app.models.connection import ConnectionManager
from app.services.ai_service import generate_answer
from app.services.document_service import upload_and_process_document
from app.utils.vector_db import load_vector_db, query_vector_db
from app.config.settings import logger, UPLOADS_DIR

# Initialize FastAPI app
app = FastAPI(
    title="Assistente IA Ada Sistemas",
    description="API para o assistente de IA da Ada Sistemas",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static directories
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/client", StaticFiles(directory="client"), name="client")

# Criar o gerenciador de conexões WebSocket
manager = ConnectionManager()

# Endpoint para verificar status da API
@app.get("/status")
async def api_status():
    """Verificar o status da API."""
    try:
        return {
            "status": "online",
            "message": "API está funcionando corretamente"
        }
    except Exception as e:
        logger.error(f"Erro ao verificar status da API: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

# Endpoint para servir a página inicial do cliente
@app.get("/")
async def serve_client():
    """Redirecionar para a página inicial do cliente em /client/index.html"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/client/index.html")

# Endpoint para listar documentos carregados
@app.get("/documents")
async def list_documents():
    """Listar todos os documentos carregados."""
    try:
        # Verificar se o diretório de uploads existe
        if not os.path.exists(UPLOADS_DIR):
            os.makedirs(UPLOADS_DIR, exist_ok=True)
            return []
        
        documents = []
        
        # Listar arquivos no diretório de uploads
        for filename in os.listdir(UPLOADS_DIR):
            file_path = os.path.join(UPLOADS_DIR, filename)
            
            # Verificar se é um arquivo
            if os.path.isfile(file_path):
                # Obter informações do arquivo
                file_size = os.path.getsize(file_path)
                file_type = os.path.splitext(filename)[1].lower()
                
                # Obter data de modificação como timestamp de upload
                mod_time = os.path.getmtime(file_path)
                import datetime
                upload_time = datetime.datetime.fromtimestamp(mod_time).isoformat()
                
                # Criar objeto de documento
                document = DocumentInfo(
                    filename=filename,
                    upload_time=upload_time,
                    file_path=file_path,
                    size=file_size,
                    type=file_type
                )
                
                documents.append(document)
        
        # Ordenar documentos por data de upload (mais recentes primeiro)
        documents.sort(key=lambda x: x.upload_time, reverse=True)
        
        return documents
        
    except Exception as e:
        logger.error(f"Erro ao listar documentos: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao listar documentos: {str(e)}")

# Endpoint para fazer upload de um documento
@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Fazer upload de um documento e adicioná-lo ao banco de dados de vetores."""
    try:
        # Verificar se o arquivo foi enviado
        if not file:
            raise HTTPException(status_code=400, detail="Nenhum arquivo enviado")
        
        # Ler o conteúdo do arquivo
        file_content = await file.read()
        
        # Verificar se o arquivo está vazio
        if len(file_content) == 0:
            raise HTTPException(status_code=400, detail="Arquivo vazio")
        
        # Upload e processamento do documento
        file_path = await upload_and_process_document(file_content, file.filename)
        
        # Obter informações do arquivo
        file_size = os.path.getsize(file_path)
        file_type = os.path.splitext(file.filename)[1].lower()
        import datetime
        upload_time = datetime.datetime.now().isoformat()
        
        # Criar resposta
        document_info = DocumentInfo(
            filename=file.filename,
            upload_time=upload_time,
            file_path=file_path,
            size=file_size,
            type=file_type
        )
        
        logger.info(f"Documento carregado com sucesso: {file.filename}")
        return document_info
        
    except Exception as e:
        logger.error(f"Erro ao fazer upload do documento: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao processar o documento: {str(e)}")

# Endpoint HTTP para fazer uma pergunta
@app.post("/questions/ask")
async def ask_question(request: QuestionRequest):
    """Fazer uma pergunta e obter uma resposta com base no contexto do documento."""
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

# Endpoint WebSocket para chat - Rota original
@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """Endpoint WebSocket para chat em tempo real."""
    await manager.connect(websocket, session_id)
    
    try:
        while True:
            # Receber mensagem do cliente
            data = await websocket.receive_text()
            
            try:
                # Decodificar mensagem JSON
                message = json.loads(data)
                
                # Verificar se é uma pergunta (formato antigo ou novo)
                question = None
                top_k = 5
                file_paths = []
                
                if message.get("role") == "user" and message.get("content"):
                    # Formato novo: { role: "user", content: message }
                    question = message["content"]
                    top_k = message.get("top_k", 5)
                    file_paths = message.get("file_paths", [])
                elif message.get("question"):
                    # Formato antigo: { question: message, top_k: 5 }
                    question = message["question"]
                    top_k = message.get("top_k", 5)
                    file_paths = message.get("file_paths", [])
                
                if question:  # Processar apenas se tiver uma pergunta válida
                    # Adicionar mensagem ao histórico
                    await manager.send_personal_message(
                        {
                            "role": "user",
                            "content": question,
                            "timestamp": time.time()
                        },
                        session_id
                    )
                    
                    # Enviar mensagem de digitação
                    await manager.send_personal_message(
                        {
                            "role": "system",
                            "content": "typing",
                            "typing": True
                        },
                        session_id
                    )
                    
                    try:
                        # Consultar banco de dados de vetores para documentos relevantes
                        docs = await query_vector_db(question, top_k, file_paths)
                        
                        # Obter histórico de chat para a sessão
                        chat_history = manager.get_chat_history(session_id)
                        
                        # Gerar resposta
                        answer = await generate_answer(question, docs, chat_history)
                        
                        # Preparar informações de fontes
                        sources = [{"content": doc.page_content, "metadata": doc.metadata} for doc in docs]
                        
                        # Enviar resposta de volta ao cliente
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

# Endpoint WebSocket para chat - Rota compatível com o frontend
@app.websocket("/ws/chat/{session_id}")
async def websocket_chat_endpoint(websocket: WebSocket, session_id: str):
    """Endpoint WebSocket para chat em tempo real (rota compatível com o frontend)."""
    # Redirecionar para o endpoint principal
    await websocket_endpoint(websocket, session_id)

# Startup event
@app.on_event("startup")
async def startup_db_client():
    """Load the vector database on startup."""
    try:
        logger.info("Carregando banco de dados de vetores...")
        vector_db = load_vector_db()
        if vector_db:
            logger.info("Banco de dados de vetores carregado com sucesso")
        else:
            logger.info("Nenhum banco de dados de vetores existente encontrado. Será criado quando documentos forem carregados.")
    except Exception as e:
        logger.error(f"Erro ao carregar banco de dados de vetores: {str(e)}", exc_info=True)

# Run the application
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

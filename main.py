"""
Ponto de entrada principal para a aplicação Assistente AgiFinance.
"""
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.controllers.main_controller import router as main_router
from app.controllers.document_controller import router as document_router
from app.controllers.question_controller import router as question_router
from app.controllers.websocket_controller import router as websocket_router

from app.utils.vector_db import load_vector_db
from app.config.settings import logger

app = FastAPI(
    title="Assistente IA AgiFinance",
    description="API para o assistente de IA do AgiFinance - Seu gerenciador financeiro inteligente",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/client", StaticFiles(directory="client"), name="client")


app.include_router(main_router)
app.include_router(document_router)
app.include_router(question_router)
app.include_router(websocket_router)


@app.on_event("startup")
async def startup_db_client():
    """Carrega o banco de dados de vetores na inicialização."""
    try:
        logger.info("Carregando banco de dados de vetores...")
        vector_db = load_vector_db()
        if vector_db:
            logger.info("Banco de dados de vetores carregado com sucesso")
        else:
            logger.info("Nenhum banco de dados de vetores existente encontrado. Será criado quando documentos forem carregados.")
    except Exception as e:
        logger.error(f"Erro ao carregar banco de dados de vetores: {str(e)}", exc_info=True)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

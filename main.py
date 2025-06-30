"""
Ponto de entrada principal para a aplicação Assistente AgiFinance.
Configurado para deployment no Railway com Redis.
"""
import os
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.controllers.main_controller import router as main_router
from app.controllers.document_controller import router as document_router
from app.controllers.question_controller import router as question_router
from app.controllers.websocket_controller import router as websocket_router
from app.controllers.auth_controller import router as auth_router

from app.utils.vector_db import load_vector_db
from app.config.settings import logger
from app.middleware.auth_middleware import IframeAuthMiddleware

# Configuração CORS para Railway/Next.js
def get_cors_origins():
    """Retorna origens permitidas para CORS."""
    origins = []
    
    # Origem do site Next.js (Railway)
    site_url = os.getenv('NEXT_PUBLIC_SITE_URL')
    if site_url:
        origins.extend([site_url, site_url.rstrip('/')])
    
    # Origens de desenvolvimento
    if os.getenv('NODE_ENV') != 'production':
        origins.extend([
            "http://localhost:3000",
            "http://localhost:3001", 
            "http://127.0.0.1:3000",
            "http://127.0.0.1:3001"
        ])
    
    # Origens adicionais
    additional_origins = os.getenv('ALLOWED_ORIGINS', '')
    if additional_origins:
        for origin in additional_origins.split(','):
            origin = origin.strip()
            if origin and origin not in origins:
                origins.append(origin)
    
    # Fallback para desenvolvimento
    if not origins:
        origins = ["*"]
    
    logger.info(f"CORS origens configuradas: {origins}")
    return origins

app = FastAPI(
    title="Assistente IA AgiFinance",
    description="API para o assistente de IA do AgiFinance - Seu gerenciador financeiro inteligente com Redis",
    version="1.1.0"
)

# Configurar CORS
cors_origins = get_cors_origins()
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Adiciona middleware de autenticação para o iframe
app.add_middleware(IframeAuthMiddleware)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/client", StaticFiles(directory="client"), name="client")

app.include_router(main_router)
app.include_router(document_router)
app.include_router(question_router)
app.include_router(websocket_router)
app.include_router(auth_router)

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

@app.on_event("startup")
async def startup_redis_check():
    """Verifica conexão Redis na inicialização."""
    try:
        from app.config.redis_config import get_redis_session_manager
        redis_manager = get_redis_session_manager()
        if redis_manager.health_check():
            logger.info("✅ Conexão Redis estabelecida com sucesso")
        else:
            logger.warning("⚠️ Redis não disponível - sistema funcionará em modo degradado")
    except Exception as e:
        logger.error(f"❌ Erro ao verificar Redis: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint para Railway."""
    try:
        from app.config.redis_config import get_redis_session_manager
        redis_manager = get_redis_session_manager()
        redis_healthy = redis_manager.health_check()
        
        return {
            "status": "healthy",
            "redis": "connected" if redis_healthy else "disconnected",
            "version": "1.1.0",
            "environment": os.getenv('NODE_ENV', 'development')
        }
    except Exception as e:
        return {
            "status": "degraded",
            "redis": "error",
            "error": str(e),
            "version": "1.1.0"
        }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    reload = os.getenv("NODE_ENV") != "production"
    
    logger.info(f"🚀 Iniciando servidor em {host}:{port}")
    logger.info(f"🔧 Modo: {os.getenv('NODE_ENV', 'development')}")
    logger.info(f"🔄 Reload: {reload}")
    
    uvicorn.run("main:app", host=host, port=port, reload=reload)

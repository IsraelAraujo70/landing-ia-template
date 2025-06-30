"""
Configuração CORS para integração com frontend Next.js no Railway.
"""
import os
from fastapi.middleware.cors import CORSMiddleware
from app.config.settings import logger

def get_cors_origins():
    """
    Retorna lista de origens permitidas para CORS.
    """
    origins = []
    
    # Origem do site Next.js (Railway)
    site_url = os.getenv('NEXT_PUBLIC_SITE_URL')
    if site_url:
        origins.append(site_url)
        # Adicionar versão sem trailing slash
        origins.append(site_url.rstrip('/'))
    
    # Origens de desenvolvimento
    if os.getenv('NODE_ENV') != 'production':
        origins.extend([
            "http://localhost:3000",
            "http://localhost:3001", 
            "http://127.0.0.1:3000",
            "http://127.0.0.1:3001"
        ])
    
    # Origens adicionais via variável de ambiente
    additional_origins = os.getenv('ALLOWED_ORIGINS', '')
    if additional_origins:
        for origin in additional_origins.split(','):
            origin = origin.strip()
            if origin and origin not in origins:
                origins.append(origin)
    
    logger.info(f"CORS origens configuradas: {origins}")
    return origins

def setup_cors(app):
    """
    Configura CORS middleware na aplicação FastAPI.
    """
    origins = get_cors_origins()
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["*"]
    )
    
    logger.info("CORS middleware configurado para Railway/Next.js")
    return app
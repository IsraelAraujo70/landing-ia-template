"""
Middleware de autenticação para proteger o acesso ao iframe.
Agora usando Redis para verificação de sessions.
"""
from fastapi import Request, HTTPException
from fastapi.responses import HTMLResponse
from starlette.middleware.base import BaseHTTPMiddleware
from urllib.parse import urlparse, parse_qs
import sys
import os
from datetime import datetime

# Adiciona o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.config.settings import logger
from app.config.redis_config import get_redis_session_manager


class IframeAuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware para proteger o acesso ao iframe com session ID usando Redis.
    """
    
    def __init__(self, app):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next):
        """
        Intercepta as requisições para verificar autenticação do iframe.
        """
        # Verifica se é uma requisição para o iframe
        if request.url.path == "/client/iframe.html":
            try:
                # Obtém o gerenciador Redis
                redis_manager = get_redis_session_manager()
                
                # Verifica se Redis está disponível
                if not redis_manager.health_check():
                    logger.error("Redis indisponível durante verificação de middleware")
                    return HTMLResponse(
                        content=self._get_unauthorized_html("Serviço temporariamente indisponível"),
                        status_code=503
                    )
                
                # Obtém o session_id da query string
                session_id = request.query_params.get("session_id")
                
                if not session_id:
                    logger.warning("Tentativa de acesso ao iframe sem session ID")
                    return HTMLResponse(
                        content=self._get_unauthorized_html("Session ID obrigatório"),
                        status_code=401
                    )
                
                # Recupera dados da session do Redis
                session_data = redis_manager.get_session(session_id)
                
                # Verifica se session existe
                if not session_data:
                    logger.warning(f"Tentativa de acesso com session ID inválido: {session_id}")
                    return HTMLResponse(
                        content=self._get_unauthorized_html("Session ID inválido ou expirado"),
                        status_code=401
                    )
                
                # Verifica se session já foi usada
                if session_data.get('used', False):
                    logger.warning(f"Tentativa de reutilizar session ID: {session_id}")
                    return HTMLResponse(
                        content=self._get_unauthorized_html("Session ID já foi utilizado"),
                        status_code=401
                    )
                
                # Verifica se session está expirada (dupla verificação)
                expires_at = datetime.fromisoformat(session_data['expires_at'])
                if datetime.now() > expires_at:
                    redis_manager.delete_session(session_id)
                    logger.warning(f"Session ID expirado: {session_id}")
                    return HTMLResponse(
                        content=self._get_unauthorized_html("Session ID expirado"),
                        status_code=401
                    )
                
                # Marca session como usada no Redis
                success = redis_manager.mark_session_used(session_id)
                
                if not success:
                    logger.error(f"Falha ao marcar session como usada: {session_id}")
                    return HTMLResponse(
                        content=self._get_unauthorized_html("Erro interno de autenticação"),
                        status_code=500
                    )
                
                logger.info(f"Acesso autorizado ao iframe com session ID: {session_id}")
                
            except Exception as e:
                logger.error(f"Erro no middleware de autenticação: {str(e)}")
                return HTMLResponse(
                    content=self._get_unauthorized_html("Erro interno de autenticação"),
                    status_code=500
                )
        
        # Continua com a requisição normal
        response = await call_next(request)
        return response
    
    def _get_unauthorized_html(self, message: str) -> str:
        """
        Retorna uma página HTML de erro para acesso não autorizado.
        """
        return f"""
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Acesso Negado - AgiFinance</title>
            <link href="https://fonts.googleapis.com/css2?family=Mulish:wght@300;400;500;600;700&display=swap" rel="stylesheet">
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
            <style>
                body {{
                    font-family: 'Mulish', sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    margin: 0;
                }}
                .error-container {{
                    background: white;
                    border-radius: 20px;
                    padding: 3rem;
                    text-align: center;
                    box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                    max-width: 500px;
                    margin: 2rem;
                }}
                .error-icon {{
                    font-size: 4rem;
                    color: #dc3545;
                    margin-bottom: 1rem;
                }}
                .error-title {{
                    color: #333;
                    font-size: 1.8rem;
                    font-weight: 600;
                    margin-bottom: 1rem;
                }}
                .error-message {{
                    color: #666;
                    font-size: 1.1rem;
                    margin-bottom: 2rem;
                    line-height: 1.6;
                }}
                .btn-home {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    border: none;
                    color: white;
                    padding: 12px 30px;
                    border-radius: 25px;
                    font-weight: 500;
                    text-decoration: none;
                    display: inline-block;
                    transition: transform 0.2s;
                }}
                .btn-home:hover {{
                    transform: translateY(-2px);
                    color: white;
                    text-decoration: none;
                }}
                .storage-info {{
                    color: #888;
                    font-size: 0.9rem;
                    margin-top: 1rem;
                    padding: 10px;
                    background: #f8f9fa;
                    border-radius: 8px;
                }}
            </style>
        </head>
        <body>
            <div class="error-container">
                <div class="error-icon">🔒</div>
                <h1 class="error-title">Acesso Negado</h1>
                <p class="error-message">{message}</p>
                <p class="error-message">Para acessar o iframe, você precisa de um session ID válido.</p>
                <div class="storage-info">
                    ⚡ Autenticação baseada em Redis para melhor performance e escalabilidade
                </div>
                <a href="/" class="btn-home">Voltar ao Início</a>
            </div>
        </body>
        </html>
        """
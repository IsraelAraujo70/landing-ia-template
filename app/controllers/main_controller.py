"""
Controlador principal para manipulação de endpoints básicos.
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from app.config.settings import logger

# Cria o router
router = APIRouter(tags=["main"])

@router.get("/")
async def serve_client():
    """
    Serve a página principal do cliente.
    
    Retorna:
        Resposta de arquivo HTML
    """
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/client/index.html")

@router.get("/auth-demo")
async def auth_demo():
    """
    Serve a página de demonstração do sistema de autenticação.
    
    Retorna:
        Página HTML de demonstração
    """
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/client/auth-demo.html")

@router.get("/status")
async def api_status():
    """
    Verifica o status da API.
    
    Retorna:
        Informações de status
    """
    try:
        return {
            "status": "online",
            "message": "API está funcionando corretamente"
        }
    except Exception as e:
        logger.error(f"Erro ao verificar status da API: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

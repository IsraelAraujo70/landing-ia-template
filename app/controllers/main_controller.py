"""
Main controller for handling basic endpoints.
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from app.config.settings import logger

# Create router
router = APIRouter(tags=["main"])

@router.get("/")
async def serve_client():
    """
    Serve the client's main page.
    
    Returns:
        HTML file response
    """
    return FileResponse("client/index.html")

@router.get("/status")
async def api_status():
    """
    Check API status.
    
    Returns:
        Status information
    """
    try:
        return {
            "status": "online",
            "message": "API está funcionando corretamente"
        }
    except Exception as e:
        logger.error(f"Erro ao verificar status da API: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno do servidor")

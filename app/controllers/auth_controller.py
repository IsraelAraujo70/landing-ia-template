"""
Controlador de autenticação para gerenciar session IDs do iframe.
Agora usando Redis para armazenamento persistente e escalável.
"""
import uuid
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from app.config.settings import logger
from app.config.redis_config import get_redis_session_manager

# Cria o router
router = APIRouter(tags=["auth"])

# Configurações
SESSION_EXPIRY_MINUTES = 30  # Session expira em 30 minutos se não usado
MAX_SESSIONS = 1000  # Máximo de sessions simultâneas


def generate_session_id() -> str:
    """Gera um session ID único."""
    return str(uuid.uuid4())


@router.post("/auth/create-session")
async def create_session():
    """
    Cria um novo session ID válido para acesso ao iframe.
    Usa Redis para armazenamento persistente.
    
    Retorna:
        Session ID único que pode ser usado uma vez
    """
    try:
        # Obtém o gerenciador Redis
        redis_manager = get_redis_session_manager()
        
        # Verifica se Redis está disponível
        if not redis_manager.health_check():
            raise HTTPException(
                status_code=503,
                detail="Serviço de autenticação temporariamente indisponível"
            )
        
        # Verifica se não excedeu o limite de sessions
        total_sessions = redis_manager.get_total_sessions_count()
        if total_sessions >= MAX_SESSIONS:
            raise HTTPException(
                status_code=429, 
                detail="Limite de sessions simultâneas atingido. Tente novamente em alguns minutos."
            )
        
        # Gera novo session ID
        session_id = generate_session_id()
        
        # Cria a session no Redis
        success = redis_manager.create_session(session_id, SESSION_EXPIRY_MINUTES)
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Erro ao criar session. Tente novamente."
            )
        
        logger.info(f"Novo session ID criado no Redis: {session_id}")
        
        return {
            "session_id": session_id,
            "expires_in_minutes": SESSION_EXPIRY_MINUTES,
            "iframe_url": f"/client/iframe.html?session_id={session_id}",
            "storage": "redis"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao criar session: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno ao criar session")


@router.get("/auth/validate-session")
async def validate_session(session_id: str = Query(..., description="Session ID para validação")):
    """
    Valida um session ID e marca como usado.
    Utiliza Redis para verificação e atualização.
    
    Args:
        session_id: ID da session a ser validada
        
    Retorna:
        Status da validação
    """
    try:
        # Obtém o gerenciador Redis
        redis_manager = get_redis_session_manager()
        
        # Verifica se Redis está disponível
        if not redis_manager.health_check():
            raise HTTPException(
                status_code=503,
                detail="Serviço de autenticação temporariamente indisponível"
            )
        
        # Recupera dados da session
        session_data = redis_manager.get_session(session_id)
        
        # Verifica se session existe
        if not session_data:
            raise HTTPException(status_code=401, detail="Session ID inválido ou expirado")
        
        # Verifica se session já foi usada
        if session_data.get('used', False):
            raise HTTPException(status_code=401, detail="Session ID já foi utilizado")
        
        # Verifica se session está expirada (dupla verificação, Redis já expira automaticamente)
        expires_at = datetime.fromisoformat(session_data['expires_at'])
        if datetime.now() > expires_at:
            redis_manager.delete_session(session_id)
            raise HTTPException(status_code=401, detail="Session ID expirado")
        
        # Marca session como usada
        success = redis_manager.mark_session_used(session_id)
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Erro ao validar session. Tente novamente."
            )
        
        logger.info(f"Session ID validado e marcado como usado no Redis: {session_id}")
        
        return {
            "valid": True,
            "message": "Session válida",
            "session_id": session_id,
            "storage": "redis"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao validar session: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno ao validar session")


@router.get("/auth/session-status")
async def get_session_status():
    """
    Retorna informações sobre as sessions ativas no Redis.
    
    Retorna:
        Estatísticas das sessions
    """
    try:
        # Obtém o gerenciador Redis
        redis_manager = get_redis_session_manager()
        
        # Verifica se Redis está disponível
        if not redis_manager.health_check():
            raise HTTPException(
                status_code=503,
                detail="Serviço de autenticação temporariamente indisponível"
            )
        
        # Obtém estatísticas do Redis
        stats = redis_manager.get_stats()
        
        return {
            "total_sessions": stats['total_sessions'],
            "active_sessions": stats['active_sessions'],
            "used_sessions": stats['used_sessions'],
            "total_created": stats['total_created'],
            "total_used": stats['total_used'],
            "max_sessions": MAX_SESSIONS,
            "storage": "redis",
            "redis_healthy": True
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao obter status das sessions: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno ao obter status")


@router.delete("/auth/cleanup-sessions")
async def cleanup_sessions():
    """
    Força a limpeza de sessions expiradas no Redis.
    Nota: Redis faz isso automaticamente com TTL, mas este endpoint permite limpeza manual.
    
    Retorna:
        Número de sessions removidas
    """
    try:
        # Obtém o gerenciador Redis
        redis_manager = get_redis_session_manager()
        
        # Verifica se Redis está disponível
        if not redis_manager.health_check():
            raise HTTPException(
                status_code=503,
                detail="Serviço de autenticação temporariamente indisponível"
            )
        
        # Obtém contagem antes da limpeza
        initial_count = redis_manager.get_total_sessions_count()
        
        # Executa limpeza manual
        removed_count = redis_manager.cleanup_expired_sessions()
        
        # Obtém contagem após limpeza
        remaining_count = redis_manager.get_total_sessions_count()
        
        return {
            "message": "Limpeza de sessions concluída",
            "sessions_removed": removed_count,
            "sessions_remaining": remaining_count,
            "storage": "redis"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao limpar sessions: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno ao limpar sessions")


@router.get("/auth/redis-health")
async def redis_health_check():
    """
    Verifica a saúde da conexão com Redis.
    
    Retorna:
        Status da conexão Redis
    """
    try:
        # Obtém o gerenciador Redis
        redis_manager = get_redis_session_manager()
        
        # Verifica saúde
        is_healthy = redis_manager.health_check()
        
        if is_healthy:
            return {
                "status": "healthy",
                "message": "Conexão com Redis funcionando corretamente",
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "status": "unhealthy",
                "message": "Falha na conexão com Redis",
                "timestamp": datetime.now().isoformat()
            }
    
    except Exception as e:
        logger.error(f"Erro no health check do Redis: {str(e)}")
        return {
            "status": "error",
            "message": f"Erro ao verificar Redis: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }
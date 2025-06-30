"""
Controlador de autenticação para gerenciar session IDs do iframe.
"""
import uuid
import time
from datetime import datetime, timedelta
from typing import Dict, Optional
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from app.config.settings import logger

# Cria o router
router = APIRouter(tags=["auth"])

# Armazenamento em memória dos session IDs (em produção, usar Redis ou banco de dados)
session_store: Dict[str, dict] = {}

# Configurações
SESSION_EXPIRY_MINUTES = 30  # Session expira em 30 minutos se não usado
MAX_SESSIONS = 1000  # Máximo de sessions simultâneas


def cleanup_expired_sessions():
    """Remove sessions expiradas do armazenamento."""
    current_time = datetime.now()
    expired_sessions = []
    
    for session_id, session_data in session_store.items():
        if current_time > session_data['expires_at']:
            expired_sessions.append(session_id)
    
    for session_id in expired_sessions:
        del session_store[session_id]
    
    logger.info(f"Removidas {len(expired_sessions)} sessions expiradas")


def generate_session_id() -> str:
    """Gera um session ID único."""
    return str(uuid.uuid4())


@router.post("/auth/create-session")
async def create_session():
    """
    Cria um novo session ID válido para acesso ao iframe.
    
    Retorna:
        Session ID único que pode ser usado uma vez
    """
    try:
        # Limpa sessions expiradas
        cleanup_expired_sessions()
        
        # Verifica se não excedeu o limite de sessions
        if len(session_store) >= MAX_SESSIONS:
            raise HTTPException(
                status_code=429, 
                detail="Limite de sessions simultâneas atingido. Tente novamente em alguns minutos."
            )
        
        # Gera novo session ID
        session_id = generate_session_id()
        
        # Armazena o session com dados de controle
        session_store[session_id] = {
            'created_at': datetime.now(),
            'expires_at': datetime.now() + timedelta(minutes=SESSION_EXPIRY_MINUTES),
            'used': False,
            'iframe_opened': False
        }
        
        logger.info(f"Novo session ID criado: {session_id}")
        
        return {
            "session_id": session_id,
            "expires_in_minutes": SESSION_EXPIRY_MINUTES,
            "iframe_url": f"/client/iframe.html?session_id={session_id}"
        }
    
    except Exception as e:
        logger.error(f"Erro ao criar session: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno ao criar session")


@router.get("/auth/validate-session")
async def validate_session(session_id: str = Query(..., description="Session ID para validação")):
    """
    Valida um session ID e marca como usado.
    
    Args:
        session_id: ID da session a ser validada
        
    Retorna:
        Status da validação
    """
    try:
        # Limpa sessions expiradas
        cleanup_expired_sessions()
        
        # Verifica se session existe
        if session_id not in session_store:
            raise HTTPException(status_code=401, detail="Session ID inválido ou expirado")
        
        session_data = session_store[session_id]
        
        # Verifica se session já foi usada
        if session_data['used']:
            raise HTTPException(status_code=401, detail="Session ID já foi utilizado")
        
        # Verifica se session está expirada
        if datetime.now() > session_data['expires_at']:
            del session_store[session_id]
            raise HTTPException(status_code=401, detail="Session ID expirado")
        
        # Marca session como usada e iframe como aberto
        session_data['used'] = True
        session_data['iframe_opened'] = True
        session_data['used_at'] = datetime.now()
        
        logger.info(f"Session ID validado e marcado como usado: {session_id}")
        
        return {
            "valid": True,
            "message": "Session válida",
            "session_id": session_id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao validar session: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno ao validar session")


@router.get("/auth/session-status")
async def get_session_status():
    """
    Retorna informações sobre as sessions ativas.
    
    Retorna:
        Estatísticas das sessions
    """
    try:
        # Limpa sessions expiradas
        cleanup_expired_sessions()
        
        total_sessions = len(session_store)
        used_sessions = sum(1 for s in session_store.values() if s['used'])
        active_sessions = total_sessions - used_sessions
        
        return {
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "used_sessions": used_sessions,
            "max_sessions": MAX_SESSIONS
        }
    
    except Exception as e:
        logger.error(f"Erro ao obter status das sessions: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno ao obter status")


@router.delete("/auth/cleanup-sessions")
async def cleanup_sessions():
    """
    Força a limpeza de todas as sessions expiradas.
    
    Retorna:
        Número de sessions removidas
    """
    try:
        initial_count = len(session_store)
        cleanup_expired_sessions()
        removed_count = initial_count - len(session_store)
        
        return {
            "message": "Limpeza de sessions concluída",
            "sessions_removed": removed_count,
            "sessions_remaining": len(session_store)
        }
    
    except Exception as e:
        logger.error(f"Erro ao limpar sessions: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno ao limpar sessions")
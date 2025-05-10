"""
WebSocket connection manager.
"""
import json
import time
from typing import Dict, List, Any
from fastapi import WebSocket
from app.config.settings import logger

class ConnectionManager:
    """Manages WebSocket connections and chat history."""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}  # Usando dict para identificar conexões por ID
        self.chat_history: Dict[str, List[Dict[str, Any]]] = {}  # Histórico de chat por ID de sessão

    async def connect(self, websocket: WebSocket, session_id: str):
        """Connect a new WebSocket client."""
        await websocket.accept()
        self.active_connections[session_id] = websocket
        if session_id not in self.chat_history:
            self.chat_history[session_id] = []
        logger.info(f"Nova conexão WebSocket estabelecida: {session_id}")

    def disconnect(self, session_id: str):
        """Disconnect a WebSocket client."""
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            logger.info(f"Conexão WebSocket encerrada: {session_id}")

    async def send_personal_message(self, message: Dict[str, Any], session_id: str):
        """Send a message to a specific client and store in chat history."""
        if session_id in self.active_connections:
            websocket = self.active_connections[session_id]
            await websocket.send_text(json.dumps(message))
            # Adicionar mensagem ao histórico
            if message.get("role") and message.get("content"):
                self.chat_history[session_id].append({
                    "role": message["role"],
                    "content": message["content"],
                    "timestamp": time.time()
                })

    def get_chat_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get chat history for a specific session."""
        return self.chat_history.get(session_id, [])

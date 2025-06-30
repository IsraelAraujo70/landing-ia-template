"""
Configuração do Redis para armazenamento de sessions.
Configurado para Railway com fallback gracioso.
"""
import redis
import json
import os
from datetime import datetime, timedelta
from typing import Optional, Dict
from app.config.settings import logger

class RedisSessionManager:
    """Gerenciador de sessions usando Redis com fallback para Railway."""
    
    def __init__(self):
        """Inicializa a conexão com Redis."""
        # Configurações do Redis - Railway pode fornecer diferentes variáveis
        self.redis_host = os.getenv('REDIS_HOST') or os.getenv('REDISHOST', 'localhost')
        self.redis_port = int(os.getenv('REDIS_PORT') or os.getenv('REDISPORT', 6379))
        self.redis_db = int(os.getenv('REDIS_DB', 0))
        self.redis_password = os.getenv('REDIS_PASSWORD') or os.getenv('REDISPASSWORD', None)
        
        # Railway pode fornecer URL completa do Redis
        redis_url = os.getenv('REDIS_URL')
        
        # Prefixo para chaves das sessions
        self.session_prefix = "auth_session:"
        self.stats_key = "auth_stats"
        
        # Flag para indicar se Redis está disponível
        self.redis_available = False
        self.redis_client = None
        
        try:
            if redis_url:
                # Usar URL completa do Redis (Railway padrão)
                self.redis_client = redis.from_url(
                    redis_url,
                    decode_responses=True,
                    socket_connect_timeout=10,
                    socket_timeout=10,
                    retry_on_timeout=True,
                    retry_on_error=[redis.ConnectionError, redis.TimeoutError],
                    max_connections=20
                )
                logger.info(f"Conectando ao Redis via URL: {redis_url[:20]}...")
            else:
                # Conectar usando parâmetros individuais
                self.redis_client = redis.Redis(
                    host=self.redis_host,
                    port=self.redis_port,
                    db=self.redis_db,
                    password=self.redis_password,
                    decode_responses=True,
                    socket_connect_timeout=10,
                    socket_timeout=10,
                    retry_on_timeout=True,
                    retry_on_error=[redis.ConnectionError, redis.TimeoutError],
                    max_connections=20
                )
                logger.info(f"Conectando ao Redis em {self.redis_host}:{self.redis_port}")
            
            # Testa a conexão
            self.redis_client.ping()
            self.redis_available = True
            logger.info("✅ Redis conectado com sucesso")
            
        except redis.ConnectionError as e:
            logger.warning(f"⚠️ Redis não disponível: {e}")
            logger.info("Sistema funcionará sem cache de sessions (modo degradado)")
            self.redis_available = False
            self.redis_client = None
        except Exception as e:
            logger.error(f"❌ Erro inesperado ao configurar Redis: {e}")
            self.redis_available = False
            self.redis_client = None
    
    def _ensure_redis_connection(self) -> bool:
        """Verifica e reconecta ao Redis se necessário."""
        if not self.redis_client:
            return False
        
        try:
            self.redis_client.ping()
            self.redis_available = True
            return True
        except (redis.ConnectionError, redis.TimeoutError):
            logger.warning("⚠️ Conexão Redis perdida, tentando reconectar...")
            self.redis_available = False
            
            # Tentar reconectar
            try:
                redis_url = os.getenv('REDIS_URL')
                if redis_url:
                    self.redis_client = redis.from_url(redis_url, decode_responses=True)
                else:
                    self.redis_client = redis.Redis(
                        host=self.redis_host,
                        port=self.redis_port,
                        db=self.redis_db,
                        password=self.redis_password,
                        decode_responses=True
                    )
                
                self.redis_client.ping()
                self.redis_available = True
                logger.info("✅ Redis reconectado")
                return True
            except Exception as e:
                logger.error(f"❌ Falha na reconexão Redis: {e}")
                self.redis_available = False
                return False
        except Exception as e:
            logger.error(f"❌ Erro na verificação Redis: {e}")
            self.redis_available = False
            return False
    
    def _get_session_key(self, session_id: str) -> str:
        """Gera a chave Redis para uma session."""
        return f"{self.session_prefix}{session_id}"
    
    def create_session(self, session_id: str, expiry_minutes: int = 30) -> bool:
        """
        Cria uma nova session no Redis.
        
        Args:
            session_id: ID único da session
            expiry_minutes: Tempo de expiração em minutos
            
        Returns:
            True se criada com sucesso, False caso contrário
        """
        if not self._ensure_redis_connection():
            logger.warning("Redis indisponível - session não persistida")
            return False
        
        try:
            session_data = {
                'session_id': session_id,
                'created_at': datetime.now().isoformat(),
                'expires_at': (datetime.now() + timedelta(minutes=expiry_minutes)).isoformat(),
                'used': False,
                'iframe_opened': False
            }
            
            session_key = self._get_session_key(session_id)
            
            # Armazena a session com TTL automático
            self.redis_client.setex(
                session_key,
                timedelta(minutes=expiry_minutes),
                json.dumps(session_data)
            )
            
            # Incrementa contador de sessions criadas
            self.redis_client.hincrby(self.stats_key, "total_created", 1)
            
            logger.info(f"Session criada no Redis: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao criar session no Redis: {e}")
            return False
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """
        Recupera dados de uma session do Redis.
        
        Args:
            session_id: ID da session
            
        Returns:
            Dados da session ou None se não encontrada
        """
        if not self._ensure_redis_connection():
            return None
        
        try:
            session_key = self._get_session_key(session_id)
            session_data = self.redis_client.get(session_key)
            
            if session_data:
                return json.loads(session_data)
            return None
            
        except Exception as e:
            logger.error(f"Erro ao recuperar session do Redis: {e}")
            return None
    
    def mark_session_used(self, session_id: str) -> bool:
        """
        Marca uma session como usada.
        
        Args:
            session_id: ID da session
            
        Returns:
            True se marcada com sucesso, False caso contrário
        """
        if not self._ensure_redis_connection():
            return False
        
        try:
            session_data = self.get_session(session_id)
            if not session_data:
                return False
            
            # Atualiza os dados da session
            session_data['used'] = True
            session_data['iframe_opened'] = True
            session_data['used_at'] = datetime.now().isoformat()
            
            session_key = self._get_session_key(session_id)
            
            # Recupera TTL restante
            ttl = self.redis_client.ttl(session_key)
            if ttl > 0:
                # Atualiza com o mesmo TTL
                self.redis_client.setex(session_key, ttl, json.dumps(session_data))
                
                # Incrementa contador de sessions usadas
                self.redis_client.hincrby(self.stats_key, "total_used", 1)
                
                logger.info(f"Session marcada como usada: {session_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Erro ao marcar session como usada: {e}")
            return False
    
    def delete_session(self, session_id: str) -> bool:
        """
        Remove uma session do Redis.
        
        Args:
            session_id: ID da session
            
        Returns:
            True se removida com sucesso, False caso contrário
        """
        if not self._ensure_redis_connection():
            return False
        
        try:
            session_key = self._get_session_key(session_id)
            result = self.redis_client.delete(session_key)
            
            if result:
                logger.info(f"Session removida do Redis: {session_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Erro ao remover session do Redis: {e}")
            return False
    
    def get_active_sessions_count(self) -> int:
        """
        Conta o número de sessions ativas no Redis.
        
        Returns:
            Número de sessions ativas
        """
        if not self._ensure_redis_connection():
            return 0
        
        try:
            pattern = f"{self.session_prefix}*"
            active_sessions = 0
            
            # Usa SCAN para evitar bloquear o Redis com KEYS
            for key in self.redis_client.scan_iter(match=pattern, count=100):
                session_data = self.redis_client.get(key)
                if session_data:
                    data = json.loads(session_data)
                    if not data.get('used', False):
                        active_sessions += 1
            
            return active_sessions
            
        except Exception as e:
            logger.error(f"Erro ao contar sessions ativas: {e}")
            return 0
    
    def get_total_sessions_count(self) -> int:
        """
        Conta o número total de sessions no Redis.
        
        Returns:
            Número total de sessions
        """
        if not self._ensure_redis_connection():
            return 0
        
        try:
            pattern = f"{self.session_prefix}*"
            # Conta todas as keys que correspondem ao padrão
            count = 0
            for _ in self.redis_client.scan_iter(match=pattern, count=100):
                count += 1
            return count
            
        except Exception as e:
            logger.error(f"Erro ao contar total de sessions: {e}")
            return 0
    
    def get_used_sessions_count(self) -> int:
        """
        Conta o número de sessions usadas no Redis.
        
        Returns:
            Número de sessions usadas
        """
        if not self._ensure_redis_connection():
            return 0
        
        try:
            pattern = f"{self.session_prefix}*"
            used_sessions = 0
            
            for key in self.redis_client.scan_iter(match=pattern, count=100):
                session_data = self.redis_client.get(key)
                if session_data:
                    data = json.loads(session_data)
                    if data.get('used', False):
                        used_sessions += 1
            
            return used_sessions
            
        except Exception as e:
            logger.error(f"Erro ao contar sessions usadas: {e}")
            return 0
    
    def cleanup_expired_sessions(self) -> int:
        """
        Remove sessions expiradas (Redis faz isso automaticamente com TTL, mas este método pode ser usado para auditoria).
        
        Returns:
            Número de sessions removidas
        """
        if not self._ensure_redis_connection():
            return 0
        
        try:
            pattern = f"{self.session_prefix}*"
            expired_count = 0
            current_time = datetime.now()
            
            for key in self.redis_client.scan_iter(match=pattern, count=100):
                session_data = self.redis_client.get(key)
                if session_data:
                    data = json.loads(session_data)
                    expires_at = datetime.fromisoformat(data['expires_at'])
                    
                    if current_time > expires_at:
                        self.redis_client.delete(key)
                        expired_count += 1
            
            logger.info(f"Limpeza manual: {expired_count} sessions expiradas removidas")
            return expired_count
            
        except Exception as e:
            logger.error(f"Erro na limpeza de sessions: {e}")
            return 0
    
    def get_stats(self) -> Dict:
        """
        Retorna estatísticas das sessions.
        
        Returns:
            Dicionário com estatísticas
        """
        if not self._ensure_redis_connection():
            return {
                'total_created': 0,
                'total_used': 0,
                'active_sessions': 0,
                'total_sessions': 0,
                'used_sessions': 0,
                'redis_available': False
            }
        
        try:
            stats = self.redis_client.hgetall(self.stats_key)
            
            return {
                'total_created': int(stats.get('total_created', 0)),
                'total_used': int(stats.get('total_used', 0)),
                'active_sessions': self.get_active_sessions_count(),
                'total_sessions': self.get_total_sessions_count(),
                'used_sessions': self.get_used_sessions_count(),
                'redis_available': True
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas: {e}")
            return {
                'total_created': 0,
                'total_used': 0,
                'active_sessions': 0,
                'total_sessions': 0,
                'used_sessions': 0,
                'redis_available': False
            }
    
    def health_check(self) -> bool:
        """
        Verifica se a conexão com Redis está saudável.
        
        Returns:
            True se saudável, False caso contrário
        """
        return self._ensure_redis_connection()

# Instância global do gerenciador de sessions
redis_session_manager = None

def get_redis_session_manager() -> RedisSessionManager:
    """
    Retorna a instância do gerenciador de sessions Redis.
    Cria uma nova instância se não existir.
    """
    global redis_session_manager
    if redis_session_manager is None:
        redis_session_manager = RedisSessionManager()
    return redis_session_manager
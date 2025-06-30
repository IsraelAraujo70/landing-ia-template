# Implementação Redis para Sistema de Autenticação de Iframe

## 📋 Visão Geral

O sistema de autenticação foi migrado do armazenamento em memória para **Redis**, proporcionando:

- ✅ **Persistência**: Sessions sobrevivem a reinicializações da aplicação
- ✅ **Escalabilidade**: Suporte a múltiplas instâncias da aplicação
- ✅ **Performance**: Cache em memória distribuído de alta performance
- ✅ **TTL Automático**: Expiração automática de sessions sem intervenção manual
- ✅ **Monitoramento**: Estatísticas avançadas e health checks

## 🏗️ Arquitetura

### Componentes Implementados

1. **RedisSessionManager** (`app/config/redis_config.py`)
   - Gerencia conexões Redis
   - Operações CRUD para sessions
   - Health checks e estatísticas
   - TTL automático

2. **Auth Controller Atualizado** (`app/controllers/auth_controller.py`)
   - Migrado para usar Redis
   - Novo endpoint de health check
   - Tratamento de erros melhorado

3. **Middleware Atualizado** (`app/middleware/auth_middleware.py`)
   - Verificação de sessions via Redis
   - Fallback para serviço indisponível
   - Performance otimizada

## 🔧 Configuração

### Variáveis de Ambiente

Adicione no arquivo `.env`:

```bash
# Configurações do Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# Configurações da aplicação
DEBUG=True
LOG_LEVEL=INFO
```

### Instalação do Redis

#### Método 1: Script Automático
```bash
./scripts/setup_redis.sh
```

#### Método 2: Manual

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install redis-server
sudo systemctl start redis
```

**CentOS/RHEL:**
```bash
sudo yum install redis
sudo systemctl start redis
```

**macOS:**
```bash
brew install redis
brew services start redis
```

**Docker:**
```bash
docker run -d -p 6379:6379 --name redis redis:7-alpine
```

## 📡 Endpoints da API

### Endpoints Existentes (Atualizados)

#### POST `/auth/create-session`
Cria nova session no Redis com TTL automático.

**Response:**
```json
{
  "session_id": "uuid-v4",
  "expires_in_minutes": 30,
  "iframe_url": "/client/iframe.html?session_id=uuid-v4",
  "storage": "redis"
}
```

#### GET `/auth/validate-session?session_id=uuid`
Valida e marca session como usada no Redis.

#### GET `/auth/session-status`
Estatísticas avançadas das sessions:

```json
{
  "total_sessions": 5,
  "active_sessions": 3,
  "used_sessions": 2,
  "total_created": 150,
  "total_used": 147,
  "max_sessions": 1000,
  "storage": "redis",
  "redis_healthy": true
}
```

### Novo Endpoint

#### GET `/auth/redis-health`
Verifica saúde da conexão Redis:

```json
{
  "status": "healthy",
  "message": "Conexão com Redis funcionando corretamente",
  "timestamp": "2024-01-XX..."
}
```

## 🔄 Migração de Dados

### Do Sistema Anterior
- ✅ **Automática**: Não há dados para migrar
- ✅ **Zero Downtime**: Sistema continua funcionando
- ✅ **Compatível**: APIs mantêm mesma interface

### Sessions Existentes
Sessions em memória serão perdidas na migração (comportamento esperado, pois eram temporárias).

## 🔍 Monitoramento

### Health Checks
```bash
# Via API
curl http://localhost:8000/auth/redis-health

# Via Redis CLI
redis-cli ping
```

### Estatísticas
```bash
# Sessions ativas
curl http://localhost:8000/auth/session-status

# Info do Redis
redis-cli info stats
```

### Logs
```bash
# Logs da aplicação
tail -f logs/app.log | grep -i redis

# Logs do Redis
tail -f /var/log/redis/redis-server.log
```

## 📊 Estrutura de Dados Redis

### Chaves das Sessions
```
Padrão: auth_session:{session_id}
Exemplo: auth_session:550e8400-e29b-41d4-a716-446655440000
```

### Dados da Session
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2024-01-XX...",
  "expires_at": "2024-01-XX...",
  "used": false,
  "iframe_opened": false,
  "used_at": "2024-01-XX..."  // Adicionado quando usada
}
```

### Estatísticas Globais
```
Chave: auth_stats
Campos:
- total_created: Contador de sessions criadas
- total_used: Contador de sessions utilizadas
```

## ⚡ Performance

### Otimizações Implementadas

1. **TTL Automático**: Redis remove sessions expiradas automaticamente
2. **SCAN em vez de KEYS**: Evita bloquear Redis em operações de listagem
3. **Pipeline Operations**: Operações batch quando possível
4. **Connection Pooling**: Reutilização eficiente de conexões
5. **Timeout Configurável**: Evita travamentos em conexões lentas

### Métricas Esperadas
- **Latência**: < 1ms para operações básicas
- **Throughput**: > 10.000 ops/sec
- **Memória**: ~100 bytes por session
- **TTL**: Expiração automática em 30 minutos

## 🛡️ Segurança

### Implementadas
- ✅ Conexão local por padrão (bind 127.0.0.1)
- ✅ Timeout de conexão configurável
- ✅ Validação de dados de entrada
- ✅ Logs de segurança

### Recomendações para Produção
- 🔒 **AUTH**: Configure senha Redis (`REDIS_PASSWORD`)
- 🔒 **TLS**: Use conexões criptografadas
- 🔒 **Firewall**: Restrinja acesso à porta 6379
- 🔒 **Network**: Use VPN ou rede privada
- 🔒 **Backup**: Configure backup automático
- 🔒 **Monitoring**: Monitore métricas de segurança

## 🚀 Deploy em Produção

### Configuração Recomendada

```bash
# Redis em produção
REDIS_HOST=redis.internal.domain.com
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=sua_senha_segura_aqui
```

### Docker Compose Example
```yaml
version: '3.8'
services:
  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    environment:
      - REDIS_PASSWORD=${REDIS_PASSWORD}

  app:
    build: .
    depends_on:
      - redis
    environment:
      - REDIS_HOST=redis
      - REDIS_PASSWORD=${REDIS_PASSWORD}

volumes:
  redis_data:
```

### Escalabilidade
- **Redis Cluster**: Para grandes volumes
- **Redis Sentinel**: Para alta disponibilidade
- **Read Replicas**: Para distribuir carga de leitura

## 🔧 Troubleshooting

### Problemas Comuns

#### 1. "Redis Connection Failed"
```bash
# Verifica se Redis está rodando
ps aux | grep redis
sudo systemctl status redis

# Testa conexão
redis-cli ping
```

#### 2. "Service Temporarily Unavailable" (503)
- Verifica configurações de rede
- Confirma variáveis de ambiente
- Checa logs Redis

#### 3. "Session ID Invalid" após migração
- Normal: Sessions em memória foram perdidas
- Criar novas sessions via API

### Logs Úteis
```bash
# Logs detalhados da aplicação
grep -i "redis" logs/app.log

# Conexões Redis
redis-cli monitor

# Estatísticas Redis
redis-cli --stat
```

## 📈 Próximos Passos

### Melhorias Futuras
1. **Redis Cluster**: Para escalabilidade extrema
2. **Cache de Múltiplas Camadas**: L1 (local) + L2 (Redis)
3. **Metrics**: Integração com Prometheus/Grafana
4. **Backup Automático**: Snapshots programados
5. **Geolocalização**: Sessions por região

### Monitoramento Avançado
- Dashboard Grafana para métricas Redis
- Alertas para falhas de conexão
- Relatórios de performance

---

## 📝 Resumo da Implementação

✅ **Concluído**:
- Configuração Redis completa
- Migração de controllers e middleware
- Health checks e monitoramento
- Scripts de setup automatizado
- Documentação completa

✅ **Benefícios Obtidos**:
- Performance superior
- Escalabilidade horizontal
- Persistência de dados
- Monitoramento avançado
- Produção-ready

O sistema agora está pronto para ambientes de produção com Redis como backend de sessions, oferecendo performance, confiabilidade e escalabilidade superiores ao sistema anterior em memória.
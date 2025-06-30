# Sistema de Autenticação para Iframe

## 📋 Visão Geral

Este sistema implementa uma solução de segurança para controlar o acesso ao iframe através de **Session IDs únicos e de uso único**. Cada session ID pode ser usado apenas uma vez e expira automaticamente após um período determinado.

## 🔒 Como Funciona

### 1. Geração de Session ID
- **Endpoint**: `POST /auth/create-session`
- Cria um session ID único (UUID)
- Define tempo de expiração (30 minutos por padrão)
- Retorna a URL completa para o iframe

### 2. Validação e Uso Único
- O middleware `IframeAuthMiddleware` intercepta todas as requisições para `/client/iframe.html`
- Verifica se existe um `session_id` válido na URL
- Marca a session como "usada" na primeira chamada
- Bloqueia tentativas subsequentes de usar o mesmo session ID

### 3. Expiração Automática
- Sessions expiram em 30 minutos se não utilizadas
- Cleanup automático remove sessions expiradas
- Limite máximo de 1000 sessions simultâneas

## 🚀 Endpoints da API

### Criar Nova Session
```http
POST /auth/create-session
```

**Resposta de Sucesso:**
```json
{
  "session_id": "123e4567-e89b-12d3-a456-426614174000",
  "expires_in_minutes": 30,
  "iframe_url": "/client/iframe.html?session_id=123e4567-e89b-12d3-a456-426614174000"
}
```

### Validar Session
```http
GET /auth/validate-session?session_id=<SESSION_ID>
```

**Resposta de Sucesso:**
```json
{
  "valid": true,
  "message": "Session válida",
  "session_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

### Status das Sessions
```http
GET /auth/session-status
```

**Resposta:**
```json
{
  "total_sessions": 5,
  "active_sessions": 3,
  "used_sessions": 2,
  "max_sessions": 1000
}
```

### Limpar Sessions Expiradas
```http
DELETE /auth/cleanup-sessions
```

**Resposta:**
```json
{
  "message": "Limpeza de sessions concluída",
  "sessions_removed": 2,
  "sessions_remaining": 3
}
```

## 🎯 Exemplos de Uso

### 1. Implementação Básica

```javascript
// 1. Criar uma nova session
const response = await fetch('/auth/create-session', {
    method: 'POST'
});
const sessionData = await response.json();

// 2. Usar a URL do iframe
const iframe = document.createElement('iframe');
iframe.src = sessionData.iframe_url;
document.body.appendChild(iframe);

// 3. O session ID será invalidado após o carregamento
```

### 2. Verificar Status da Session

```javascript
// Verificar se uma session ainda é válida
const isValid = await fetch(`/auth/validate-session?session_id=${sessionId}`);
if (isValid.ok) {
    console.log('Session ainda é válida');
} else {
    console.log('Session inválida ou já usada');
}
```

## 🛡️ Características de Segurança

### ✅ Protecções Implementadas
- **Uso Único**: Cada session ID só pode ser usado uma vez
- **Expiração Temporal**: Sessions expiram em 30 minutos
- **UUIDs Únicos**: Session IDs são gerados como UUIDs v4
- **Validação Rigorosa**: Middleware intercepta e valida todas as requisições
- **Cleanup Automático**: Remove sessions expiradas automaticamente
- **Limite de Sessions**: Máximo de 1000 sessions simultâneas

### ❌ Tentativas de Acesso Bloqueadas
- Acesso sem session ID
- Session ID inválido ou inexistente
- Session ID já utilizado
- Session ID expirado
- Excesso de limite de sessions

## 🎨 Página de Demonstração

Acesse `/auth-demo` para ver uma demonstração interativa do sistema:

- **Criar Sessions**: Teste a criação de novos session IDs
- **Abrir Iframe**: Use session IDs válidos para carregar o iframe
- **Acesso Inválido**: Teste tentativas de acesso sem autenticação
- **Monitoramento**: Veja estatísticas em tempo real
- **Log de Atividades**: Acompanhe todas as operações

## ⚙️ Configurações

As configurações podem ser modificadas no arquivo `app/controllers/auth_controller.py`:

```python
# Tempo de expiração das sessions (em minutos)
SESSION_EXPIRY_MINUTES = 30

# Máximo de sessions simultâneas
MAX_SESSIONS = 1000
```

## 🔧 Estrutura do Código

```
app/
├── controllers/
│   └── auth_controller.py      # Lógica de autenticação
├── middleware/
│   └── auth_middleware.py      # Middleware de proteção
└── main.py                     # Configuração da aplicação

client/
├── iframe.html                 # Iframe protegido
└── auth-demo.html             # Página de demonstração
```

## 🚨 Considerações para Produção

### Para Uso em Produção, Considere:

1. **Armazenamento Persistente**: Substitua o armazenamento em memória por Redis ou banco de dados
2. **Rate Limiting**: Implemente limitação de taxa para criação de sessions
3. **Logs de Auditoria**: Adicione logs detalhados para auditoria de segurança
4. **HTTPS Obrigatório**: Use apenas HTTPS em produção
5. **Configurações de CORS**: Restrinja origens permitidas
6. **Monitoramento**: Implemente alertas para tentativas de acesso suspeitas

### Exemplo de Implementação com Redis:

```python
import redis
import json
from datetime import datetime, timedelta

# Conectar ao Redis
redis_client = redis.Redis(host='localhost', port=6379, db=0)

def store_session(session_id: str, session_data: dict):
    """Armazena session no Redis com TTL"""
    redis_client.setex(
        f"session:{session_id}", 
        SESSION_EXPIRY_MINUTES * 60,  # TTL em segundos
        json.dumps(session_data, default=str)
    )

def get_session(session_id: str) -> dict:
    """Recupera session do Redis"""
    data = redis_client.get(f"session:{session_id}")
    return json.loads(data) if data else None
```

## 📞 Suporte

Para dúvidas sobre implementação ou customização do sistema de autenticação, consulte:
- Código fonte em `app/controllers/auth_controller.py`
- Middleware em `app/middleware/auth_middleware.py`
- Demonstração em `/auth-demo`
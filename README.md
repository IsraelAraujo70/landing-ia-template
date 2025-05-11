# Assistente IA AgiFinance

Este projeto implementa um assistente de IA para o suporte do AgiFinance, utilizando processamento de linguagem natural e recuperação de informações baseada em vetores para responder perguntas sobre finanças pessoais, gestão financeira e uso da plataforma AgiFinance.

## Características

- API RESTful usando FastAPI
- Suporte a WebSocket para chat em tempo real
- Processamento de documentos PDF, TXT e Markdown
- Armazenamento de embeddings usando FAISS
- Containerização com Docker
- Configuração para deploy no GOCD
- Integração com AgiFinance via iframe

## Requisitos

- Python 3.10+
- Docker e Docker Compose (para desenvolvimento local e produção)
- Chave de API da OpenAI

## Configuração

1. Clone o repositório:
   ```
   git clone https://github.com/IsraelAraujo70/ia-suporte.git
   cd ia-suporte
   ```

2. Crie um arquivo `.env` baseado no `.env.example`:
   ```
   cp .env.example .env
   ```

3. Edite o arquivo `.env` e adicione sua chave de API da OpenAI:
   ```
   OPENAI_API_KEY=sua_chave_api_aqui
   ```

## Desenvolvimento Local

### Usando Docker Compose

```bash
docker-compose up --build
```

### Sem Docker

1. Crie um ambiente virtual Python:
   ```
   python -m venv venv
   source venv/bin/activate  # No Windows: venv\Scripts\activate
   ```

2. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```

3. Execute a aplicação:
   ```
   uvicorn app:app --reload --host 0.0.0.0 --port 8000
   ```

## Uso da API

A API estará disponível em `http://localhost:8000` durante o desenvolvimento local. Em produção, será integrada ao AgiFinance via iframe.

### Endpoints Principais

- `GET /`: Verifica o status da API
- `GET /documents`: Lista todos os documentos carregados
- `POST /upload`: Faz upload de um novo documento
- `POST /perguntar`: Envia uma pergunta e recebe uma resposta
- `WebSocket /ws/chat/{session_id}`: Conecta-se ao chat em tempo real

### Exemplo de Uso do WebSocket

```javascript
// Conectar ao WebSocket
const socket = new WebSocket('ws://localhost:8000/ws/chat/session123');

// Receber mensagens
socket.onmessage = function(event) {
  const message = JSON.parse(event.data);
  console.log('Mensagem recebida:', message);
};

// Enviar uma pergunta
socket.send(JSON.stringify({
  question: 'Como posso visualizar meus gastos mensais?',
  top_k: 5
}));
```

## Estrutura de Diretórios

```
agifinance-assistente/
├── app.py                # Código principal da aplicação
├── Dockerfile            # Configuração do Docker
├── docker-compose.yml    # Configuração do Docker Compose
├── requirements.txt      # Dependências Python
├── .env.example          # Exemplo de variáveis de ambiente
├── gocd.yaml             # Configuração do GOCD para CI/CD
├── uploads/              # Diretório para documentos carregados
└── faiss_index/          # Diretório para o índice FAISS
```

## Deploy

O deploy pode ser feito manualmente ou integrado ao pipeline de CI/CD do AgiFinance:

1. Build da imagem Docker
2. Execução de testes

## Licença

Proprietário - Israel Araujo

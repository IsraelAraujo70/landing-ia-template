# Assistente IA Ada Sistemas

Este projeto implementa um assistente de IA para o suporte da Ada Sistemas, utilizando processamento de linguagem natural e recuperação de informações baseada em vetores para responder perguntas com base em documentos carregados.

## Características

- API RESTful usando FastAPI
- Suporte a WebSocket para chat em tempo real
- Processamento de documentos PDF, TXT e Markdown
- Armazenamento de embeddings usando FAISS
- Containerização com Docker
- Configuração para deploy no GOCD
- Hospedagem na AWS (https://aws.adasistemas.com.br/assistente)

## Requisitos

- Python 3.10+
- Docker e Docker Compose (para desenvolvimento local e produção)
- Chave de API da OpenAI

## Configuração

1. Clone o repositório:
   ```
   git clone https://github.com/adasistemas/ada-assistente.git
   cd ada-assistente
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

A API estará disponível em `http://localhost:8000` durante o desenvolvimento local ou em `https://aws.adasistemas.com.br/assistente` em produção.

### Endpoints Principais

- `GET /`: Verifica o status da API
- `GET /documents`: Lista todos os documentos carregados
- `POST /upload`: Faz upload de um novo documento
- `POST /perguntar`: Envia uma pergunta e recebe uma resposta
- `WebSocket /ws/chat/{session_id}`: Conecta-se ao chat em tempo real

### Exemplo de Uso do WebSocket

```javascript
// Conectar ao WebSocket
const socket = new WebSocket('wss://aws.adasistemas.com.br/assistente/ws/chat/session123');

// Receber mensagens
socket.onmessage = function(event) {
  const message = JSON.parse(event.data);
  console.log('Mensagem recebida:', message);
};

// Enviar uma pergunta
socket.send(JSON.stringify({
  question: 'Como posso resetar minha senha?',
  top_k: 5
}));
```

## Estrutura de Diretórios

```
ada-assistente/
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

O deploy é automatizado através do GOCD usando o arquivo `gocd.yaml`. O pipeline inclui:

1. Build da imagem Docker
2. Execução de testes
3. Deploy na AWS (após aprovação manual)

## Licença

Proprietário - Ada Sistemas

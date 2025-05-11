// Script específico para a página principal do assistente AgiFinance

document.addEventListener('DOMContentLoaded', function() {
    // Verificar se estamos no modo de desenvolvimento
    const isDev = window.location.search.includes('dev=f9a6e6f8-9c6d-4b0b-8b4d-7e5c6f2a0f1d');

    // Mostrar ou ocultar elementos com base nas verificações
    if (isDev) {
        document.getElementById('sources-container').style.display = 'block';
        document.getElementById('documents-container').style.display = 'block';
    } else {
        document.getElementById('sources-container').style.display = 'none';
        document.getElementById('documents-container').style.display = 'none';
    }

    // Obter configurações com base no ambiente
    const config = detectEnvironment(isDev);
    const API_BASE_URL = config.apiBaseUrl;
    const WS_BASE_URL = config.wsBaseUrl;

    // Gerar um ID de sessão único
    const sessionId = generateSessionId();

    let socket;
    let isConnected = false;

    // Elementos DOM
    const chatMessages = document.getElementById('chat-messages');
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const connectionStatus = document.getElementById('connection-status');
    const sourcesContainer = document.getElementById('sources-container');
    const sourcesList = document.getElementById('sources-list');
    const fileUpload = document.getElementById('file-upload');
    const uploadButton = document.getElementById('upload-button');
    const uploadStatus = document.getElementById('upload-status');
    const documentsList = document.getElementById('documents-list');

    // Conectar ao WebSocket
    function initWebSocket() {
        socket = connectWebSocket(WS_BASE_URL, sessionId, {
            onOpen: function() {
                isConnected = true;
                connectionStatus.textContent = 'Conectado';
                connectionStatus.style.color = 'green';
                addSystemMessage('Conectado ao assistente', chatMessages);
            },
            onMessage: function(event) {
                const message = JSON.parse(event.data);
                console.log('Mensagem recebida:', message);

                // Remover indicador de digitação se existir
                const typingIndicator = document.querySelector('.typing-indicator');
                if (typingIndicator) {
                    typingIndicator.remove();
                }

                if (message.typing) {
                    // Mostrar indicador de digitação
                    const typingDiv = document.createElement('div');
                    typingDiv.className = 'message assistant-message typing-indicator';
                    typingDiv.innerHTML = '<span></span><span></span><span></span>';
                    chatMessages.appendChild(typingDiv);
                    chatMessages.scrollTop = chatMessages.scrollHeight;
                } else if (message.role === 'assistant') {
                    // Adicionar mensagem do assistente
                    addAssistantMessage(message.content, chatMessages);

                    // Mostrar fontes se disponíveis
                    if (message.sources && message.sources.length > 0) {
                        showSources(message.sources, sourcesList, sourcesContainer);
                    } else {
                        sourcesContainer.style.display = 'none';
                    }
                } else if (message.role === 'user') {
                    // Não adicionar mensagem do usuário aqui, pois já foi adicionada ao enviar
                    // Apenas registrar no console para depuração
                    console.log('Mensagem do usuário recebida via WebSocket:', message.content);
                } else if (message.role === 'system' || message.error) {
                    // Adicionar mensagem do sistema ou erro
                    addSystemMessage(message.content || message.error, chatMessages);
                }
            },
            onClose: function() {
                isConnected = false;
                connectionStatus.textContent = 'Desconectado';
                connectionStatus.style.color = 'red';
                addSystemMessage('Desconectado do assistente. Tentando reconectar...', chatMessages);

                // Tentar reconectar após 3 segundos
                setTimeout(initWebSocket, 3000);
            },
            onError: function(error) {
                console.error('Erro WebSocket:', error);
                addSystemMessage('Erro na conexão', chatMessages);
            }
        });
    }

    // Enviar mensagem
    function sendMessage() {
        const message = messageInput.value.trim();

        if (message && isConnected) {
            // Adicionar mensagem do usuário ao chat
            addUserMessage(message, chatMessages);

            // Enviar mensagem para o servidor
            socket.send(JSON.stringify({
                question: message,
                top_k: 5
            }));

            // Limpar campo de entrada
            messageInput.value = '';
        } else if (!isConnected) {
            addSystemMessage('Não foi possível enviar a mensagem. Reconectando...', chatMessages);
            initWebSocket();
        }
    }

    // Carregar lista de documentos
    async function loadDocuments() {
        try {
            const response = await fetch(`${API_BASE_URL}/documents`);
            const documents = await response.json();

            if (documents.length === 0) {
                documentsList.innerHTML = '<p>Nenhum documento carregado</p>';
                return;
            }

            documentsList.innerHTML = '';

            documents.forEach(doc => {
                const docDiv = document.createElement('div');
                docDiv.className = 'card mb-2';

                docDiv.innerHTML = `
                    <div class="card-body">
                        <h5 class="card-title">${doc.filename}</h5>
                        <p class="card-text">
                            <small class="text-muted">Tipo: ${doc.type}</small><br>
                            <small class="text-muted">Tamanho: ${formatFileSize(doc.size)}</small><br>
                            <small class="text-muted">Carregado em: ${doc.upload_time}</small>
                        </p>
                    </div>
                `;

                documentsList.appendChild(docDiv);
            });
        } catch (error) {
            console.error('Erro ao carregar documentos:', error);
            documentsList.innerHTML = '<p class="text-danger">Erro ao carregar documentos</p>';
        }
    }

    // Fazer upload de documento
    async function uploadDocument() {
        const file = fileUpload.files[0];

        if (!file) {
            uploadStatus.innerHTML = '<p class="text-danger">Selecione um arquivo para enviar</p>';
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        uploadStatus.innerHTML = '<p>Enviando documento...</p>';

        try {
            const response = await fetch(`${API_BASE_URL}/upload`, {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (response.ok) {
                uploadStatus.innerHTML = `<p class="text-success">Documento "${result.filename}" enviado com sucesso!</p>`;
                fileUpload.value = '';
                loadDocuments();
            } else {
                uploadStatus.innerHTML = `<p class="text-danger">Erro ao enviar documento: ${result.detail}</p>`;
            }
        } catch (error) {
            console.error('Erro ao enviar documento:', error);
            uploadStatus.innerHTML = `<p class="text-danger">Erro ao enviar documento: ${error.message}</p>`;
        }
    }

    // Event listeners
    sendButton.addEventListener('click', sendMessage);

    messageInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });

    uploadButton.addEventListener('click', uploadDocument);

    // Inicializar
    initWebSocket();
    loadDocuments();
});

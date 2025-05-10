/**
 * ADA ASSISTENTE - FUNÇÕES JAVASCRIPT COMUNS
 * Última atualização: 09/05/2025
 * 
 * Este arquivo contém funções compartilhadas entre as diferentes interfaces do chat.
 * Inclui funções para detecção de ambiente, manipulação de mensagens e conexão WebSocket.
 */

// Configurações - Detecção automática de ambiente
function detectEnvironment(isDev = false) {
    const hostname = window.location.hostname;
    const urlParams = new URLSearchParams(window.location.search);
    
    // Verificar se devemos usar ambiente de desenvolvimento
    const useDev = urlParams.get('useDev') === 'true' || isDev;
    
    if (useDev || hostname === 'localhost' || hostname === '127.0.0.1') {
        return {
            apiBaseUrl: 'http://localhost:8000',
            wsBaseUrl: 'ws://localhost:8000'
        };
    } else {
        return {
            apiBaseUrl: 'https://aws.adasistemas.com.br/assistente',
            wsBaseUrl: 'wss://aws.adasistemas.com.br/assistente'
        };
    }
}

// Gerar um ID de sessão único
function generateSessionId() {
    return 'session-' + Math.random().toString(36).substring(2, 15);
}

// Adicionar mensagem do usuário ao chat
function addUserMessage(text, chatMessages) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message user-message';
    messageDiv.textContent = text;
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Adicionar mensagem do assistente ao chat com suporte a Markdown
function addAssistantMessage(text, chatMessages) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message assistant-message';
    
    // Configurar marked.js para abrir links em nova aba
    marked.setOptions({
        breaks: true, // Quebras de linha são respeitadas
        gfm: true,    // GitHub Flavored Markdown
        sanitize: false, // Não sanitizar, permitir HTML
    });
    
    // Renderizar Markdown para HTML
    messageDiv.innerHTML = marked.parse(text);
    
    // Configurar todos os links para abrir em nova aba
    const links = messageDiv.querySelectorAll('a');
    links.forEach(link => {
        link.setAttribute('target', '_blank');
        link.setAttribute('rel', 'noopener noreferrer');
    });
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Adicionar mensagem do sistema ao chat
function addSystemMessage(text, chatMessages) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message system-message';
    messageDiv.textContent = text;
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Mostrar fontes de informação
function showSources(sources, sourcesList, sourcesContainer) {
    sourcesList.innerHTML = '';
    
    sources.forEach((source, index) => {
        const sourceDiv = document.createElement('div');
        sourceDiv.className = 'source-item';
        
        const metadata = source.metadata || {};
        const filename = metadata.filename || 'Documento desconhecido';
        
        sourceDiv.innerHTML = `
            <h5>Fonte ${index + 1}: ${filename}</h5>
            <p>${source.content}</p>
        `;
        
        sourcesList.appendChild(sourceDiv);
    });
    
    sourcesContainer.style.display = 'block';
}

// Formatar tamanho de arquivo
function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' bytes';
    else if (bytes < 1048576) return (bytes / 1024).toFixed(2) + ' KB';
    else return (bytes / 1048576).toFixed(2) + ' MB';
}

// Conectar ao WebSocket
function connectWebSocket(wsBaseUrl, sessionId, handlers) {
    const socket = new WebSocket(`${wsBaseUrl}/ws/chat/${sessionId}`);
    
    socket.onopen = function() {
        if (handlers.onOpen) handlers.onOpen();
    };
    
    socket.onmessage = function(event) {
        if (handlers.onMessage) handlers.onMessage(event);
    };
    
    socket.onclose = function() {
        if (handlers.onClose) handlers.onClose();
    };
    
    socket.onerror = function(error) {
        if (handlers.onError) handlers.onError(error);
    };
    
    return socket;
}

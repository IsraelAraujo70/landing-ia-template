// Script específico para a página iframe do assistente AgiFinance

document.addEventListener('DOMContentLoaded', function() {
    // Verificar parâmetros da URL
    const urlParams = new URLSearchParams(window.location.search);
    const useDev = urlParams.get('useDev') === 'true';
    
    // Obter configurações com base no ambiente
    const config = detectEnvironment(useDev);
    const API_BASE_URL = config.apiBaseUrl;
    const WS_BASE_URL = config.wsBaseUrl;
    
    // Gerar um ID de sessão único
    const sessionId = generateSessionId();
    
    let socket;
    let isConnected = false;
    let isTyping = false;
    
    // Elementos do DOM
    const chatMessages = document.getElementById('chat-messages');
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    
    // Conectar ao WebSocket
    function initWebSocket() {
        socket = connectWebSocket(WS_BASE_URL, sessionId, {
            onOpen: function() {
                isConnected = true;
                addSystemMessage('Conectado ao assistente', chatMessages);
            },
            onMessage: function(event) {
                const message = JSON.parse(event.data);
                
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
                } else if (message.role === 'user') {
                    // Não adicionar mensagem do usuário aqui, pois já foi adicionada ao enviar
                } else if (message.role === 'system' || message.error) {
                    // Adicionar mensagem do sistema ou erro
                    addSystemMessage(message.content || message.error, chatMessages);
                }
            },
            onClose: function() {
                isConnected = false;
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
    
    // Event listeners
    sendButton.addEventListener('click', sendMessage);
    
    messageInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
    
    // Inicializar
    initWebSocket();
});

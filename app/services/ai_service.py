"""
AI service for generating answers using OpenAI.
"""
from typing import List, Dict, Any, Tuple
from langchain.docstore.document import Document
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage
import tiktoken
from app.config.settings import OPENAI_API_KEY, CHAT_MODEL, TEMPERATURE, logger

# Initialize OpenAI chat model
chat_model = ChatOpenAI(
    model_name=CHAT_MODEL,
    temperature=TEMPERATURE,
    api_key=OPENAI_API_KEY
)

# Initialize tokenizer
tokenizer = tiktoken.get_encoding("cl100k_base")

def count_tokens(text: str) -> int:
    """
    Count the number of tokens in a text.
    
    Args:
        text: Text to count tokens
        
    Returns:
        Number of tokens
    """
    tokens = tokenizer.encode(text)
    return len(tokens)

def split_context_by_tokens(context_docs: List[Document], max_tokens: int = 250000) -> List[List[Document]]:
    """
    Split context documents into batches that don't exceed the token limit.
    
    Args:
        context_docs: List of context Document objects
        max_tokens: Maximum number of tokens per batch
        
    Returns:
        List of batches of Document objects
    """
    batches = []
    current_batch = []
    current_tokens = 0
    
    for doc in context_docs:
        doc_tokens = count_tokens(doc.page_content)
        
        # If a single document exceeds the token limit, we need to split it
        if doc_tokens > max_tokens:
            # If we have documents in the current batch, add them as a batch
            if current_batch:
                batches.append(current_batch)
                current_batch = []
                current_tokens = 0
            
            # Split the large document into smaller chunks
            text = doc.page_content
            chunks = []
            start = 0
            
            while start < len(text):
                # Try with a chunk of 1000 characters first
                end = start + 1000
                if end > len(text):
                    end = len(text)
                
                chunk = text[start:end]
                chunk_tokens = count_tokens(chunk)
                
                # Adjust chunk size to fit within token limit
                while chunk_tokens > max_tokens and end > start + 100:
                    end = start + int((end - start) * 0.8)  # Reduce by 20%
                    chunk = text[start:end]
                    chunk_tokens = count_tokens(chunk)
                
                # Create a new document with the chunk
                chunk_doc = Document(
                    page_content=chunk,
                    metadata=doc.metadata.copy()
                )
                chunks.append(chunk_doc)
                
                start = end
            
            # Add each chunk as its own batch
            for chunk_doc in chunks:
                batches.append([chunk_doc])
        
        # If adding this document would exceed the token limit, start a new batch
        elif current_tokens + doc_tokens > max_tokens:
            batches.append(current_batch)
            current_batch = [doc]
            current_tokens = doc_tokens
        
        # Otherwise, add the document to the current batch
        else:
            current_batch.append(doc)
            current_tokens += doc_tokens
    
    # Add the last batch if it's not empty
    if current_batch:
        batches.append(current_batch)
    
    return batches

async def generate_answer(question: str, context_docs: List[Document], chat_history: List[Dict[str, Any]] = []) -> str:
    """
    Generate an answer using OpenAI based on the question, context documents, and chat history.
    
    Args:
        question: User's question
        context_docs: List of context Document objects
        chat_history: Chat history
        
    Returns:
        Generated answer
    """
    
    # Verificar se o usuário está pedindo para falar com um humano
    question_lower = question.lower()
    human_request_keywords = [
        "falar com humano", "falar com uma pessoa", "falar com atendente",
        "quero falar com alguém", "preciso de um humano", "atendimento humano",
        "pessoa real", "atendente real", "contato humano", "suporte humano"
    ]
    
    if any(keyword in question_lower for keyword in human_request_keywords):
        return "Entendo que você prefere falar com um humano. Você pode entrar em contato com nossa equipe pelo WhatsApp clicando neste link: [Falar com atendente](https://wa.me/553537217123). Estamos disponíveis de segunda a sexta, das 8h às 18h. Posso ajudar com mais alguma coisa?"
    
    try:
        # Extrair as últimas 5 mensagens do histórico de chat (ou menos se não houver tantas)
        recent_history = chat_history[-5:] if len(chat_history) > 5 else chat_history
        
        # Formatar o histórico de chat para o prompt
        formatted_history = ""
        for msg in recent_history:
            role = msg.get("role", "")
            content = msg.get("content", "")
            if role and content:
                formatted_history += f"\n{role.capitalize()}: {content}"
        
        # Dividir os documentos em lotes para não exceder o limite de tokens
        MAX_TOKENS_PER_REQUEST = 250000  # Limite seguro abaixo do máximo de 300.000
        batches = split_context_by_tokens(context_docs, MAX_TOKENS_PER_REQUEST)
        
        if not batches:
            logger.warning("Nenhum documento de contexto disponível para a pergunta.")
            return "Não encontrei informações relevantes para responder à sua pergunta. Por favor, tente reformular ou forneça mais detalhes."
        
        # Se houver apenas um lote, processe normalmente
        if len(batches) == 1:
            return await process_single_batch(question, batches[0], formatted_history)
        
        # Se houver múltiplos lotes, processe cada um e combine as respostas
        logger.info(f"Dividindo contexto em {len(batches)} lotes devido ao tamanho do documento")
        
        all_answers = []
        for i, batch in enumerate(batches):
            logger.info(f"Processando lote {i+1} de {len(batches)}")
            batch_answer = await process_single_batch(question, batch, formatted_history)
            all_answers.append(batch_answer)
        
        # Combinar as respostas dos diferentes lotes
        combined_answer = ""
        
        # Criar um novo prompt para sintetizar as respostas
        synthesis_prompt = f"""Você é Ada, uma assistente de IA da Ada Sistemas.

Você recebeu as seguintes respostas parciais para a pergunta: "{question}"

Respostas parciais:
{' '.join(all_answers)}

Por favor, sintetize essas respostas em uma única resposta coerente e concisa. Remova qualquer redundância e organize as informações de forma lógica.
"""
        
        # Criar mensagens para sintetizar
        synthesis_messages = [
            {"role": "system", "content": synthesis_prompt}
        ]
        
        # Gerar resposta sintetizada
        synthesis_response = chat_model.invoke(synthesis_messages)
        final_answer = synthesis_response.content
        
        logger.info(f"Resposta final sintetizada para a pergunta: {question[:50]}...")
        return final_answer
        
    except Exception as e:
        logger.error(f"Erro ao gerar resposta: {str(e)}")
        raise ValueError(f"Erro ao gerar resposta: {str(e)}")

async def process_single_batch(question: str, batch_docs: List[Document], formatted_history: str) -> str:
    """
    Process a single batch of documents to generate an answer.
    
    Args:
        question: User's question
        batch_docs: Batch of Document objects
        formatted_history: Formatted chat history
        
    Returns:
        Generated answer for this batch
    """
    # Preparar o contexto a partir dos documentos do lote
    context_text = ""
    for i, doc in enumerate(batch_docs):
        # Adicionar metadados e conteúdo do documento
        source = doc.metadata.get("source", "Desconhecido")
        page = doc.metadata.get("page", "N/A")
        context_text += f"\n\nDocumento {i+1} (Fonte: {source}, Página: {page}):\n{doc.page_content}"
    
    # Verificar o tamanho do contexto em tokens
    context_tokens = count_tokens(context_text)
    logger.info(f"Tamanho do contexto: {context_tokens} tokens")
    
    # Criar o prompt do sistema
    system_prompt = f"""Você é Ada, uma assistente de IA da Ada Sistemas, especializada em responder perguntas com base em documentos.
    
Regras:
1. Use APENAS as informações fornecidas nos documentos para responder às perguntas.
2. Se a informação não estiver nos documentos, diga que não pode responder com base no treinamento atual.
3. Seja concisa e direta em suas respostas.
4. Não invente informações ou faça suposições além do que está nos documentos.
5. Não cite as fontes dos documentos.
6. Mantenha um tom profissional e amigável.
7. Se o usuário pedir para falar com um humano ou atendente, forneça o link para o WhatsApp https://wa.me/553537217123 e informe que o atendimento está disponível de segunda a sexta, das 8h às 18h.
Histórico de conversa recente:{formatted_history}

Contexto dos documentos:
{context_text}
"""
    
    # Criar o prompt do usuário
    user_prompt = f"Pergunta: {question}"
    
    # Criar mensagens diretamente sem usar ChatPromptTemplate
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    # Gerar resposta
    response = chat_model.invoke(messages)
    answer = response.content
    
    return answer

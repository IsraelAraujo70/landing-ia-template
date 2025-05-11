"""
Serviço de IA para geração de respostas usando OpenAI.
"""
from typing import List, Dict, Any, Tuple
import random
from langchain.docstore.document import Document
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage
import tiktoken
from app.config.settings import OPENAI_API_KEY, CHAT_MODEL, TEMPERATURE, logger

# Inicializa o modelo de chat OpenAI
chat_model = ChatOpenAI(
    model_name=CHAT_MODEL,
    temperature=TEMPERATURE,
    api_key=OPENAI_API_KEY
)

# Inicializa o tokenizador
tokenizer = tiktoken.get_encoding("cl100k_base")

def count_tokens(text: str) -> int:
    """
    Conta o número de tokens em um texto.
    
    Args:
        text: Texto para contar tokens
        
    Retorna:
        Número de tokens
    """
    tokens = tokenizer.encode(text)
    return len(tokens)

def split_context_by_tokens(context_docs: List[Document], max_tokens: int = 250000) -> List[List[Document]]:
    """
    Divide documentos de contexto em lotes que não excedam o limite de tokens.
    
    Args:
        context_docs: Lista de objetos Document de contexto
        max_tokens: Número máximo de tokens por lote
        
    Retorna:
        Lista de lotes de objetos Document
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
    Gera uma resposta usando OpenAI com base na pergunta, documentos de contexto e histórico de chat.
    
    Args:
        question: Pergunta do usuário
        context_docs: Lista de objetos Document de contexto
        chat_history: Histórico de chat
        
    Retorna:
        Resposta gerada
    """
    
    try:
        from app.config.agifinance_prompts import SYSTEM_PROMPT, ANSWER_PROMPT, FINANCIAL_TIPS, FINANCIAL_GLOSSARY
    except ImportError as e:
        logger.error(f"Erro ao importar prompts do AgiFinance: {str(e)}")
    
    question_lower = question.lower()
    human_request_keywords = [
        "falar com humano", "falar com uma pessoa", "falar com atendente",
        "quero falar com alguém", "preciso de um humano", "atendimento humano",
        "pessoa real", "atendente real", "contato humano", "suporte humano"
    ]
    
    if any(keyword in question_lower for keyword in human_request_keywords):
        return "Entendo que você prefere falar com um humano. Você pode entrar em contato com nossa equipe de suporte do AgiFinance pelo email support@agifinance.com.br ou pelo chat no site principal. Estamos disponíveis de segunda a sexta, das 9h às 18h. Posso ajudar com mais alguma coisa?"
    
    try:
        recent_history = chat_history[-5:] if len(chat_history) > 5 else chat_history
        
        formatted_history = ""
        for msg in recent_history:
            role = msg.get("role", "")
            content = msg.get("content", "")
            if role and content:
                formatted_history += f"\n{role.capitalize()}: {content}"
        
        MAX_TOKENS_PER_REQUEST = 250000  # Limite seguro abaixo do máximo de 300.000
        batches = split_context_by_tokens(context_docs, MAX_TOKENS_PER_REQUEST)
        
        if not batches:
            logger.warning("Nenhum documento de contexto disponível para a pergunta.")
            return "Não encontrei informações relevantes para responder à sua pergunta. Por favor, tente reformular ou forneça mais detalhes."
        
        if len(batches) == 1:
            return await process_single_batch(question, batches[0], formatted_history)
        
        logger.info(f"Dividindo contexto em {len(batches)} lotes devido ao tamanho do documento")
        
        all_answers = []
        for i, batch in enumerate(batches):
            logger.info(f"Processando lote {i+1} de {len(batches)}")
            batch_answer = await process_single_batch(question, batch, formatted_history)
            all_answers.append(batch_answer)
        
        combined_answer = ""
        
        synthesis_prompt = f"""Você é o assistente de IA do AgiFinance, uma plataforma moderna de gestão financeira pessoal.

Você recebeu as seguintes respostas parciais para a pergunta: "{question}"

Respostas parciais:
{' '.join(all_answers)}

Por favor, sintetize essas respostas em uma única resposta coerente e concisa. Remova qualquer redundância e organize as informações de forma lógica. Mantenha o foco em finanças pessoais e no uso da plataforma AgiFinance.
"""
        
        synthesis_messages = [
            {"role": "system", "content": synthesis_prompt}
        ]
        
        synthesis_response = chat_model.invoke(synthesis_messages)
        final_answer = synthesis_response.content
        
        logger.info(f"Resposta final sintetizada para a pergunta: {question[:50]}...")
        return final_answer
        
    except Exception as e:
        logger.error(f"Erro ao gerar resposta: {str(e)}")
        raise ValueError(f"Erro ao gerar resposta: {str(e)}")

async def process_single_batch(question: str, batch_docs: List[Document], formatted_history: str) -> str:
    """
    Processa um único lote de documentos para gerar uma resposta.
    
    Args:
        question: Pergunta do usuário
        batch_docs: Lote de objetos Document
        formatted_history: Histórico de chat formatado
        
    Retorna:
        Resposta gerada para este lote
    """
    context_text = ""
    for i, doc in enumerate(batch_docs):
        source = doc.metadata.get("source", "Desconhecido")
        page = doc.metadata.get("page", "N/A")
        context_text += f"\n\nDocumento {i+1} (Fonte: {source}, Página: {page}):\n{doc.page_content}"
    
    context_tokens = count_tokens(context_text)
    logger.info(f"Tamanho do contexto: {context_tokens} tokens")
    
    try:
        financial_tip = f"\n\nDICA FINANCEIRA: {random.choice(FINANCIAL_TIPS)}" if random.random() < 0.3 else ""
    except Exception as e:
        logger.error(f"Erro ao gerar dica financeira: {str(e)}")
        financial_tip = ""
    
    system_prompt = f"""Você é o assistente de IA do AgiFinance, uma plataforma moderna de gestão financeira pessoal.
Seu objetivo é ajudar os usuários a gerenciar suas finanças e utilizar efetivamente as funcionalidades do AgiFinance.

Histórico de conversa recente:{formatted_history}

Contexto dos documentos:
{context_text}{financial_tip}
"""
    
    user_prompt = f"Pergunta: {question}"
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    # Gerar resposta
    response = chat_model.invoke(messages)
    answer = response.content
    
    return answer

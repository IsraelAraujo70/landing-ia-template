"""
Vector database utilities for the Ada Assistant application.
"""
import os
import numpy as np
import tiktoken
from typing import List, Optional, Any
from langchain.docstore.document import Document
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from app.config.settings import OPENAI_API_KEY, FAISS_INDEX_PATH, EMBEDDINGS_MODEL, logger

# Initialize embeddings model
embeddings_model = OpenAIEmbeddings(
    model=EMBEDDINGS_MODEL,
    openai_api_key=OPENAI_API_KEY
)

# Initialize tokenizer for token counting
tokenizer = tiktoken.get_encoding("cl100k_base")

# Global vector database instance
vector_db = None

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

def batch_documents_by_tokens(documents: List[Document], max_tokens_per_batch: int = 250000) -> List[List[Document]]:
    """
    Divide documents into batches based on token count.
    
    Args:
        documents: List of Document objects
        max_tokens_per_batch: Maximum tokens per batch
        
    Returns:
        List of document batches
    """
    batches = []
    current_batch = []
    current_batch_tokens = 0
    
    for doc in documents:
        # Count tokens in the document
        doc_tokens = count_tokens(doc.page_content)
        
        # If a single document exceeds the token limit, we need to split it
        if doc_tokens > max_tokens_per_batch:
            # If we have documents in the current batch, add them as a batch
            if current_batch:
                batches.append(current_batch)
                current_batch = []
                current_batch_tokens = 0
            
            # Split the large document into smaller chunks
            logger.warning(f"Documento muito grande ({doc_tokens} tokens). Dividindo em chunks menores.")
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
                while chunk_tokens > max_tokens_per_batch and end > start + 100:
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
        elif current_batch_tokens + doc_tokens > max_tokens_per_batch:
            batches.append(current_batch)
            current_batch = [doc]
            current_batch_tokens = doc_tokens
        
        # Otherwise, add the document to the current batch
        else:
            current_batch.append(doc)
            current_batch_tokens += doc_tokens
    
    # Add the last batch if it's not empty
    if current_batch:
        batches.append(current_batch)
    
    return batches

def create_vector_db(documents: List[Document]) -> FAISS:
    """
    Create a FAISS vector database from documents.
    
    Args:
        documents: List of Document objects
        
    Returns:
        FAISS vector database
    """
    db = FAISS.from_documents(documents, embeddings_model)
    return db

def save_vector_db(db: FAISS) -> None:
    """
    Save the vector database to disk.
    
    Args:
        db: FAISS vector database
    """
    os.makedirs(FAISS_INDEX_PATH, exist_ok=True)
    db.save_local(FAISS_INDEX_PATH)
    logger.info(f"Banco de dados de vetores salvo em {FAISS_INDEX_PATH}")

def load_vector_db() -> Optional[FAISS]:
    """
    Load the vector database from disk.
    
    Returns:
        FAISS vector database or None if not found
    """
    global vector_db
    
    if not os.path.exists(FAISS_INDEX_PATH):
        logger.info(f"Diretório {FAISS_INDEX_PATH} não encontrado. Criando...")
        os.makedirs(FAISS_INDEX_PATH, exist_ok=True)
        return None
    
    try:
        # Carregar o banco de dados de vetores sem patch
        db = FAISS.load_local(FAISS_INDEX_PATH, embeddings_model)
        logger.info(f"Banco de dados de vetores carregado de {FAISS_INDEX_PATH}")
        return db
    except Exception as e:
        logger.error(f"Erro ao carregar banco de dados de vetores: {str(e)}")
        return None

async def query_vector_db(question: str, top_k: int = 5, file_paths: List[str] = []) -> List[Document]:
    """
    Query the vector database for relevant documents.
    
    Args:
        question: Query string
        top_k: Number of documents to return
        file_paths: List of file paths to filter by
        
    Returns:
        List of relevant Document objects
    
    Raises:
        ValueError: If the vector database is not loaded
    """
    global vector_db
    
    if vector_db is None:
        vector_db = load_vector_db()
        if vector_db is None:
            raise ValueError("Banco de dados de vetores não carregado. Adicione documentos primeiro.")
    
    # Consulta simples se não houver filtro de arquivos
    if not file_paths:
        docs = vector_db.similarity_search(question, k=top_k)
        return docs
    
    # Consulta com filtro de arquivos
    filter_function = lambda doc: any(doc.metadata.get("source", "").startswith(file_path) for file_path in file_paths)
    
    # Executar a consulta com filtro
    # Aumentamos o k para garantir que tenhamos documentos suficientes após o filtro
    search_k = top_k * 4  # Buscar mais documentos para ter margem após o filtro
    docs = vector_db.similarity_search(question, k=search_k)
    
    # Aplicar o filtro
    filtered_docs = [doc for doc in docs if filter_function(doc)]
    
    # Limitar ao número solicitado
    return filtered_docs[:top_k]

def add_documents_to_vector_db(documents: List[Document]) -> None:
    """
    Add documents to the vector database.
    
    Args:
        documents: List of Document objects
    """
    global vector_db
    
    try:
        if vector_db is None:
            vector_db = load_vector_db()
        
        # Calcular o total de tokens em todos os documentos
        total_tokens = sum(count_tokens(doc.page_content) for doc in documents)
        logger.info(f"Total de tokens em todos os documentos: {total_tokens}")
        
        # Verificar se precisamos dividir em lotes
        MAX_TOKENS_PER_BATCH = 250000  # Limite seguro abaixo do máximo de 300.000
        
        if total_tokens > MAX_TOKENS_PER_BATCH:
            # Dividir documentos em lotes baseados em tokens
            batches = batch_documents_by_tokens(documents, MAX_TOKENS_PER_BATCH)
            logger.info(f"Documentos divididos em {len(batches)} lotes devido ao tamanho")
            
            # Processar cada lote separadamente
            for i, batch in enumerate(batches):
                batch_tokens = sum(count_tokens(doc.page_content) for doc in batch)
                logger.info(f"Processando lote {i+1}/{len(batches)} com {len(batch)} documentos ({batch_tokens} tokens)")
                
                if vector_db is None:
                    # Criar novo banco de dados com o primeiro lote
                    vector_db = create_vector_db(batch)
                    logger.info(f"Novo banco de dados de vetores criado com {len(batch)} documentos")
                else:
                    # Adicionar lote ao banco existente
                    vector_db.add_documents(batch)
                    logger.info(f"{len(batch)} documentos adicionados ao banco de dados de vetores existente")
                
                # Salvar após cada lote para garantir que não perdemos progresso
                save_vector_db(vector_db)
        else:
            # Processar todos os documentos de uma vez se estiver dentro do limite
            if vector_db is None:
                # Criar novo banco de dados se não existir
                vector_db = create_vector_db(documents)
                logger.info(f"Novo banco de dados de vetores criado com {len(documents)} documentos")
            else:
                # Adicionar documentos ao banco existente
                vector_db.add_documents(documents)
                logger.info(f"{len(documents)} documentos adicionados ao banco de dados de vetores existente")
            
            # Salvar o banco de dados atualizado
            save_vector_db(vector_db)
        
    except Exception as e:
        logger.error(f"Erro ao adicionar documentos ao banco de dados de vetores: {str(e)}")
        raise

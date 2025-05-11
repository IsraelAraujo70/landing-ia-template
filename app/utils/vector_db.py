"""
Utilitários de banco de dados vetorial para a aplicação do Assistente AgiFinance.
"""
import os
import numpy as np
import tiktoken
from typing import List, Optional, Any
from langchain.docstore.document import Document
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from app.config.settings import OPENAI_API_KEY, FAISS_INDEX_PATH, EMBEDDINGS_MODEL, logger

embeddings_model = OpenAIEmbeddings(
    model=EMBEDDINGS_MODEL,
    openai_api_key=OPENAI_API_KEY
)

tokenizer = tiktoken.get_encoding("cl100k_base")

vector_db = None

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

def batch_documents_by_tokens(documents: List[Document], max_tokens_per_batch: int = 250000) -> List[List[Document]]:
    """
    Divide documentos em lotes com base na contagem de tokens.
    
    Args:
        documents: Lista de objetos Document
        max_tokens_per_batch: Máximo de tokens por lote
        
    Retorna:
        Lista de lotes de documentos
    """
    batches = []
    current_batch = []
    current_batch_tokens = 0
    
    for doc in documents:
        doc_tokens = count_tokens(doc.page_content)
        
        if doc_tokens > max_tokens_per_batch:
            if current_batch:
                batches.append(current_batch)
                current_batch = []
                current_batch_tokens = 0
            
            logger.warning(f"Documento muito grande ({doc_tokens} tokens). Dividindo em chunks menores.")
            text = doc.page_content
            chunks = []
            start = 0
            
            while start < len(text):
                end = start + 1000
                if end > len(text):
                    end = len(text)
                
                chunk = text[start:end]
                chunk_tokens = count_tokens(chunk)
                
                while chunk_tokens > max_tokens_per_batch and end > start + 100:
                    end = start + int((end - start) * 0.8)  # Reduz por 20%
                    chunk = text[start:end]
                    chunk_tokens = count_tokens(chunk)
                
                chunk_doc = Document(
                    page_content=chunk,
                    metadata=doc.metadata.copy()
                )
                chunks.append(chunk_doc)
                
                start = end
            
            for chunk_doc in chunks:
                batches.append([chunk_doc])
        
        elif current_batch_tokens + doc_tokens > max_tokens_per_batch:
            batches.append(current_batch)
            current_batch = [doc]
            current_batch_tokens = doc_tokens
        
        else:
            current_batch.append(doc)
            current_batch_tokens += doc_tokens
    
    if current_batch:
        batches.append(current_batch)
    
    return batches

def create_vector_db(documents: List[Document]) -> FAISS:
    """
    Cria um banco de dados vetorial FAISS a partir de documentos.
    
    Args:
        documents: Lista de objetos Document
        
    Retorna:
        Banco de dados vetorial FAISS
    """
    db = FAISS.from_documents(documents, embeddings_model)
    return db

def save_vector_db(db: FAISS) -> None:
    """
    Salva o banco de dados vetorial no disco.
    
    Args:
        db: Banco de dados vetorial FAISS
    """
    os.makedirs(FAISS_INDEX_PATH, exist_ok=True)
    db.save_local(FAISS_INDEX_PATH)
    logger.info(f"Banco de dados de vetores salvo em {FAISS_INDEX_PATH}")

def load_vector_db() -> Optional[FAISS]:
    """
    Carrega o banco de dados vetorial do disco.
    
    Retorna:
        Banco de dados vetorial FAISS ou None se não for encontrado
    """
    global vector_db
    
    if not os.path.exists(FAISS_INDEX_PATH):
        logger.info(f"Diretório {FAISS_INDEX_PATH} não encontrado. Criando...")
        os.makedirs(FAISS_INDEX_PATH, exist_ok=True)
        return None
    
    try:
        db = FAISS.load_local(FAISS_INDEX_PATH, embeddings_model)
        logger.info(f"Banco de dados de vetores carregado de {FAISS_INDEX_PATH}")
        return db
    except Exception as e:
        logger.error(f"Erro ao carregar banco de dados de vetores: {str(e)}")
        return None

async def query_vector_db(question: str, top_k: int = 5, file_paths: List[str] = []) -> List[Document]:
    """
    Consulta o banco de dados vetorial para documentos relevantes.
    
    Args:
        question: String de consulta
        top_k: Número de documentos a retornar
        file_paths: Lista de caminhos de arquivo para filtrar
        
    Retorna:
        Lista de objetos Document relevantes
    
    Levanta:
        ValueError: Se o banco de dados vetorial não estiver carregado
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
    
    filter_function = lambda doc: any(doc.metadata.get("source", "").startswith(file_path) for file_path in file_paths)
    
    search_k = top_k * 4  # Buscar mais documentos para ter margem após o filtro
    docs = vector_db.similarity_search(question, k=search_k)
    
    filtered_docs = [doc for doc in docs if filter_function(doc)]
    
    return filtered_docs[:top_k]

def add_documents_to_vector_db(documents: List[Document]) -> None:
    """
    Adiciona documentos ao banco de dados vetorial.
    
    Args:
        documents: Lista de objetos Document
    """
    global vector_db
    
    try:
        if vector_db is None:
            vector_db = load_vector_db()
        
        total_tokens = sum(count_tokens(doc.page_content) for doc in documents)
        logger.info(f"Total de tokens em todos os documentos: {total_tokens}")
        
        MAX_TOKENS_PER_BATCH = 250000  # Limite seguro abaixo do máximo de 300.000
        
        if total_tokens > MAX_TOKENS_PER_BATCH:
            batches = batch_documents_by_tokens(documents, MAX_TOKENS_PER_BATCH)
            logger.info(f"Documentos divididos em {len(batches)} lotes devido ao tamanho")
            
            for i, batch in enumerate(batches):
                batch_tokens = sum(count_tokens(doc.page_content) for doc in batch)
                logger.info(f"Processando lote {i+1}/{len(batches)} com {len(batch)} documentos ({batch_tokens} tokens)")
                
                if vector_db is None:
                    vector_db = create_vector_db(batch)
                    logger.info(f"Novo banco de dados de vetores criado com {len(batch)} documentos")
                else:
                    vector_db.add_documents(batch)
                    logger.info(f"{len(batch)} documentos adicionados ao banco de dados de vetores existente")
                
                save_vector_db(vector_db)
        else:
            if vector_db is None:
                vector_db = create_vector_db(documents)
                logger.info(f"Novo banco de dados de vetores criado com {len(documents)} documentos")
            else:
                vector_db.add_documents(documents)
                logger.info(f"{len(documents)} documentos adicionados ao banco de dados de vetores existente")
            
            save_vector_db(vector_db)
        
    except Exception as e:
        logger.error(f"Erro ao adicionar documentos ao banco de dados de vetores: {str(e)}")
        raise

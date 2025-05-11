"""
Utilitários de processamento de texto para a aplicação do Assistente AgiFinance.
"""
import pdfplumber
import tiktoken
from typing import List
import os
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
from app.config.settings import logger

# Inicializa o tokenizador para divisão de texto
tokenizer = tiktoken.get_encoding("cl100k_base")

def extract_text(file_path: str) -> str:
    """
    Extrai texto de um arquivo com base em sua extensão.
    
    Args:
        file_path: Caminho para o arquivo
        
    Retorna:
        Conteúdo de texto extraído
    
    Levanta:
        ValueError: Se o formato do arquivo não for suportado
    """
    file_extension = os.path.splitext(file_path)[1].lower()
    
    if file_extension == '.pdf':
        with pdfplumber.open(file_path) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() or ""
            return text
    elif file_extension == '.txt':
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    elif file_extension == '.md':
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    else:
        raise ValueError(f"Formato de arquivo não suportado: {file_extension}")

def split_text(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[Document]:
    """
    Divide o texto em pedaços (chunks) com uma contagem máxima de tokens.
    
    Args:
        text: Texto a ser dividido
        chunk_size: Número máximo de tokens por pedaço
        chunk_overlap: Número de tokens sobrepostos entre pedaços
        
    Retorna:
        Lista de objetos Document
    """
    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    chunks = text_splitter.create_documents([text])
    return chunks

"""
Serviço de processamento de documentos.
"""
import os
import datetime
from typing import List
from langchain.docstore.document import Document
from app.utils.text_processing import extract_text, split_text
from app.utils.vector_db import add_documents_to_vector_db
from app.config.settings import UPLOADS_DIR, logger

async def process_document(file_path: str, file_name: str, upload_time: str) -> List[Document]:
    """
    Processa um documento e o divide em pedaços (chunks).
    
    Args:
        file_path: Caminho para o documento
        file_name: Nome do documento
        upload_time: Timestamp de upload
        
    Retorna:
        Lista de objetos Document
    """
    try:
        # Extrair texto do documento
        text = extract_text(file_path)
        
        # Dividir o texto em chunks
        chunks = split_text(text)
        
        # Adicionar metadados aos chunks
        for chunk in chunks:
            chunk.metadata["source"] = file_path
            chunk.metadata["filename"] = file_name
            chunk.metadata["upload_time"] = upload_time
        
        logger.info(f"Documento processado: {file_name} - {len(chunks)} chunks criados")
        return chunks
        
    except Exception as e:
        logger.error(f"Erro ao processar documento {file_name}: {str(e)}")
        raise ValueError(f"Erro ao processar documento: {str(e)}")

async def upload_and_process_document(file_content: bytes, file_name: str) -> str:
    """
    Salva um arquivo enviado e o processa.
    
    Args:
        file_content: Bytes do conteúdo do arquivo
        file_name: Nome do arquivo
        
    Retorna:
        Caminho para o arquivo salvo
    """
    # Criar diretório de uploads se não existir
    os.makedirs(UPLOADS_DIR, exist_ok=True)
    
    # Gerar timestamp para o upload
    upload_time = datetime.datetime.now().isoformat()
    
    # Criar caminho para o arquivo
    file_path = os.path.join(UPLOADS_DIR, file_name)
    
    # Salvar o arquivo
    with open(file_path, "wb") as f:
        f.write(file_content)
    
    logger.info(f"Arquivo salvo: {file_path}")
    
    # Processar o documento
    chunks = await process_document(file_path, file_name, upload_time)
    
    # Adicionar chunks ao banco de dados de vetores
    add_documents_to_vector_db(chunks)
    
    return file_path

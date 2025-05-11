"""
Controlador de documentos para manipulação de endpoints relacionados a documentos.
"""
import os
import datetime
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.models.schemas import DocumentInfo
from app.services.document_service import upload_and_process_document
from app.config.settings import UPLOADS_DIR, logger

# Cria o router
router = APIRouter(prefix="/documents", tags=["documents"])

@router.post("/upload", response_model=DocumentInfo)
async def upload_document(file: UploadFile = File(...)) -> DocumentInfo:
    """
    Faz upload de um documento e o adiciona ao banco de dados vetorial.
    
    Args:
        file: Arquivo enviado
        
    Retorna:
        Informações do documento
    """
    try:
        # Verificar se o arquivo foi enviado
        if not file:
            raise HTTPException(status_code=400, detail="Nenhum arquivo enviado")
        
        # Ler o conteúdo do arquivo
        file_content = await file.read()
        
        # Verificar se o arquivo está vazio
        if len(file_content) == 0:
            raise HTTPException(status_code=400, detail="Arquivo vazio")
        
        # Upload e processamento do documento
        file_path = await upload_and_process_document(file_content, file.filename)
        
        # Obter informações do arquivo
        file_size = os.path.getsize(file_path)
        file_type = os.path.splitext(file.filename)[1].lower()
        upload_time = datetime.datetime.now().isoformat()
        
        # Criar resposta
        document_info = DocumentInfo(
            filename=file.filename,
            upload_time=upload_time,
            file_path=file_path,
            size=file_size,
            type=file_type
        )
        
        logger.info(f"Documento carregado com sucesso: {file.filename}")
        return document_info
        
    except Exception as e:
        logger.error(f"Erro ao fazer upload do documento: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao processar o documento: {str(e)}")

@router.get("/list", response_model=List[DocumentInfo])
async def list_documents() -> List[DocumentInfo]:
    """
    Lista todos os documentos enviados.
    
    Retorna:
        Lista de informações dos documentos
    """
    try:
        # Verificar se o diretório de uploads existe
        if not os.path.exists(UPLOADS_DIR):
            os.makedirs(UPLOADS_DIR, exist_ok=True)
            return []
        
        documents = []
        
        # Listar arquivos no diretório de uploads
        for filename in os.listdir(UPLOADS_DIR):
            file_path = os.path.join(UPLOADS_DIR, filename)
            
            # Verificar se é um arquivo
            if os.path.isfile(file_path):
                # Obter informações do arquivo
                file_size = os.path.getsize(file_path)
                file_type = os.path.splitext(filename)[1].lower()
                
                # Obter data de modificação como timestamp de upload
                mod_time = os.path.getmtime(file_path)
                upload_time = datetime.datetime.fromtimestamp(mod_time).isoformat()
                
                # Criar objeto de documento
                document = DocumentInfo(
                    filename=filename,
                    upload_time=upload_time,
                    file_path=file_path,
                    size=file_size,
                    type=file_type
                )
                
                documents.append(document)
        
        # Ordenar documentos por data de upload (mais recentes primeiro)
        documents.sort(key=lambda x: x.upload_time, reverse=True)
        
        return documents
        
    except Exception as e:
        logger.error(f"Erro ao listar documentos: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao listar documentos: {str(e)}")

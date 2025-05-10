import os
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Importar depois de configurar o mock para OPENAI_API_KEY
with patch.dict(os.environ, {"OPENAI_API_KEY": "fake-api-key"}):
    from app import app

client = TestClient(app)

def test_root_endpoint():
    """Testa se o endpoint raiz está funcionando corretamente."""
    response = client.get("/")
    assert response.status_code == 200
    assert "status" in response.json()
    assert response.json()["status"] == "online"

def test_list_documents_empty():
    """Testa se o endpoint de listagem de documentos funciona quando não há documentos."""
    with patch("os.path.exists", return_value=False):
        response = client.get("/documents")
        assert response.status_code == 200
        assert response.json() == []

def test_list_documents():
    """Testa se o endpoint de listagem de documentos funciona quando há documentos."""
    with patch("os.path.exists", return_value=True), \
         patch("os.listdir", return_value=["12345_test.pdf"]), \
         patch("os.path.isfile", return_value=True), \
         patch("os.stat") as mock_stat:
        
        # Configurar o mock para os.stat
        mock_stat_result = MagicMock()
        mock_stat_result.st_size = 1024
        mock_stat.return_value = mock_stat_result
        
        response = client.get("/documents")
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["filename"] == "test.pdf"

@pytest.mark.asyncio
async def test_ask_question():
    """Testa se o endpoint de perguntas funciona corretamente."""
    # Mock para o banco de dados de vetores
    with patch("app.vector_db") as mock_db, \
         patch("app.query_vector_db") as mock_query, \
         patch("app.generate_answer") as mock_generate:
        
        # Configurar os mocks
        mock_db.return_value = True
        mock_doc = MagicMock()
        mock_doc.page_content = "Conteúdo de teste"
        mock_doc.metadata = {"source": "test.pdf"}
        mock_query.return_value = [mock_doc]
        mock_generate.return_value = "Resposta de teste"
        
        # Fazer a requisição
        response = client.post(
            "/perguntar",
            json={"question": "Pergunta de teste?", "session_id": "test-session"}
        )
        
        assert response.status_code == 200
        assert response.json()["answer"] == "Resposta de teste"
        assert len(response.json()["sources"]) == 1

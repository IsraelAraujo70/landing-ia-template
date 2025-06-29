"""
Configurações para a aplicação do Assistente AgiFinance.
"""
import os
import logging
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# Chaves de API
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY or OPENAI_API_KEY == "your-openai-api-key-here":
    raise ValueError("OPENAI_API_KEY não está definido ou está usando valor placeholder. Configure com sua chave real da OpenAI.")

# Caminhos
UPLOADS_DIR = "uploads"
FAISS_INDEX_PATH = os.path.abspath("faiss_index")

# Configurações do modelo
EMBEDDINGS_MODEL = "text-embedding-3-small"
CHAT_MODEL = "gpt-4o"
TEMPERATURE = 0.7

# Configuração de logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("app.log")
    ]
)
logger = logging.getLogger("agifinance-assistente")

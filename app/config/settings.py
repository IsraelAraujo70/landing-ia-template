"""
Configuration settings for the Ada Assistant application.
"""
import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY não está definido no arquivo .env")

# Paths
UPLOADS_DIR = "uploads"
FAISS_INDEX_PATH = os.path.abspath("faiss_index")

# Model settings
EMBEDDINGS_MODEL = "text-embedding-3-small"
CHAT_MODEL = "gpt-4o"
TEMPERATURE = 0.7

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("app.log")
    ]
)
logger = logging.getLogger("ada-assistente")

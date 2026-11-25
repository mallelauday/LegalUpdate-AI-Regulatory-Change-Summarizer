import os
from pathlib import Path
from dotenv import load_dotenv

base_dir = Path(__file__).resolve().parent
load_dotenv(base_dir / ".env")

class Config:
    PORT = int(os.getenv("PORT", 5000))
    DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "t")
    SECRET_KEY = os.getenv("SECRET_KEY", "legalupdate-ai-secret-key-2026")
    JWT_SECRET = os.getenv("JWT_SECRET", "legalupdate-jwt-secret-2026")
    
    # Firebase Configuration
    _raw_key = os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY", "")
    FIREBASE_SERVICE_ACCOUNT_KEY = str(base_dir / _raw_key) if _raw_key and not os.path.isabs(_raw_key) else _raw_key
    FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID", "legalupdate-ai")
    
    # Groq LLM
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    
    # Firecrawl
    FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY", "")
    FIRECRAWL_API_URL = os.getenv("FIRECRAWL_API_URL", "https://api.firecrawl.dev/v1")
    FIRECRAWL_WEBHOOK_SECRET = os.getenv("FIRECRAWL_WEBHOOK_SECRET", "legalupdate-firecrawl-webhook-secret-2026")
    
    # Memento Memory
    MEMENTO_API_KEY = os.getenv("MEMENTO_API_KEY", "")
    MEMENTO_STORAGE_PATH = os.getenv("MEMENTO_STORAGE_PATH", str(base_dir / "data" / "memento_store"))
    MEMENTO_MCP_URL = os.getenv("MEMENTO_MCP_URL", "https://api.mementoagi.com/mcp")
    
    # Worker Configuration
    WORKER_POLL_INTERVAL = int(os.getenv("WORKER_POLL_INTERVAL", 10))

    @classmethod
    def is_groq_configured(cls):
        return bool(cls.GROQ_API_KEY and not cls.GROQ_API_KEY.startswith("your_"))
        
    @classmethod
    def is_firecrawl_configured(cls):
        return bool(cls.FIRECRAWL_API_KEY and not cls.FIRECRAWL_API_KEY.startswith("your_"))

    @classmethod
    def is_memento_configured(cls):
        return bool(cls.MEMENTO_API_KEY and not cls.MEMENTO_API_KEY.startswith("your_"))

    @classmethod
    def is_firebase_configured(cls):
        if cls.FIREBASE_SERVICE_ACCOUNT_KEY and os.path.exists(cls.FIREBASE_SERVICE_ACCOUNT_KEY):
            return True
        return False

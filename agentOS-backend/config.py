from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    GEMINI_API_KEY: str = ""  # Optional - Quatarly is primary now
    GEMINI_MODEL: str = "gemini-2.0-flash"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5:3b"
    TAVILY_API_KEY: str = ""  # Optional - can work without web search
    CHROMA_PERSIST_DIR: str = "./chroma_db"
    SQLITE_URL: str = "sqlite+aiosqlite:///./agentOS.db"
    CORS_ORIGINS: List[str] = ["http://localhost:5173"]
    
    # Quatarly API — unified Claude/GPT/Gemini gateway (PRIMARY)
    QUATARLY_API_KEY: str
    QUATARLY_BASE_URL: str = "https://api.quatarly.cloud/v1"
    QUATARLY_PRIMARY_MODEL: str = "claude-opus-4-6-thinking"
    QUATARLY_FALLBACK_1: str = "claude-sonnet-4-6-thinking"
    QUATARLY_FALLBACK_2: str = "gpt-5.1"

    class Config:
        env_file = ".env"


settings = Settings()

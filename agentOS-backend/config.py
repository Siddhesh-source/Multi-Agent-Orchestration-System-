from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemini-2.0-flash"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5:3b"
    TAVILY_API_KEY: str
    CHROMA_PERSIST_DIR: str = "./chroma_db"
    SQLITE_URL: str = "sqlite+aiosqlite:///./agentOS.db"
    CORS_ORIGINS: List[str] = ["http://localhost:5173"]

    class Config:
        env_file = ".env"


settings = Settings()

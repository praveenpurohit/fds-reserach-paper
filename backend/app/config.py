from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://research:research123@localhost:5433/research_db"

    # Auth
    SECRET_KEY: str = "your-secret-key-change-in-production-abc123"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # LLM
    OLLAMA_MODEL: str = "qwen2.5:3b"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    ANTHROPIC_API_KEY: str = ""
    CLAUDE_MODEL: str = "claude-sonnet-4-20250514"

    # Embeddings
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    # External APIs
    SEMANTIC_SCHOLAR_API_KEY: str = ""
    OPENALEX_EMAIL: str = ""

    # App
    APP_TITLE: str = "ResearchIQ"
    TOP_K_RESULTS: int = 10

    class Config:
        env_file = ".env"
        extra = "allow"


@lru_cache
def get_settings() -> Settings:
    return Settings()

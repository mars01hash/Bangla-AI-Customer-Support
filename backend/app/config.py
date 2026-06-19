import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Security
    JWT_SECRET: str = "supersecretjwtsecretkeychangeinproduction123456789"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    ADMIN_INITIAL_PASSWORD: str = "adminpassword123"

    # Database
    DATABASE_URL: str = "sqlite:///./support_platform.db"

    # Vector Database (ChromaDB)
    CHROMA_PERSIST_DIRECTORY: str = "./chroma_db"

    # LLM Agent
    LLM_PROVIDER: str = "mock"  # "mock", "openai", "groq", "huggingface"
    LLM_API_KEY: str = "mock-key"
    LLM_MODEL_NAME: str = "qwen-3-7b-chat"

    # Embedding
    EMBEDDING_MODEL_NAME: str = "sentence-transformers/LaBSE"

    # Telegram Bot
    TELEGRAM_BOT_TOKEN: str = ""  # Set in .env: TELEGRAM_BOT_TOKEN=123456:ABC-...

    # API Config
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

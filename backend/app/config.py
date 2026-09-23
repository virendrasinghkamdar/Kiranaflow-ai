"""KiranaFlow AI - Application Configuration"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # AI Provider
    ai_provider: str = "mock"
    gemini_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3"

    # Database
    database_url: str = "sqlite:///./kiranaflow.db"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    # Store
    store_name: str = "KiranaFlow Store"
    default_delivery_fee: float = 30.0
    currency_symbol: str = "₹"

    class Config:
        env_file = ("../.env", ".env")
        env_file_encoding = "utf-8"


settings = Settings()

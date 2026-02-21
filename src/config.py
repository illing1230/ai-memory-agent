"""설정 관리 모듈"""

import os
from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """애플리케이션 설정"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database
    sqlite_db_path: str = "./data/sqlite/memory.db"

    # Qdrant
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "ai-memory-agent"
    qdrant_api_key: str | None = None

    # Embedding Provider
    embedding_provider: Literal["openai", "ollama", "huggingface"] = "huggingface"
    embedding_dimension: int = 1024

    # HuggingFace Embedding
    huggingface_api_key: str | None = None
    huggingface_embedding_model_url: str | None = None

    # OpenAI Embedding
    openai_api_key: str | None = None
    openai_embedding_model: str = "text-embedding-3-small"
    openai_embedding_url: str = "https://api.openai.com/v1/embeddings"

    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_embedding_model: str = "nomic-embed-text"
    ollama_llm_model: str = "llama3.2"

    # LLM Provider
    llm_provider: Literal["openai", "ollama", "anthropic"] = "openai"

    # OpenAI LLM (OpenAI 호환 API 포함)
    openai_llm_url: str = "https://api.openai.com/v1"
    openai_llm_model: str = "gpt-4o-mini"

    # Anthropic
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-sonnet-4-20250514"

    # Application
    app_env: Literal["development", "production", "test"] = "development"
    debug: bool = True
    log_level: str = "INFO"
    
    # Test User Password (개발 환경용)
    test_user_password: str = "test123"

    # JWT Authentication
    jwt_secret_key: str = "change-this-secret-key-in-production"
    jwt_access_token_expire_hours: int = 24

    # Reranker
    reranker_url: str | None = None
    reranker_model: str = "jinaai/jina-reranker-v2-base-multilingual"

    # Memory Extraction
    auto_extract_memory: bool = True
    min_message_length_for_extraction: int = 10
    duplicate_threshold: float = 0.85

    # Mchat (Mattermost) Integration
    mchat_url: str = "https://mchat.samsung.com"
    mchat_token: str | None = None
    mchat_enabled: bool = False

    # Proxy 설정 (내부망 직접 접속용)
    no_proxy: str = "10.244.*,localhost,127.0.0.1"

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"
    
    def apply_proxy_settings(self) -> None:
        """NO_PROXY 환경 변수 적용 (내부망 직접 접속)"""
        if self.no_proxy:
            os.environ["NO_PROXY"] = self.no_proxy
            os.environ["no_proxy"] = self.no_proxy


@lru_cache
def get_settings() -> Settings:
    """설정 싱글톤 반환"""
    settings = Settings()
    settings.apply_proxy_settings()  # 설정 로드 시 프록시 설정 적용
    return settings

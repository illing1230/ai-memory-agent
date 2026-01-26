"""Provider Factory"""

from functools import lru_cache

from src.config import get_settings
from src.shared.providers.base import BaseEmbeddingProvider, BaseLLMProvider


@lru_cache
def get_embedding_provider() -> BaseEmbeddingProvider:
    """Embedding Provider 생성"""
    settings = get_settings()
    provider = settings.embedding_provider

    if provider == "openai":
        from src.shared.providers.embedding.openai import OpenAIEmbeddingProvider

        return OpenAIEmbeddingProvider(
            api_key=settings.openai_api_key,
            model=settings.openai_embedding_model,
            base_url=settings.openai_embedding_url,
            dimension=settings.embedding_dimension,
        )

    elif provider == "huggingface":
        from src.shared.providers.embedding.huggingface import HuggingFaceEmbeddingProvider

        return HuggingFaceEmbeddingProvider(
            api_key=settings.huggingface_api_key,
            model_url=settings.huggingface_embedding_model_url,
            dimension=settings.embedding_dimension,
        )

    elif provider == "ollama":
        from src.shared.providers.embedding.ollama import OllamaEmbeddingProvider

        return OllamaEmbeddingProvider(
            base_url=settings.ollama_base_url,
            model=settings.ollama_embedding_model,
            dimension=settings.embedding_dimension,
        )

    else:
        raise ValueError(f"Unknown embedding provider: {provider}")


@lru_cache
def get_llm_provider() -> BaseLLMProvider:
    """LLM Provider 생성"""
    settings = get_settings()
    provider = settings.llm_provider

    if provider == "openai":
        from src.shared.providers.llm.openai import OpenAILLMProvider

        return OpenAILLMProvider(
            api_key=settings.openai_api_key,
            model=settings.openai_llm_model,
            base_url=settings.openai_llm_url,
        )

    elif provider == "ollama":
        from src.shared.providers.llm.ollama import OllamaLLMProvider

        return OllamaLLMProvider(
            base_url=settings.ollama_base_url,
            model=settings.ollama_llm_model,
        )

    elif provider == "anthropic":
        from src.shared.providers.llm.anthropic import AnthropicLLMProvider

        return AnthropicLLMProvider(
            api_key=settings.anthropic_api_key,
            model=settings.anthropic_model,
        )

    else:
        raise ValueError(f"Unknown LLM provider: {provider}")

from knowledge_service.app.llm.base_provider import BaseLLMProvider
from knowledge_service.app.llm.base_provider import BaseLLMProvider
from knowledge_service.app.llm.openrouter_provider import OpenRouterProvider
from knowledge_service.app.llm.vllm_provider import VLLMProvider


def get_llm_provider(provider: str) -> BaseLLMProvider:
    """
    Factory function to get an LLM provider instance.

    Args:
        provider: Explicit provider name to use (overrides environment variable)

    Returns:
        Configured LLM provider instance

    Raises:
        ValueError: If requested provider is not available
    """
    if not provider:
        raise ValueError("provider is required")

    provider_name = provider

    if provider_name == "openrouter":
        return OpenRouterProvider(api_key=config.OPENROUTER_API_KEY,model=config.OPENROUTER_MODEL)
    elif provider_name == "vllm":
        return VLLMProvider()
    else:
        raise ValueError(f"Unsupported LLM provider: {provider_name}")


__all__ = ['get_llm_provider']

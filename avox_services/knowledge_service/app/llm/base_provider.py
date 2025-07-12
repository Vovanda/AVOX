
from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def generate(self, prompt: str, **kwargs: Any) -> str:
        """
        Generate text completion from prompt.

        Args:
            prompt: Input text prompt
            **kwargs: Additional provider-specific parameters

        Returns:
            Generated text completion
        """
        pass

    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current model configuration.

        Returns:
            Dictionary containing model metadata (name, parameters, etc.)
        """
        pass

    @abstractmethod
    def validate_credentials(self) -> bool:
        """
        Validate provider credentials and connection.

        Returns:
            True if credentials are valid, False otherwise
        """
        pass

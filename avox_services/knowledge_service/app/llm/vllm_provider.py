from typing import Dict, Any

from knowledge_service.app.llm.base_provider import BaseLLMProvider


class VLLMProvider(BaseLLMProvider):
    """Stub implementation for vLLM provider."""

    def __init__(self, model_path: str = "local/t5-model"):
        """
        Initialize vLLM provider stub.

        Args:
            model_path: Path to local model (default placeholder)
        """
        self.model_path = model_path

    def generate(self, prompt: str, **kwargs: Any) -> str:
        """
        Stub implementation for text generation.

        Args:
            prompt: Input text prompt
            **kwargs: Additional parameters (ignored in stub)

        Returns:
            Mock response with echo of input
        """
        return f"[vLLM STUB] Response to: {prompt}"

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get stub model information.

        Returns:
            Dictionary with placeholder model metadata
        """
        return {
            "provider": "vLLM",
            "model_path": self.model_path,
            "status": "stub_implementation"
        }

    def validate_credentials(self) -> bool:
        """
        Stub credential validation.

        Returns:
            Always True for stub implementation
        """
        return True

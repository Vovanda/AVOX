from typing import Dict, Any

from openai import OpenAI

from knowledge_service.app.llm.base_provider import BaseLLMProvider


class OpenRouterProvider(BaseLLMProvider):
    """OpenRouter implementation using the official OpenAI-compatible client."""

    def __init__(self, api_key: str, model: str):
        if not api_key:
            raise ValueError("api_key is required")

        if not model:
            raise ValueError("model is required")

        self.api_key = api_key
        self.model = model

        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.api_key,
        )

        # self.extra_headers = {
        #    "HTTP-Referer": config.OPENROUTER_SITE_URL,
        #    "X-Title": config.OPENROUTER_SITE_NAME,
        #}

    def generate(self, prompt: str, **kwargs: Any) -> str:
        """
        Generate text completion using OpenRouter via the OpenAI-compatible client.

        Args:
            prompt: Input prompt text
            **kwargs: Additional parameters (e.g., temperature, top_p, etc.)

        Returns:
            LLM-generated response as string
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                extra_headers=self.extra_headers,
                **kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"OpenRouter completion failed: {str(e)}") from e

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "provider": "OpenRouter",
            "model": self.model,
            "base_url": "https://openrouter.ai/api/v1"
        }

    def validate_credentials(self) -> bool:
        """
        Dummy validation, since OpenRouter does not expose a validation endpoint directly.
        You can implement real validation by attempting a minimal call.
        """
        try:
            self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=1,
                extra_headers=self.extra_headers
            )
            return True
        except Exception:
            return False

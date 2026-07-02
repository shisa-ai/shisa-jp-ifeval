from typing import Any, Optional
import os

from loguru import logger
from openai import OpenAI

from .base import LLMCaller, LLMResponse


class LiteLLMCaller:
    """Implementation of LLMCaller using direct OpenAI-compatible clients.

    Despite the name, this no longer depends on litellm; it is kept for
    backwards compatibility with existing scripts.
    """

    def __init__(self, model: str, api_base: str, api_key: Optional[str] = None):
        """Initialize the caller.

        Args:
            model: Name of the model to use.
            api_base: Base URL for the API (OpenAI-compatible endpoint).
            api_key: API key for authentication (optional).
        """

        self.model = model
        self.api_base = api_base
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")

    def call(
        self,
        prompt: str,
        temperature: float = 0.0,
        max_tokens: int = 512,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Make a call to the language model.

        Args:
            prompt: The prompt to send to the model.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.
            system_prompt: Optional system prompt to prepend.
            **kwargs: Additional parameters (unused for now).

        Returns:
            Standardized LLMResponse.
        """
        try:
            client_kwargs = {}
            if self.api_key:
                client_kwargs["api_key"] = self.api_key
            if self.api_base:
                client_kwargs["base_url"] = self.api_base

            client = OpenAI(**client_kwargs)

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            choice = response.choices[0] if response.choices else None
            message = getattr(choice, "message", None) if choice is not None else None
            content = getattr(message, "content", None) if message is not None else None

            if content is None:
                content = ""

            return LLMResponse(
                output=str(content),
                generated_tokens=getattr(getattr(response, "usage", None), "completion_tokens", 0),
                status="success",
                error=None,
            )

        except Exception as e:
            logger.error(f"Error in OpenAI-compatible call: {e}")
            return LLMResponse(
                output=None,
                generated_tokens=0,
                status="error",
                error=str(e),
            )

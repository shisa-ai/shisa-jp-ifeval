from typing import Protocol, Dict, Any, TypedDict, Optional

class LLMResponse(TypedDict):
    """Standardized response format for LLM calls."""
    output: Optional[str]
    generated_tokens: int
    status: str
    error: Optional[str]

class LLMCaller(Protocol):
    """Protocol for making calls to language models.
    
    This protocol defines a standard interface for interacting with different
    LLM backends (OpenAI, vLLM, local models, etc).
    """
    def call(self, 
            prompt: str,
            temperature: float = 0.0,
            max_tokens: int = 3000,
            **kwargs: Any) -> LLMResponse:
        """Make a call to the language model.
        
        Args:
            prompt: The prompt to send to the model
            temperature: Sampling temperature (default: 0.0)
            max_tokens: Maximum tokens to generate (default: 3000)
            **kwargs: Additional model-specific parameters
            
        Returns:
            LLMResponse containing the model output or error information
        """
        ...

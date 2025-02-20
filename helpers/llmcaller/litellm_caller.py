from typing import Any, Optional
import os

import litellm
from loguru import logger

from .base import LLMCaller, LLMResponse

class LiteLLMCaller:
    """Implementation of LLMCaller using LiteLLM."""
    
    def __init__(self, model: str, api_base: str):
        """Initialize the LiteLLM caller.
        
        Args:
            model: Name of the model to use
            api_base: Base URL for the API
        """

        self.model = model
        #Turn these on to enable debug mode. 
        #os.environ['LITELLM_LOG'] = 'DEBUG'
        #litellm.set_verbose=True

        self.api_base = api_base
        

    def call(self,
             prompt: str,
             temperature: float = 0.0,
             max_tokens: int = 512,
             system_prompt: Optional[str] = None,
             **kwargs: Any) -> LLMResponse:
        """Make a call to the language model using LiteLLM.
        
        Args:
            prompt: The prompt to send to the model
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            system_prompt: Optional system prompt to prepend before the user message
            **kwargs: Additional parameters to pass to litellm.completion
            
        Returns:
            Standardized LLMResponse
        """
        try:            
            # Create messages for API call
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            '''
            if self.model.startswith("bedrock"):
                region = os.getenv('AWS_DEFAULT_REGION', 'us-west-2')
                self.api_base = f"https://bedrock-runtime.{region}.amazonaws.com"
            '''

            if 'gemini' in self.model:
                safety_settings=[
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_NONE",
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_NONE",
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_NONE",
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_NONE",
                },
            ]
                response = litellm.completion(
                    model=self.model,
                    messages=messages,
                    api_base=self.api_base,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    safety_settings=safety_settings,
                    **kwargs
                )
            else: 
                response = litellm.completion(
                    model=self.model,
                    messages=messages,
                    api_base=self.api_base,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs
                )



            return LLMResponse(
                output=response.choices[0].message.content,
                generated_tokens=response.usage.completion_tokens,
                status="success",
                error=None
            )
            
        except Exception as e:
            logger.error(f"Error in LiteLLM call: {e}")
            return LLMResponse(
                output=None,
                generated_tokens=0,
                status="error",
                error=str(e)
            )

"""Claude API client for LLM operations."""

import os
from typing import Optional, Dict, Any
from anthropic import Anthropic, APIError, APIConnectionError as AnthropicConnectionError
from ..utils.logger import get_logger
from .exceptions import APIConnectionError, APIKeyError, APIRateLimitError, APITimeoutError

logger = get_logger(__name__)


class ClaudeClient:
    """
    Client for interacting with Anthropic's Claude API.

    Handles authentication, API calls, and error handling.
    """

    # Pricing for Claude 3.5 Sonnet (as of 2024)
    # Input: $3 per million tokens
    # Output: $15 per million tokens
    PRICING = {
        "claude-3-5-sonnet-20241022": {
            "input": 3.0 / 1_000_000,  # $ per token
            "output": 15.0 / 1_000_000,  # $ per token
        },
        "claude-3-sonnet-20240229": {
            "input": 3.0 / 1_000_000,
            "output": 15.0 / 1_000_000,
        },
    }

    DEFAULT_MODEL = "claude-3-5-sonnet-20241022"
    DEFAULT_MAX_TOKENS = 4096
    DEFAULT_TEMPERATURE = 1.0

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = DEFAULT_TEMPERATURE,
    ):
        """
        Initialize Claude API client.

        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            model: Claude model to use
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0-1)

        Raises:
            APIKeyError: If API key is not provided or found in environment
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise APIKeyError(
                "ANTHROPIC_API_KEY not found. Please set it as an environment variable "
                "or pass it to the constructor."
            )

        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature

        try:
            self.client = Anthropic(api_key=self.api_key)
            logger.info(f"Claude client initialized with model: {self.model}")
        except Exception as e:
            raise APIConnectionError(f"Failed to initialize Anthropic client: {str(e)}")

    def create_message(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Create a message using Claude API.

        Args:
            prompt: User prompt
            system: System prompt (optional)
            max_tokens: Override default max_tokens
            temperature: Override default temperature

        Returns:
            API response dictionary containing:
                - content: Response text
                - usage: Token usage information
                - model: Model used

        Raises:
            APIConnectionError: If connection fails
            APIRateLimitError: If rate limit is exceeded
            APITimeoutError: If request times out
        """
        try:
            params = {
                "model": self.model,
                "max_tokens": max_tokens or self.max_tokens,
                "temperature": temperature if temperature is not None else self.temperature,
                "messages": [{"role": "user", "content": prompt}],
            }

            if system:
                params["system"] = system

            logger.debug(f"Calling Claude API with model={self.model}")
            response = self.client.messages.create(**params)

            # Extract response text
            content_text = ""
            if response.content and len(response.content) > 0:
                content_text = response.content[0].text

            result = {
                "content": content_text,
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
                },
                "model": response.model,
                "id": response.id,
            }

            logger.debug(
                f"API call successful. Tokens: {result['usage']['input_tokens']} in, "
                f"{result['usage']['output_tokens']} out"
            )

            return result

        except AnthropicConnectionError as e:
            logger.error(f"API connection error: {e}")
            raise APIConnectionError(f"Failed to connect to Claude API: {str(e)}")
        except APIError as e:
            if "rate_limit" in str(e).lower():
                logger.error(f"Rate limit exceeded: {e}")
                raise APIRateLimitError(f"Rate limit exceeded: {str(e)}")
            elif "timeout" in str(e).lower():
                logger.error(f"Request timeout: {e}")
                raise APITimeoutError(f"Request timed out: {str(e)}")
            else:
                logger.error(f"API error: {e}")
                raise APIConnectionError(f"API error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error during API call: {e}")
            raise APIConnectionError(f"Unexpected error: {str(e)}")

    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """
        Calculate the cost of API usage.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Cost in USD
        """
        pricing = self.PRICING.get(self.model)
        if not pricing:
            logger.warning(f"No pricing info for model {self.model}, returning 0")
            return 0.0

        input_cost = input_tokens * pricing["input"]
        output_cost = output_tokens * pricing["output"]
        total_cost = input_cost + output_cost

        return total_cost

    def estimate_tokens(self, text: str) -> int:
        """
        Estimate the number of tokens in a text.

        This is a rough estimate based on character count.
        For accurate counts, use the API's token counting.

        Args:
            text: Input text

        Returns:
            Estimated token count
        """
        # Rough estimate: ~4 characters per token for English
        # Adjust for other languages as needed
        return len(text) // 4

    def get_max_context_tokens(self) -> int:
        """
        Get the maximum context window size for the current model.

        Returns:
            Maximum context tokens
        """
        # Claude 3.5 Sonnet has 200k context window
        if "claude-3-5" in self.model or "claude-3" in self.model:
            return 200_000
        return 100_000  # Conservative default

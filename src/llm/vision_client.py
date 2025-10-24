"""Claude Vision API client for analyzing images."""

import os
import base64
from typing import Optional, Dict, Any
from pathlib import Path
from anthropic import Anthropic, APIError, APIConnectionError as AnthropicConnectionError
from ..utils.logger import get_logger
from .exceptions import APIConnectionError, APIKeyError, APIRateLimitError, APITimeoutError

logger = get_logger(__name__)


class VisionClient:
    """
    Client for interacting with Claude Vision API.

    Handles image encoding, API calls, and error handling for image analysis.
    """

    # Pricing for Claude 3.5 Sonnet Vision (as of 2024)
    # Same as text API + additional image tokens
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
    DEFAULT_MAX_TOKENS = 2048
    DEFAULT_TEMPERATURE = 0.0  # Deterministic for analysis

    # Supported image formats
    SUPPORTED_FORMATS = [".png", ".jpg", ".jpeg", ".gif", ".webp"]

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = DEFAULT_TEMPERATURE,
    ):
        """
        Initialize Vision API client.

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
            logger.info(f"Vision client initialized with model: {self.model}")
        except Exception as e:
            raise APIConnectionError(f"Failed to initialize Anthropic client: {str(e)}")

    def encode_image(self, image_path: str) -> Dict[str, str]:
        """
        Encode image to base64 for API.

        Args:
            image_path: Path to image file

        Returns:
            Dictionary with media_type and base64 data

        Raises:
            FileNotFoundError: If image file doesn't exist
            ValueError: If image format is not supported
        """
        image_path_obj = Path(image_path)

        # Check file exists
        if not image_path_obj.exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")

        # Check file format
        if image_path_obj.suffix.lower() not in self.SUPPORTED_FORMATS:
            raise ValueError(
                f"Unsupported image format: {image_path_obj.suffix}. "
                f"Supported formats: {', '.join(self.SUPPORTED_FORMATS)}"
            )

        # Determine media type
        media_type_map = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".webp": "image/webp",
        }
        media_type = media_type_map.get(image_path_obj.suffix.lower(), "image/jpeg")

        # Read and encode image
        try:
            with open(image_path, "rb") as f:
                image_data = base64.standard_b64encode(f.read()).decode("utf-8")

            logger.debug(f"Encoded image: {image_path} ({len(image_data)} bytes base64)")

            return {
                "media_type": media_type,
                "data": image_data,
            }
        except Exception as e:
            raise IOError(f"Failed to read/encode image {image_path}: {str(e)}")

    def analyze_image(
        self,
        image_path: str,
        prompt: str,
        system: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Analyze an image using Claude Vision API.

        Args:
            image_path: Path to image file
            prompt: Analysis prompt
            system: System prompt (optional)
            max_tokens: Override default max_tokens
            temperature: Override default temperature

        Returns:
            API response dictionary containing:
                - content: Response text (JSON)
                - usage: Token usage information
                - model: Model used

        Raises:
            FileNotFoundError: If image file doesn't exist
            ValueError: If image format is not supported
            APIConnectionError: If connection fails
            APIRateLimitError: If rate limit is exceeded
            APITimeoutError: If request times out
        """
        # Encode image
        encoded_image = self.encode_image(image_path)

        try:
            params = {
                "model": self.model,
                "max_tokens": max_tokens or self.max_tokens,
                "temperature": temperature if temperature is not None else self.temperature,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": encoded_image["media_type"],
                                    "data": encoded_image["data"],
                                },
                            },
                            {
                                "type": "text",
                                "text": prompt,
                            },
                        ],
                    }
                ],
            }

            if system:
                params["system"] = system

            logger.debug(f"Calling Vision API for image: {image_path}")
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
                f"Vision API call successful. Tokens: {result['usage']['input_tokens']} in, "
                f"{result['usage']['output_tokens']} out"
            )

            return result

        except AnthropicConnectionError as e:
            logger.error(f"API connection error: {e}")
            raise APIConnectionError(f"Failed to connect to Claude Vision API: {str(e)}")
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
            logger.error(f"Unexpected error during Vision API call: {e}")
            raise APIConnectionError(f"Unexpected error: {str(e)}")

    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """
        Calculate the cost of Vision API usage.

        Args:
            input_tokens: Number of input tokens (including image tokens)
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

    def get_image_info(self, image_path: str) -> Dict[str, Any]:
        """
        Get information about an image file.

        Args:
            image_path: Path to image file

        Returns:
            Dictionary with image info (size, format, etc.)
        """
        image_path_obj = Path(image_path)

        if not image_path_obj.exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")

        return {
            "path": str(image_path_obj.absolute()),
            "name": image_path_obj.name,
            "size_bytes": image_path_obj.stat().st_size,
            "size_kb": image_path_obj.stat().st_size / 1024,
            "format": image_path_obj.suffix.lower(),
        }

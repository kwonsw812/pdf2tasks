"""LLM caller with retry logic and response parsing."""

import json
import re
import time
from typing import List, Dict, Any, Optional
from ...types.models import IdentifiedTask, TokenUsage
from ...utils.logger import get_logger
from ..exceptions import (
    JSONParseError,
    TaskIdentificationError,
    APIRateLimitError,
    APITimeoutError,
)
from ..claude_client import ClaudeClient

logger = get_logger(__name__)


class LLMCaller:
    """
    Handles LLM API calls with retry logic and response parsing.
    """

    DEFAULT_MAX_RETRIES = 3
    DEFAULT_RETRY_DELAY = 2.0  # seconds
    DEFAULT_BACKOFF_MULTIPLIER = 2.0

    def __init__(
        self,
        client: ClaudeClient,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_delay: float = DEFAULT_RETRY_DELAY,
        backoff_multiplier: float = DEFAULT_BACKOFF_MULTIPLIER,
    ):
        """
        Initialize LLMCaller.

        Args:
            client: Claude API client
            max_retries: Maximum number of retry attempts
            retry_delay: Initial delay between retries (seconds)
            backoff_multiplier: Multiplier for exponential backoff
        """
        self.client = client
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.backoff_multiplier = backoff_multiplier
        logger.info(f"LLMCaller initialized with {max_retries} max retries")

    def call_for_task_identification(
        self, system_prompt: str, user_prompt: str
    ) -> tuple[List[IdentifiedTask], TokenUsage]:
        """
        Call LLM for task identification.

        Args:
            system_prompt: System prompt
            user_prompt: User prompt

        Returns:
            Tuple of (tasks, token_usage)

        Raises:
            TaskIdentificationError: If task identification fails after retries
            JSONParseError: If response cannot be parsed
        """
        logger.info("Calling LLM for task identification")

        for attempt in range(1, self.max_retries + 1):
            try:
                logger.debug(f"Attempt {attempt}/{self.max_retries}")

                response = self.client.create_message(
                    prompt=user_prompt, system=system_prompt
                )

                # Parse response
                tasks = self._parse_task_response(response["content"])

                # Create token usage object
                token_usage = TokenUsage(
                    input_tokens=response["usage"]["input_tokens"],
                    output_tokens=response["usage"]["output_tokens"],
                    total_tokens=response["usage"]["total_tokens"],
                )

                logger.info(
                    f"Task identification successful. "
                    f"Identified {len(tasks)} tasks. "
                    f"Tokens: {token_usage.total_tokens}"
                )

                return tasks, token_usage

            except (APIRateLimitError, APITimeoutError) as e:
                if attempt < self.max_retries:
                    delay = self.retry_delay * (self.backoff_multiplier ** (attempt - 1))
                    logger.warning(
                        f"API error on attempt {attempt}: {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    time.sleep(delay)
                else:
                    logger.error(f"API error after {self.max_retries} attempts: {e}")
                    raise TaskIdentificationError(
                        f"Failed after {self.max_retries} attempts: {str(e)}"
                    )

            except JSONParseError as e:
                if attempt < self.max_retries:
                    delay = self.retry_delay
                    logger.warning(
                        f"JSON parsing error on attempt {attempt}: {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    time.sleep(delay)
                else:
                    logger.error(
                        f"JSON parsing failed after {self.max_retries} attempts: {e}"
                    )
                    raise

            except Exception as e:
                logger.error(f"Unexpected error on attempt {attempt}: {e}")
                if attempt < self.max_retries:
                    delay = self.retry_delay
                    logger.warning(f"Retrying in {delay:.1f}s...")
                    time.sleep(delay)
                else:
                    raise TaskIdentificationError(
                        f"Task identification failed: {str(e)}"
                    )

        raise TaskIdentificationError("Max retries exceeded")

    def _parse_task_response(self, response_text: str) -> List[IdentifiedTask]:
        """
        Parse LLM response to extract tasks.

        Args:
            response_text: Raw response text from LLM

        Returns:
            List of IdentifiedTask objects

        Raises:
            JSONParseError: If parsing fails
        """
        logger.debug("Parsing task response")

        try:
            # Extract JSON from response (in case there's extra text)
            json_text = self._extract_json(response_text)

            # Parse JSON
            parsed = json.loads(json_text)

            # Validate structure
            if "tasks" not in parsed:
                raise JSONParseError("Response missing 'tasks' field")

            if not isinstance(parsed["tasks"], list):
                raise JSONParseError("'tasks' field must be a list")

            # Convert to IdentifiedTask objects
            tasks = []
            for task_data in parsed["tasks"]:
                try:
                    task = IdentifiedTask(**task_data)
                    tasks.append(task)
                except Exception as e:
                    logger.warning(f"Failed to parse task: {e}. Data: {task_data}")
                    # Continue with other tasks

            if not tasks:
                raise JSONParseError("No valid tasks found in response")

            logger.debug(f"Parsed {len(tasks)} tasks successfully")
            return tasks

        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            logger.error(f"Response text: {response_text[:500]}...")
            raise JSONParseError(f"Invalid JSON in response: {str(e)}")

        except Exception as e:
            logger.error(f"Error parsing task response: {e}")
            raise JSONParseError(f"Failed to parse response: {str(e)}")

    def _extract_json(self, text: str) -> str:
        """
        Extract JSON content from text.

        Handles cases where LLM includes extra text before/after JSON.

        Args:
            text: Raw text

        Returns:
            Extracted JSON string

        Raises:
            JSONParseError: If no JSON found
        """
        # Try to find JSON object in text
        # Look for content between outermost { }
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return match.group(0)

        # If no braces found, assume entire text is JSON
        return text.strip()

    def call_with_retry(
        self, system_prompt: str, user_prompt: str, max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generic method to call LLM with retry logic.

        Args:
            system_prompt: System prompt
            user_prompt: User prompt
            max_tokens: Maximum tokens (optional)

        Returns:
            API response dictionary

        Raises:
            TaskIdentificationError: If call fails after retries
        """
        logger.debug("Calling LLM with retry logic")

        for attempt in range(1, self.max_retries + 1):
            try:
                logger.debug(f"Attempt {attempt}/{self.max_retries}")

                response = self.client.create_message(
                    prompt=user_prompt, system=system_prompt, max_tokens=max_tokens
                )

                return response

            except (APIRateLimitError, APITimeoutError) as e:
                if attempt < self.max_retries:
                    delay = self.retry_delay * (self.backoff_multiplier ** (attempt - 1))
                    logger.warning(f"API error: {e}. Retrying in {delay:.1f}s...")
                    time.sleep(delay)
                else:
                    logger.error(f"API error after {self.max_retries} attempts: {e}")
                    raise TaskIdentificationError(
                        f"Failed after {self.max_retries} attempts: {str(e)}"
                    )

            except Exception as e:
                logger.error(f"Unexpected error on attempt {attempt}: {e}")
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay)
                else:
                    raise TaskIdentificationError(f"LLM call failed: {str(e)}")

        raise TaskIdentificationError("Max retries exceeded")

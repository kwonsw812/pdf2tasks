"""Token usage tracking and cost calculation."""

from typing import List
from ...types.models import TokenUsage
from ...utils.logger import get_logger

logger = get_logger(__name__)


class TokenTracker:
    """
    Tracks token usage and calculates costs.
    """

    # Pricing for Claude models (USD per token)
    PRICING = {
        "claude-3-5-sonnet-20241022": {
            "input": 3.0 / 1_000_000,  # $3 per million tokens
            "output": 15.0 / 1_000_000,  # $15 per million tokens
        },
        "claude-3-sonnet-20240229": {
            "input": 3.0 / 1_000_000,
            "output": 15.0 / 1_000_000,
        },
        "claude-3-haiku-20240307": {
            "input": 0.25 / 1_000_000,  # $0.25 per million tokens
            "output": 1.25 / 1_000_000,  # $1.25 per million tokens
        },
    }

    DEFAULT_MODEL = "claude-3-5-sonnet-20241022"

    def __init__(self, model: str = DEFAULT_MODEL):
        """
        Initialize TokenTracker.

        Args:
            model: Claude model name for pricing
        """
        self.model = model
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0.0
        self.call_count = 0

        logger.info(f"TokenTracker initialized for model: {model}")

    def track(self, token_usage: TokenUsage) -> float:
        """
        Track a token usage and calculate cost.

        Args:
            token_usage: Token usage information

        Returns:
            Cost for this usage in USD
        """
        cost = self.calculate_cost(
            token_usage.input_tokens, token_usage.output_tokens
        )

        # Update totals
        self.total_input_tokens += token_usage.input_tokens
        self.total_output_tokens += token_usage.output_tokens
        self.total_cost += cost
        self.call_count += 1

        logger.debug(
            f"Tracked usage: {token_usage.input_tokens} in, "
            f"{token_usage.output_tokens} out, "
            f"cost: ${cost:.6f}"
        )

        return cost

    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """
        Calculate cost for given token counts.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Cost in USD
        """
        pricing = self.PRICING.get(self.model)

        if not pricing:
            logger.warning(
                f"No pricing info for model {self.model}, using default"
            )
            pricing = self.PRICING[self.DEFAULT_MODEL]

        input_cost = input_tokens * pricing["input"]
        output_cost = output_tokens * pricing["output"]
        total_cost = input_cost + output_cost

        return total_cost

    def get_summary(self) -> dict:
        """
        Get summary of tracked usage.

        Returns:
            Dictionary with usage statistics
        """
        return {
            "model": self.model,
            "total_calls": self.call_count,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_tokens": self.total_input_tokens + self.total_output_tokens,
            "total_cost_usd": self.total_cost,
            "average_tokens_per_call": (
                (self.total_input_tokens + self.total_output_tokens) / self.call_count
                if self.call_count > 0
                else 0
            ),
        }

    def log_summary(self) -> None:
        """
        Log a summary of tracked usage.
        """
        summary = self.get_summary()

        logger.info("=" * 80)
        logger.info("TOKEN USAGE SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Model: {summary['model']}")
        logger.info(f"Total API calls: {summary['total_calls']}")
        logger.info(f"Input tokens: {summary['total_input_tokens']:,}")
        logger.info(f"Output tokens: {summary['total_output_tokens']:,}")
        logger.info(f"Total tokens: {summary['total_tokens']:,}")
        logger.info(f"Total cost: ${summary['total_cost_usd']:.6f}")

        if summary['total_calls'] > 0:
            logger.info(
                f"Average tokens/call: {summary['average_tokens_per_call']:.1f}"
            )

        logger.info("=" * 80)

    def reset(self) -> None:
        """
        Reset tracking counters.
        """
        logger.info("Resetting token tracker")
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0.0
        self.call_count = 0

    def get_total_tokens(self) -> int:
        """
        Get total tokens used.

        Returns:
            Total token count
        """
        return self.total_input_tokens + self.total_output_tokens

    def get_total_cost(self) -> float:
        """
        Get total cost.

        Returns:
            Total cost in USD
        """
        return self.total_cost

    def estimate_cost_for_tokens(self, input_tokens: int, output_tokens: int) -> float:
        """
        Estimate cost for a given token count without tracking.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Estimated cost in USD
        """
        return self.calculate_cost(input_tokens, output_tokens)


def create_token_usage(input_tokens: int, output_tokens: int) -> TokenUsage:
    """
    Create a TokenUsage object.

    Helper function for creating TokenUsage instances.

    Args:
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens

    Returns:
        TokenUsage object
    """
    return TokenUsage(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=input_tokens + output_tokens,
    )

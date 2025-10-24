"""Cost calculation utilities for LLM usage."""

from typing import Dict

# Claude 3.5 Sonnet pricing (as of 2024)
CLAUDE_PRICING: Dict[str, Dict[str, float]] = {
    "claude-3-5-sonnet-20241022": {
        "input_per_1m": 3.0,  # $3 per 1M input tokens
        "output_per_1m": 15.0,  # $15 per 1M output tokens
    },
    "claude-3-sonnet-20240229": {
        "input_per_1m": 3.0,
        "output_per_1m": 15.0,
    },
    "claude-3-opus-20240229": {
        "input_per_1m": 15.0,
        "output_per_1m": 75.0,
    },
    "claude-3-haiku-20240307": {
        "input_per_1m": 0.25,
        "output_per_1m": 1.25,
    },
}


def calculate_cost(
    input_tokens: int,
    output_tokens: int,
    model: str = "claude-3-5-sonnet-20241022",
) -> float:
    """
    Calculate LLM API cost based on token usage.

    Args:
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        model: Model name (default: claude-3-5-sonnet-20241022)

    Returns:
        Cost in USD

    Example:
        >>> calculate_cost(1000, 2000)
        0.033  # $0.033
        >>> calculate_cost(100000, 50000, "claude-3-5-sonnet-20241022")
        1.05  # $1.05
    """
    # Get pricing for model, default to Claude 3.5 Sonnet if not found
    pricing = CLAUDE_PRICING.get(model, CLAUDE_PRICING["claude-3-5-sonnet-20241022"])

    # Calculate cost
    input_cost = (input_tokens / 1_000_000) * pricing["input_per_1m"]
    output_cost = (output_tokens / 1_000_000) * pricing["output_per_1m"]

    return input_cost + output_cost


def get_pricing_info(model: str = "claude-3-5-sonnet-20241022") -> Dict[str, float]:
    """
    Get pricing information for a specific model.

    Args:
        model: Model name

    Returns:
        Dictionary with pricing information

    Example:
        >>> get_pricing_info("claude-3-5-sonnet-20241022")
        {'input_per_1m': 3.0, 'output_per_1m': 15.0}
    """
    return CLAUDE_PRICING.get(model, CLAUDE_PRICING["claude-3-5-sonnet-20241022"])


def estimate_cost_for_tokens(total_tokens: int, model: str = "claude-3-5-sonnet-20241022") -> float:
    """
    Estimate cost assuming 50/50 split between input and output tokens.

    Args:
        total_tokens: Total number of tokens
        model: Model name

    Returns:
        Estimated cost in USD

    Example:
        >>> estimate_cost_for_tokens(10000)
        0.09  # $0.09
    """
    input_tokens = total_tokens // 2
    output_tokens = total_tokens - input_tokens
    return calculate_cost(input_tokens, output_tokens, model)

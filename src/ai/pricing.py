"""
OpenAI pricing configuration.

Prices as of October 2025 (per 1M tokens).
Source: https://openai.com/api/pricing/
Last updated: 2025-10-02

gpt-4o-mini:
  - Input: $0.15 / 1M tokens
  - Cached Input: $0.075 / 1M tokens
  - Output: $0.60 / 1M tokens
"""

# Prices per 1K tokens (divide by 1000)
PRICING = {
    "gpt-4o-mini": {
        "input_per_1k": 0.00015,        # $0.15 / 1M = $0.00015 / 1K
        "cached_per_1k": 0.000075,      # $0.075 / 1M = $0.000075 / 1K
        "output_per_1k": 0.0006,        # $0.60 / 1M = $0.0006 / 1K
    },
    "gpt-4o": {
        "input_per_1k": 0.0025,
        "cached_per_1k": 0.00125,
        "output_per_1k": 0.01,
    }
}


def get_model_pricing(model: str) -> dict:
    """
    Get pricing configuration for a model.
    
    Args:
        model: Model name (e.g., "gpt-4o-mini")
    
    Returns:
        Dictionary with pricing per 1K tokens
    """
    # Default to gpt-4o-mini if model not found
    return PRICING.get(model, PRICING["gpt-4o-mini"])


def calculate_cost(
    prompt_tokens: int,
    completion_tokens: int,
    cached_tokens: int,
    model: str
) -> float:
    """
    Calculate cost for a request.
    
    Args:
        prompt_tokens: Number of input tokens
        completion_tokens: Number of output tokens
        cached_tokens: Number of cached input tokens
        model: Model name
    
    Returns:
        Cost in USD
    """
    pricing = get_model_pricing(model)
    
    # Regular input tokens (non-cached)
    regular_input = prompt_tokens - cached_tokens
    
    cost = (
        (regular_input * pricing["input_per_1k"]) +
        (cached_tokens * pricing["cached_per_1k"]) +
        (completion_tokens * pricing["output_per_1k"])
    ) / 1000
    
    return cost

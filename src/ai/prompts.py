"""
Load and format prompts from YAML configuration
"""

import yaml
from pathlib import Path
from src.models import StoryInput
import logging

logger = logging.getLogger(__name__)

# Cache loaded prompts
_prompts_cache = None


def load_prompts() -> dict:
    """
    Load prompts from YAML file.
    
    Returns:
        Dictionary with prompt templates
    """
    global _prompts_cache
    
    if _prompts_cache is not None:
        return _prompts_cache
    
    prompts_file = Path("config/prompts.yaml")
    
    if not prompts_file.exists():
        raise FileNotFoundError(f"Prompts file not found: {prompts_file}")
    
    with open(prompts_file, "r", encoding="utf-8") as f:
        _prompts_cache = yaml.safe_load(f)
    
    logger.info("Prompts loaded from YAML")
    return _prompts_cache


def get_classification_prompt(story: StoryInput) -> tuple[str, str]:
    """
    Get system and user prompts for story classification.
    
    Args:
        story: StoryInput object with story data
    
    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    prompts = load_prompts()
    
    system_prompt = prompts["classification"]["system"]
    user_template = prompts["classification"]["user_template"]
    
    # Format user prompt with story data
    user_prompt = user_template.format(
        title=story.title,
        url=story.url or "None (Ask HN/Show HN)",
        points=story.points,
        comments=story.comments
    )
    
    return system_prompt, user_prompt

"""
OpenAI integration for story classification using Responses API
"""

from openai import AsyncOpenAI
from src.models import Story, StoryInput, StoryClassification, ClassifiedStory, ClassificationResponse
from src.ai.prompts import get_classification_prompt
from src.exceptions import AIClassificationError, AIRateLimitError, AITimeoutError
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def get_openai_config() -> tuple[AsyncOpenAI, str]:
    """
    Get configured OpenAI async client and model name from environment.
    
    Returns:
        Tuple of (AsyncOpenAI client, model name)
        
    Raises:
        AIClassificationError: If API key or model is not configured
    """
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL")
    
    if not api_key:
        raise AIClassificationError(
            "OPENAI_API_KEY not found in environment variables"
        )
    
    if not model:
        raise AIClassificationError(
            "OPENAI_MODEL not found in environment variables"
        )
    
    logger.info(f"Using OpenAI model: {model}")
    return AsyncOpenAI(api_key=api_key), model


async def classify_single_story(
    story: Story,
    index: int,
    client: Optional[AsyncOpenAI] = None,
    model: Optional[str] = None
) -> StoryClassification:
    """
    Classify a single story using OpenAI Responses API.
    
    Args:
        story: Story object to classify
        index: Index of the story in the list
        client: Optional AsyncOpenAI client (for testing)
        model: Optional model override (for testing)
    
    Returns:
        StoryClassification object
        
    Raises:
        AIClassificationError: If classification fails
        AIRateLimitError: If rate limit is hit
        AITimeoutError: If request times out
    """
    if client is None or model is None:
        client, model = get_openai_config()
    
    try:
        # Prepare input
        story_input = StoryInput.from_story(story, index)
        system_prompt, user_prompt = get_classification_prompt(story_input)
        
        logger.info(f"Classifying story {index}: {story.title[:50]}...")
        
        # Call OpenAI Responses API with Structured Outputs using responses.parse()
        response = await client.responses.parse(
            model=model,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            text_format=StoryClassification,  # Pydantic model directly!
            temperature=0.3  # Lower temperature for consistent classifications
        )
        
        # Get parsed output - already a StoryClassification object!
        classification = response.output_parsed
        
        logger.info(
            f"Classified story {index}: category={classification.category}, "
            f"confidence={classification.confidence}"
        )
        
        return classification
        
    except Exception as e:
        error_msg = str(e).lower()
        
        if "rate_limit" in error_msg or "rate limit" in error_msg:
            logger.error(f"Rate limit hit for story {index}")
            raise AIRateLimitError(f"OpenAI rate limit exceeded: {e}") from e
        
        if "timeout" in error_msg:
            logger.error(f"Timeout classifying story {index}")
            raise AITimeoutError(f"OpenAI request timeout: {e}") from e
        
        logger.error(f"Error classifying story {index}: {e}")
        raise AIClassificationError(f"Failed to classify story: {e}") from e


async def classify_stories(
    stories: list[Story],
    max_stories: int = 5
) -> ClassificationResponse:
    """
    Classify multiple stories using OpenAI Responses API.
    
    Only classifies the first `max_stories` stories as per requirements.
    
    Args:
        stories: List of Story objects
        max_stories: Maximum number of stories to classify (default: 5)
    
    Returns:
        ClassificationResponse with classified stories
        
    Raises:
        AIClassificationError: If classification fails
    """
    client, model = get_openai_config()
    
    # Take only first N stories
    stories_to_classify = stories[:max_stories]
    
    logger.info(f"Classifying {len(stories_to_classify)} stories with {model}")
    
    classified_stories = []
    
    for index, story in enumerate(stories_to_classify):
        try:
            # Classify single story
            classification = await classify_single_story(
                story=story,
                index=index,
                client=client,
                model=model
            )
            
            # Combine story + classification
            classified_story = ClassifiedStory.from_story_and_classification(
                story, classification
            )
            classified_stories.append(classified_story)
            
        except (AIClassificationError, AIRateLimitError, AITimeoutError) as e:
            logger.error(f"Failed to classify story {index}: {e}")
            # Continue with other stories even if one fails
            continue
    
    response = ClassificationResponse(
        model=model,
        total=len(classified_stories),
        schema_version="1",
        items=classified_stories
    )
    
    logger.info(
        f"Successfully classified {len(classified_stories)}/{len(stories_to_classify)} stories"
    )
    
    return response

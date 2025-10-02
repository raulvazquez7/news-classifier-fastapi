"""
OpenAI integration for story classification using Responses API
"""

from openai import AsyncOpenAI
from src.models import Story, StoryInput, StoryClassification, ClassifiedStory, ClassificationResponse
from src.ai.prompts import get_classification_prompt
from src.exceptions import AIClassificationError, AIRateLimitError, AITimeoutError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)
import os
import asyncio
import time
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


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((AIRateLimitError, AITimeoutError)),
    reraise=True
)
async def classify_single_story(
    story: Story,
    index: int,
    client: Optional[AsyncOpenAI] = None,
    model: Optional[str] = None
) -> StoryClassification:
    """
    Classify a single story using OpenAI Responses API.
    
    Includes retry logic for rate limits and timeouts.
    
    Args:
        story: Story object to classify
        index: Index of the story in the list
        client: Optional AsyncOpenAI client (for testing)
        model: Optional model override (for testing)
    
    Returns:
        StoryClassification object
        
    Raises:
        AIClassificationError: If classification fails
        AIRateLimitError: If rate limit is hit (will retry)
        AITimeoutError: If request times out (will retry)
    """
    if client is None or model is None:
        client, model = get_openai_config()
    
    start_time = time.time()
    
    try:
        # Prepare input
        story_input = StoryInput.from_story(story, index)
        system_prompt, user_prompt = get_classification_prompt(story_input)
        
        logger.info(f"Classifying story {index}: {story.title[:50]}...")
        
        # Call OpenAI Responses API with timeout and structured outputs
        response = await asyncio.wait_for(
            client.responses.parse(
                model=model,
                input=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                text_format=StoryClassification,
                temperature=0.3
            ),
            timeout=30.0  # 30 seconds timeout
        )
        
        # Get parsed output - already a StoryClassification object!
        classification = response.output_parsed
        
        # Calculate elapsed time
        elapsed = time.time() - start_time
        
        logger.info(
            f"✅ Story {index} classified | "
            f"Category: {classification.category} | "
            f"Confidence: {classification.confidence}% | "
            f"Latency: {elapsed:.2f}s"
        )
        
        return classification
        
    except asyncio.TimeoutError as e:
        elapsed = time.time() - start_time
        logger.error(f"⏱️ Timeout classifying story {index} after {elapsed:.1f}s")
        raise AITimeoutError(f"OpenAI request timeout after {elapsed:.1f}s") from e
    
    except Exception as e:
        error_msg = str(e).lower()
        
        if "rate_limit" in error_msg or "rate limit" in error_msg:
            logger.warning(f"⚠️ Rate limit hit for story {index} (will retry)")
            raise AIRateLimitError(f"OpenAI rate limit exceeded: {e}") from e
        
        if "timeout" in error_msg:
            logger.warning(f"⚠️ Timeout for story {index} (will retry)")
            raise AITimeoutError(f"OpenAI request timeout: {e}") from e
        
        logger.error(f"❌ Error classifying story {index}: {e}")
        raise AIClassificationError(f"Failed to classify story: {e}") from e


async def classify_stories(
    stories: list[Story],
    max_stories: int = 5
) -> ClassificationResponse:
    """
    Classify multiple stories using OpenAI in parallel.
    
    Uses semaphore to limit concurrent requests (max 3 simultaneous).
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
    
    logger.info(f"🚀 Starting classification of {len(stories_to_classify)} stories with {model}")
    logger.info(f"🔄 Using parallel execution (max 3 concurrent requests)")
    
    start_time = time.time()
    
    # Semaphore to limit concurrent requests (max 3 at a time)
    semaphore = asyncio.Semaphore(3)
    
    async def classify_with_semaphore(story: Story, index: int):
        """Wrapper to classify with semaphore control"""
        async with semaphore:
            try:
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
                return classified_story
                
            except (AIClassificationError, AIRateLimitError, AITimeoutError) as e:
                logger.error(f"❌ Failed to classify story {index} after retries: {e}")
                return None  # Return None for failed classifications
    
    # Create tasks for all stories
    tasks = [
        classify_with_semaphore(story, index)
        for index, story in enumerate(stories_to_classify)
    ]
    
    # Execute in parallel (with semaphore control)
    results = await asyncio.gather(*tasks, return_exceptions=False)
    
    # Filter out None (failed classifications)
    classified_stories = [r for r in results if r is not None]
    
    # Calculate total metrics
    total_elapsed = time.time() - start_time
    
    response = ClassificationResponse(
        model=model,
        total=len(classified_stories),
        schema_version="1",
        items=classified_stories
    )
    
    logger.info(
        f"✅ Classification complete | "
        f"Success: {len(classified_stories)}/{len(stories_to_classify)} | "
        f"Total time: {total_elapsed:.2f}s | "
        f"Avg per story: {total_elapsed/len(classified_stories):.2f}s"
    )
    
    return response

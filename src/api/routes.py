"""
FastAPI routes for Hacker News API.

Simple HTTP layer: validation, error handling, response formatting.
"""

from fastapi import APIRouter, HTTPException, Depends, Path
from src.models import Story, ClassificationResponse
from src.cache import CacheManager
from src.ai import classify_stories
from src.api.dependencies import get_cache_manager
from src.services import StoryService
import httpx

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        Status and cache statistics
    """
    cache = get_cache_manager()
    stats = cache.get_stats()
    
    return {
        "status": "healthy",
        "cache": stats
    }


@router.get("/{pages}", response_model=list[Story])
async def get_stories(
    pages: int = Path(1, ge=1, le=10, description="Pages to fetch (1-10), defaults to 1 if omitted"),
    cache: CacheManager = Depends(get_cache_manager)
) -> list[Story]:
    """
    Get stories from N pages. Uses incremental caching.

    If 'pages' is not provided, defaults to 1 (same as the root endpoint).
    """
    try:
        return await StoryService.fetch_and_cache_stories(pages, cache)
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"HN scraping failed: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ai/classify/{pages}", response_model=ClassificationResponse)
async def classify_hn_stories(
    pages: int = Path(..., ge=1, le=10, description="Pages to classify (1-10)"),
    cache: CacheManager = Depends(get_cache_manager)
) -> ClassificationResponse:
    """Classify stories from N pages using OpenAI (first 5 only)."""
    try:
        stories = await StoryService.fetch_and_cache_stories(pages, cache)
        return await classify_stories(stories, max_stories=5)
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"HN scraping failed: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Classification failed: {e}")
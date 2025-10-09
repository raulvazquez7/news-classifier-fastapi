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


@router.get("/", response_model=list[Story])
async def get_default_stories(
    cache: CacheManager = Depends(get_cache_manager)
) -> list[Story]:
    """
    Get stories from page 1 (default endpoint).
    
    Behaves the same as GET /1
    
    Returns:
        List of 30 stories from page 1
    """
    return await get_stories(1, cache)


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


@router.get("/{pages}", response_model=list[Story])
async def get_stories(
    pages: int = Path(..., ge=1, le=10, description="Pages to fetch (1-10)"),
    cache: CacheManager = Depends(get_cache_manager)
) -> list[Story]:
    """Get stories from N pages. Uses incremental caching."""
    try:
        return await StoryService.fetch_and_cache_stories(pages, cache)
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"HN scraping failed: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

"""
FastAPI routes for Hacker News API
"""

from fastapi import APIRouter, HTTPException, Depends
from src.models import Story
from src.cache import CacheManager
from src.scrapers import scrape_pages
from src.api.dependencies import get_cache_manager
import logging

logger = logging.getLogger(__name__)

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


@router.get("/{pages}", response_model=list[Story])
async def get_stories(
    pages: int,
    cache: CacheManager = Depends(get_cache_manager)
) -> list[Story]:
    """
    Get stories from N pages of Hacker News.
    
    Uses incremental caching: only scrapes missing pages.
    
    Args:
        pages: Number of pages to retrieve (1-indexed)
               Example: 2 means pages 1 and 2 (60 stories)
    
    Returns:
        List of stories (30 * pages stories)
        
    Raises:
        HTTPException: If pages parameter is invalid or scraping fails
    """
    # Validate input
    if pages < 1:
        raise HTTPException(
            status_code=400,
            detail="Pages parameter must be >= 1"
        )
    
    if pages > 10:  # Reasonable limit
        raise HTTPException(
            status_code=400,
            detail="Pages parameter must be <= 10 (max 300 stories)"
        )
    
    try:
        # Check which pages are missing from cache
        missing_pages = cache.get_missing_pages(pages)
        
        if missing_pages:
            logger.info(f"Scraping missing pages: {missing_pages}")
            
            # Scrape missing pages
            scraped_data = await scrape_pages(missing_pages)
            
            # Add to cache
            for page_num, stories in scraped_data.items():
                if stories:  # Only cache if scraping succeeded
                    cache.add_page(page_num, stories)
                else:
                    logger.warning(f"No stories scraped for page {page_num}")
        else:
            logger.info(f"All pages 1-{pages} already in cache")
        
        # Retrieve all stories from cache
        stories = cache.get_stories_up_to(pages)
        
        logger.info(f"Returning {len(stories)} stories from {pages} page(s)")
        return stories
        
    except ValueError as e:
        # Cache error (missing pages that should be there)
        logger.error(f"Cache error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
    except Exception as e:
        # Scraping or other unexpected error
        logger.error(f"Error fetching stories: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch stories: {str(e)}"
        )

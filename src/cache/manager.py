"""
In-memory cache manager for HN stories
"""

from src.models import Story
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Manages incremental caching of scraped HN pages.
    
    The cache is in-memory and non-persistent (cleared on restart).
    It implements incremental logic to avoid re-scraping pages.
    
    Examples:
        - Request /1 → scrapes page 1, stores in cache
        - Request /2 → scrapes only page 2 (page 1 already cached)
        - Request /4 → scrapes pages 3 and 4 (pages 1-2 already cached)
    """
    
    def __init__(self):
        """Initialize empty cache"""
        self._cache: dict[int, list[Story]] = {}
        logger.info("Cache initialized (empty)")
    
    def get_cached_pages(self) -> set[int]:
        """
        Get set of page numbers currently in cache.
        
        Returns:
            Set of cached page numbers
        """
        return set(self._cache.keys())
    
    def get_missing_pages(self, requested: int) -> list[int]:
        """
        Calculate which pages need to be scraped to fulfill request.
        
        Args:
            requested: Number of pages requested (e.g., 3 means pages 1, 2, 3)
        
        Returns:
            Sorted list of page numbers that need to be scraped
            
        Examples:
            - Cache: {} → get_missing_pages(2) → [1, 2]
            - Cache: {1} → get_missing_pages(3) → [2, 3]
            - Cache: {1, 2, 4} → get_missing_pages(4) → [3]
        """
        cached = self.get_cached_pages()
        needed = set(range(1, requested + 1))
        missing = sorted(needed - cached)
        
        logger.info(f"Requested {requested} pages, cached: {cached}, missing: {missing}")
        return missing
    
    def add_page(self, page_num: int, stories: list[Story]) -> None:
        """
        Add a page to the cache.
        
        Args:
            page_num: Page number (1-indexed)
            stories: List of Story objects from that page
        """
        self._cache[page_num] = stories
        logger.info(f"Added page {page_num} to cache ({len(stories)} stories)")
    
    def get_page(self, page_num: int) -> Optional[list[Story]]:
        """
        Get a specific page from cache.
        
        Args:
            page_num: Page number to retrieve
        
        Returns:
            List of stories if cached, None if not in cache
        """
        return self._cache.get(page_num)
    
    def get_stories_up_to(self, page: int) -> list[Story]:
        """
        Get all stories from pages 1 through N (if cached).
        
        Args:
            page: Number of pages to retrieve (e.g., 2 means pages 1 and 2)
        
        Returns:
            Concatenated list of all stories from pages 1 to N
            
        Raises:
            ValueError: If any required page is not in cache
        """
        missing = self.get_missing_pages(page)
        if missing:
            raise ValueError(
                f"Cannot retrieve stories: pages {missing} not in cache. "
                f"Scrape them first."
            )
        
        result = []
        for page_num in range(1, page + 1):
            page_stories = self._cache.get(page_num, [])
            result.extend(page_stories)
        
        logger.info(f"Retrieved {len(result)} stories from pages 1-{page}")
        return result
    
    def clear(self) -> None:
        """
        Clear all cached data.
        
        Useful for testing or manual cache invalidation.
        """
        old_count = len(self._cache)
        self._cache.clear()
        logger.info(f"Cache cleared ({old_count} pages removed)")
    
    def get_stats(self) -> dict:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache stats (pages cached, total stories, etc.)
        """
        total_stories = sum(len(stories) for stories in self._cache.values())
        return {
            "pages_cached": len(self._cache),
            "total_stories": total_stories,
            "cached_page_numbers": sorted(self.get_cached_pages())
        }

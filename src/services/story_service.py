"""
Business logic for fetching stories.

Simple and readable - no over-engineering.
"""

from src.models import Story
from src.cache import CacheManager
from src.scrapers import scrape_pages


class StoryService:
    """
    Story fetching with simple caching.

    Scrapes missing pages, caches them, returns all stories.
    """

    @staticmethod
    async def fetch_and_cache_stories(pages: int, cache: CacheManager) -> list[Story]:
        """
        Get stories from pages 1 to N, with caching.

        Scrapes only missing pages. Raises httpx exceptions on failure.
        """
        # Figure out which pages we need to scrape
        missing = [p for p in range(1, pages + 1) if cache.get(p) is None]

        # Scrape missing pages concurrently
        if missing:
            scraped = await scrape_pages(missing)
            for page_num, stories in scraped.items():
                cache.set(page_num, stories)

        # Collect all stories from cache
        all_stories = []
        for page_num in range(1, pages + 1):
            page_stories = cache.get(page_num)
            if page_stories:
                all_stories.extend(page_stories)

        return all_stories

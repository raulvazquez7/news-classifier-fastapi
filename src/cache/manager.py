"""
Simple in-memory cache for HN stories.

KISS principle: Just a dict wrapper with get/set/stats.
"""

from src.models import Story

class CacheManager:
    """
    Simple cache: dict[page_num -> list[Story]]
    """

    def __init__(self):
        self._cache: dict[int, list[Story]] = {}

    def get(self, page_num: int) -> list[Story] | None:
        """Get stories for a page, or None if not cached."""
        return self._cache.get(page_num)

    def set(self, page_num: int, stories: list[Story]) -> None:
        """Cache stories for a page."""
        self._cache[page_num] = stories

    def get_stats(self) -> dict:
        """Get cache stats for health check."""
        return {
            "pages_cached": len(self._cache),
            "total_stories": sum(len(s) for s in self._cache.values())
        }

    def clear(self) -> None:
        """Clear cache (for testing)."""
        self._cache.clear()

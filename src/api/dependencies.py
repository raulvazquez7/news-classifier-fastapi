"""
Dependency injection for FastAPI
"""

from src.cache import CacheManager
from functools import lru_cache

# Singleton cache instance
_cache_manager: CacheManager | None = None


@lru_cache()
def get_cache_manager() -> CacheManager:
    """
    Get or create singleton CacheManager instance.
    
    Using @lru_cache ensures only one instance is created
    and reused across all requests.
    
    Returns:
        CacheManager singleton instance
    """
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager

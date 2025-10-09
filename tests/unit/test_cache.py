"""
Simple tests for simple cache.
"""

import pytest
from src.cache import CacheManager
from src.models import Story


@pytest.fixture
def cache():
    return CacheManager()


@pytest.fixture
def sample_story():
    return Story(
        title="Test Story",
        url="https://example.com",
        points=100,
        sent_by="testuser",
        published="1 hour ago",
        comments=25
    )


class TestCacheManager:
    """Test basic get/set/stats/clear."""

    def test_get_returns_none_when_empty(self, cache):
        assert cache.get(1) is None

    def test_set_and_get(self, cache, sample_story):
        cache.set(1, [sample_story])
        assert cache.get(1) == [sample_story]

    def test_clear(self, cache, sample_story):
        cache.set(1, [sample_story])
        cache.clear()
        assert cache.get(1) is None

    def test_stats(self, cache, sample_story):
        # Empty
        stats = cache.get_stats()
        assert stats["pages_cached"] == 0
        assert stats["total_stories"] == 0

        # With data
        cache.set(1, [sample_story, sample_story])
        cache.set(2, [sample_story])

        stats = cache.get_stats()
        assert stats["pages_cached"] == 2
        assert stats["total_stories"] == 3

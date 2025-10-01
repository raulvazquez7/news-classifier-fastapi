"""
Unit tests for CacheManager
"""

import pytest
from src.cache import CacheManager
from src.models import Story


@pytest.fixture
def cache():
    """Fresh CacheManager instance"""
    return CacheManager()


@pytest.fixture
def sample_story():
    """Sample Story object"""
    return Story(
        title="Test Story",
        url="https://example.com",
        points=100,
        sent_by="testuser",
        published="1 hour ago",
        comments=25
    )


class TestCacheManagerBasics:
    """Basic cache operations"""
    
    def test_init_empty(self, cache):
        """Test cache starts empty"""
        assert cache.get_cached_pages() == set()
        stats = cache.get_stats()
        assert stats["pages_cached"] == 0
        assert stats["total_stories"] == 0
    
    def test_add_page(self, cache, sample_story):
        """Test adding a page to cache"""
        cache.add_page(1, [sample_story])
        
        assert 1 in cache.get_cached_pages()
        assert cache.get_page(1) == [sample_story]
    
    def test_get_page_not_cached(self, cache):
        """Test getting uncached page returns None"""
        assert cache.get_page(1) is None
    
    def test_clear(self, cache, sample_story):
        """Test clearing cache"""
        cache.add_page(1, [sample_story])
        cache.add_page(2, [sample_story])
        
        assert len(cache.get_cached_pages()) == 2
        
        cache.clear()
        
        assert cache.get_cached_pages() == set()


class TestIncrementalLogic:
    """Test incremental cache behavior"""
    
    def test_missing_pages_empty_cache(self, cache):
        """Test missing pages with empty cache"""
        missing = cache.get_missing_pages(3)
        assert missing == [1, 2, 3]
    
    def test_missing_pages_partial_cache(self, cache, sample_story):
        """Test missing pages with partial cache"""
        cache.add_page(1, [sample_story])
        
        missing = cache.get_missing_pages(3)
        assert missing == [2, 3]
    
    def test_missing_pages_full_cache(self, cache, sample_story):
        """Test missing pages when all cached"""
        cache.add_page(1, [sample_story])
        cache.add_page(2, [sample_story])
        
        missing = cache.get_missing_pages(2)
        assert missing == []
    
    def test_missing_pages_gap_in_cache(self, cache, sample_story):
        """Test missing pages with gap in cache"""
        cache.add_page(1, [sample_story])
        cache.add_page(3, [sample_story])
        
        missing = cache.get_missing_pages(4)
        assert missing == [2, 4]


class TestGetStoriesUpTo:
    """Test retrieving concatenated stories"""
    
    def test_get_stories_single_page(self, cache):
        """Test getting stories from single page"""
        story1 = Story(
            title="Story 1",
            url="https://example.com/1",
            points=10,
            sent_by="user1",
            published="1h ago",
            comments=5
        )
        story2 = Story(
            title="Story 2",
            url="https://example.com/2",
            points=20,
            sent_by="user2",
            published="2h ago",
            comments=10
        )
        
        cache.add_page(1, [story1, story2])
        
        stories = cache.get_stories_up_to(1)
        assert len(stories) == 2
        assert stories[0].title == "Story 1"
        assert stories[1].title == "Story 2"
    
    def test_get_stories_multiple_pages(self, cache):
        """Test getting stories from multiple pages"""
        page1_stories = [
            Story(
                title=f"Story {i}",
                url=f"https://example.com/{i}",
                points=i * 10,
                sent_by=f"user{i}",
                published=f"{i}h ago",
                comments=i
            )
            for i in range(1, 3)
        ]
        
        page2_stories = [
            Story(
                title=f"Story {i}",
                url=f"https://example.com/{i}",
                points=i * 10,
                sent_by=f"user{i}",
                published=f"{i}h ago",
                comments=i
            )
            for i in range(3, 5)
        ]
        
        cache.add_page(1, page1_stories)
        cache.add_page(2, page2_stories)
        
        stories = cache.get_stories_up_to(2)
        assert len(stories) == 4
        assert stories[0].title == "Story 1"
        assert stories[2].title == "Story 3"
    
    def test_get_stories_missing_page_raises(self, cache, sample_story):
        """Test that missing pages raise ValueError"""
        cache.add_page(1, [sample_story])
        
        with pytest.raises(ValueError, match="pages \\[2\\] not in cache"):
            cache.get_stories_up_to(2)


class TestCacheStats:
    """Test cache statistics"""
    
    def test_stats_empty(self, cache):
        """Test stats with empty cache"""
        stats = cache.get_stats()
        assert stats["pages_cached"] == 0
        assert stats["total_stories"] == 0
        assert stats["cached_page_numbers"] == []
    
    def test_stats_with_data(self, cache, sample_story):
        """Test stats with cached data"""
        cache.add_page(1, [sample_story, sample_story])
        cache.add_page(3, [sample_story])
        
        stats = cache.get_stats()
        assert stats["pages_cached"] == 2
        assert stats["total_stories"] == 3
        assert stats["cached_page_numbers"] == [1, 3]

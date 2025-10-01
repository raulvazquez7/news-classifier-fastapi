"""
Unit tests for HN HTML parser
"""

import pytest
from src.scrapers.parser import parse_hn_page, parse_story_row
from src.exceptions import HNParseError
from bs4 import BeautifulSoup


@pytest.fixture
def sample_html():
    """Load sample HN HTML"""
    with open("tests/fixtures/hn_sample.html", "r", encoding="utf-8") as f:
        return f.read()


@pytest.fixture
def sample_soup(sample_html):
    """Parse sample HTML into BeautifulSoup"""
    return BeautifulSoup(sample_html, "lxml")


class TestParseStoryRow:
    """Tests for parse_story_row function"""
    
    def test_parse_normal_story(self, sample_soup):
        """Test parsing a normal story with external URL"""
        story_row = sample_soup.select("tr.athing")[0]
        subtext_row = story_row.find_next_sibling("tr")
        
        story = parse_story_row(story_row, subtext_row)
        
        assert story.title == "Example Article Title"
        assert story.url == "https://example.com/article"
        assert story.points == 150
        assert story.sent_by == "testuser"
        assert story.published == "2 hours ago"
        assert story.comments == 42
    
    def test_parse_ask_hn(self, sample_soup):
        """Test parsing Ask HN (no external URL)"""
        story_rows = sample_soup.select("tr.athing")
        story_row = story_rows[1]  # Second story
        subtext_row = story_row.find_next_sibling("tr")
        
        story = parse_story_row(story_row, subtext_row)
        
        assert story.title == "Ask HN: How do you learn new technologies?"
        assert story.url is None  # Ask HN has no external URL
        assert story.points == 75
        assert story.sent_by == "curious"
        assert story.comments == 23
    
    def test_parse_story_with_discuss(self, sample_soup):
        """Test parsing story with 'discuss' (0 comments)"""
        story_rows = sample_soup.select("tr.athing")
        story_row = story_rows[2]  # Third story
        subtext_row = story_row.find_next_sibling("tr")
        
        story = parse_story_row(story_row, subtext_row)
        
        assert story.title == "Brand New Story"
        assert story.url == "https://newsite.com/new-article"
        assert story.comments == 0  # "discuss" means 0 comments


class TestParseHNPage:
    """Tests for parse_hn_page function"""
    
    def test_parse_full_page(self, sample_html):
        """Test parsing a full HN page"""
        stories = parse_hn_page(sample_html)
        
        assert len(stories) == 3
        
        # Check first story
        assert stories[0].title == "Example Article Title"
        assert stories[0].url == "https://example.com/article"
        
        # Check Ask HN
        assert stories[1].title.startswith("Ask HN")
        assert stories[1].url is None
        
        # Check story with discuss
        assert stories[2].comments == 0
    
    def test_parse_empty_html(self):
        """Test parsing empty HTML"""
        html = "<html><body></body></html>"
        
        with pytest.raises(HNParseError, match="No stories found"):
            parse_hn_page(html)
    
    def test_parse_invalid_html(self):
        """Test parsing malformed HTML"""
        html = "not valid html"
        
        with pytest.raises(HNParseError):
            parse_hn_page(html)

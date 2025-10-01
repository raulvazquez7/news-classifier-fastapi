"""
Unit tests for HN scraper
"""

import pytest
import httpx
from unittest.mock import AsyncMock
from src.scrapers.hn_scraper import fetch_page_html, scrape_page, scrape_single_page
from src.exceptions import HNScraperError, HNTimeoutError, HNPageNotFoundError


@pytest.fixture
def mock_client():
    """Mock httpx AsyncClient"""
    return AsyncMock(spec=httpx.AsyncClient)


@pytest.fixture
def sample_html():
    """Load sample HTML"""
    with open("tests/fixtures/hn_sample.html", "r", encoding="utf-8") as f:
        return f.read()


class TestFetchPageHtml:
    """Tests for fetch_page_html function"""
    
    @pytest.mark.asyncio
    async def test_fetch_page_1_success(self, mock_client, sample_html):
        """Test fetching page 1 successfully"""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.text = sample_html
        mock_client.get.return_value = mock_response
        
        html = await fetch_page_html(1, mock_client)
        
        assert html == sample_html
        mock_client.get.assert_called_once()
        # Verify correct URL for page 1
        call_args = mock_client.get.call_args
        assert call_args[0][0] == "https://news.ycombinator.com"
    
    @pytest.mark.asyncio
    async def test_fetch_page_2_success(self, mock_client, sample_html):
        """Test fetching page 2 with query param"""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.text = sample_html
        mock_client.get.return_value = mock_response
        
        html = await fetch_page_html(2, mock_client)
        
        assert html == sample_html
        call_args = mock_client.get.call_args
        assert "?p=2" in call_args[0][0]
    
    @pytest.mark.asyncio
    async def test_fetch_page_404(self, mock_client):
        """Test handling 404 response"""
        mock_response = AsyncMock()
        mock_response.status_code = 404
        mock_client.get.return_value = mock_response
        
        with pytest.raises(HNPageNotFoundError, match="Page 99 not found"):
            await fetch_page_html(99, mock_client)
    
    @pytest.mark.asyncio
    async def test_fetch_page_timeout(self, mock_client):
        """Test handling timeout"""
        mock_client.get.side_effect = httpx.TimeoutException("Timeout")
        
        with pytest.raises(HNTimeoutError):
            await fetch_page_html(1, mock_client)
    
    @pytest.mark.asyncio
    async def test_fetch_page_500(self, mock_client):
        """Test handling server error"""
        mock_response = AsyncMock()
        mock_response.status_code = 500
        mock_client.get.return_value = mock_response
        
        with pytest.raises(HNScraperError, match="Unexpected status code 500"):
            await fetch_page_html(1, mock_client)


class TestScrapePage:
    """Tests for scrape_page function"""
    
    @pytest.mark.asyncio
    async def test_scrape_page_success(self, mock_client, sample_html):
        """Test scraping a page successfully"""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.text = sample_html
        mock_client.get.return_value = mock_response
        
        stories = await scrape_page(1, mock_client)
        
        assert len(stories) == 3  # Our fixture has 3 stories
        assert stories[0].title == "Example Article Title"
        assert stories[1].url is None  # Ask HN
    
    @pytest.mark.asyncio
    async def test_scrape_page_empty_html(self, mock_client):
        """Test scraping page with invalid HTML"""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.text = "<html><body></body></html>"
        mock_client.get.return_value = mock_response
        
        with pytest.raises(HNScraperError):
            await scrape_page(1, mock_client)


@pytest.mark.asyncio
async def test_scrape_single_page_integration(httpx_mock, sample_html):
    """Integration test for scrape_single_page with httpx mock"""
    # Mock the HTTP request
    httpx_mock.add_response(
        url="https://news.ycombinator.com",
        html=sample_html
    )
    
    stories = await scrape_single_page(1)
    
    assert len(stories) == 3
    assert all(hasattr(s, 'title') for s in stories)

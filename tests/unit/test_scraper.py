"""
Simple tests for simplified scraper.
"""

import pytest
import httpx
from unittest.mock import AsyncMock
from src.scrapers.hn_scraper import fetch_page_html, scrape_page, scrape_single_page


@pytest.fixture
def mock_client():
    return AsyncMock(spec=httpx.AsyncClient)


@pytest.fixture
def sample_html():
    with open("tests/fixtures/hn_sample.html", "r", encoding="utf-8") as f:
        return f.read()


class TestFetchPageHtml:
    """Test fetch with retries."""

    @pytest.mark.asyncio
    async def test_fetch_page_1_success(self, mock_client, sample_html):
        mock_response = AsyncMock()
        mock_response.text = sample_html
        mock_response.raise_for_status = AsyncMock()  # No exception
        mock_client.get.return_value = mock_response

        html = await fetch_page_html(1, mock_client)

        assert html == sample_html
        assert "https://news.ycombinator.com" in str(mock_client.get.call_args)

    @pytest.mark.asyncio
    async def test_fetch_page_2_with_query_param(self, mock_client, sample_html):
        mock_response = AsyncMock()
        mock_response.text = sample_html
        mock_response.raise_for_status = AsyncMock()
        mock_client.get.return_value = mock_response

        html = await fetch_page_html(2, mock_client)

        assert html == sample_html
        assert "?p=2" in str(mock_client.get.call_args)

    @pytest.mark.asyncio
    async def test_fetch_page_404_raises_httpx_error(self, mock_client):
        """Test that 404 raises httpx.HTTPStatusError (not custom exception)."""
        mock_client.get.side_effect = httpx.HTTPStatusError(
            "404", request=AsyncMock(), response=AsyncMock()
        )

        with pytest.raises(httpx.HTTPStatusError):
            await fetch_page_html(99, mock_client)

    @pytest.mark.asyncio
    async def test_fetch_page_timeout_raises_httpx_timeout(self, mock_client):
        """Test that timeout raises httpx.TimeoutException (for tenacity retry)."""
        mock_client.get.side_effect = httpx.TimeoutException("Timeout")

        # Tenacity will retry 3 times, then re-raise
        with pytest.raises(httpx.TimeoutException):
            await fetch_page_html(1, mock_client)


class TestScrapePage:
    """Test scrape_page (fetch + parse)."""

    @pytest.mark.asyncio
    async def test_scrape_page_success(self, mock_client, sample_html):
        mock_response = AsyncMock()
        mock_response.text = sample_html
        mock_response.raise_for_status = AsyncMock()
        mock_client.get.return_value = mock_response

        stories = await scrape_page(1, mock_client)

        assert len(stories) == 3  # Fixture has 3 stories
        assert stories[0].title == "Example Article Title"


@pytest.mark.asyncio
async def test_scrape_single_page_integration(httpx_mock, sample_html):
    """Integration test with httpx mock."""
    httpx_mock.add_response(url="https://news.ycombinator.com", html=sample_html)

    stories = await scrape_single_page(1)

    assert len(stories) == 3
    assert all(hasattr(s, "title") for s in stories)

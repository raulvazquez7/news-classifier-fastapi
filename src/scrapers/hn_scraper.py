"""
Asynchronous scraper for Hacker News
"""

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)
from src.models import Story
from src.scrapers.parser import parse_hn_page
from src.exceptions import HNScraperError, HNTimeoutError, HNPageNotFoundError
import logging

logger = logging.getLogger(__name__)

# Constants
HN_BASE_URL = "https://news.ycombinator.com"
REQUEST_TIMEOUT = 10.0  # seconds
USER_AGENT = "HN-API-AI-Bot/1.0 (Educational Purpose)"


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)),
    reraise=True
)
async def fetch_page_html(page_num: int, client: httpx.AsyncClient) -> str:
    """
    Fetch HTML content from a specific HN page with retry logic.
    
    Args:
        page_num: Page number (1-indexed)
        client: httpx AsyncClient instance
    
    Returns:
        HTML content as string
        
    Raises:
        HNPageNotFoundError: If page returns 404
        HNTimeoutError: If request times out after retries
        HNScraperError: For other HTTP errors
    """
    try:
        # Construct URL
        if page_num == 1:
            url = HN_BASE_URL
        else:
            url = f"{HN_BASE_URL}?p={page_num}"
        
        logger.info(f"Fetching HN page {page_num}: {url}")
        
        # Make request
        response = await client.get(
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=REQUEST_TIMEOUT,
            follow_redirects=True
        )
        
        # Handle response
        if response.status_code == 404:
            raise HNPageNotFoundError(f"Page {page_num} not found")
        
        if response.status_code != 200:
            raise HNScraperError(
                f"Unexpected status code {response.status_code} for page {page_num}"
            )
        
        logger.info(f"Successfully fetched page {page_num} ({len(response.text)} bytes)")
        return response.text
        
    except httpx.TimeoutException as e:
        logger.error(f"Timeout fetching page {page_num}")
        raise HNTimeoutError(f"Timeout fetching page {page_num}") from e
    
    except (HNPageNotFoundError, HNTimeoutError):
        # Re-raise our custom exceptions
        raise
    
    except Exception as e:
        logger.error(f"Error fetching page {page_num}: {e}")
        raise HNScraperError(f"Failed to fetch page {page_num}: {str(e)}") from e


async def scrape_page(page_num: int, client: httpx.AsyncClient) -> list[Story]:
    """
    Scrape a single HN page and return parsed stories.
    
    Args:
        page_num: Page number to scrape (1-indexed)
        client: httpx AsyncClient instance
    
    Returns:
        List of Story objects (typically 30 stories)
        
    Raises:
        HNScraperError: If scraping or parsing fails
    """
    try:
        # Fetch HTML
        html = await fetch_page_html(page_num, client)
        
        # Parse HTML
        stories = parse_hn_page(html)
        
        logger.info(f"Successfully scraped {len(stories)} stories from page {page_num}")
        return stories
        
    except Exception as e:
        if isinstance(e, (HNScraperError, HNTimeoutError, HNPageNotFoundError)):
            raise
        raise HNScraperError(f"Failed to scrape page {page_num}: {str(e)}") from e


async def scrape_pages(page_nums: list[int]) -> dict[int, list[Story]]:
    """
    Scrape multiple HN pages concurrently.
    
    Args:
        page_nums: List of page numbers to scrape
    
    Returns:
        Dictionary mapping page_num -> list of stories
        
    Raises:
        HNScraperError: If scraping fails
    """
    results = {}
    
    async with httpx.AsyncClient() as client:
        for page_num in page_nums:
            try:
                stories = await scrape_page(page_num, client)
                results[page_num] = stories
            except HNScraperError as e:
                logger.error(f"Failed to scrape page {page_num}: {e}")
                # Continue with other pages even if one fails
                results[page_num] = []
    
    return results


async def scrape_single_page(page_num: int) -> list[Story]:
    """
    Convenience function to scrape a single page.
    
    Args:
        page_num: Page number to scrape (1-indexed)
    
    Returns:
        List of Story objects
    """
    async with httpx.AsyncClient() as client:
        return await scrape_page(page_num, client)

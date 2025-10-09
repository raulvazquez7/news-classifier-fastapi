"""
Asynchronous scraper for Hacker News
"""

import asyncio
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from src.models import Story
from src.scrapers.parser import parse_hn_page
import logging

logger = logging.getLogger(__name__)

# Constants
HN_BASE_URL = "https://news.ycombinator.com"
REQUEST_TIMEOUT = 10.0  # seconds
USER_AGENT = "HN-API-AI-Bot/1.0 (Educational Purpose)"


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True
)
async def fetch_page_html(page_num: int, client: httpx.AsyncClient) -> str:
    """
    Fetch HTML from HN page with retry.

    Retries httpx exceptions automatically (tenacity handles it).
    No custom exceptions - let httpx exceptions propagate for retry.
    """
    url = HN_BASE_URL if page_num == 1 else f"{HN_BASE_URL}?p={page_num}"

    response = await client.get(
        url,
        headers={"User-Agent": USER_AGENT},
        timeout=REQUEST_TIMEOUT,
        follow_redirects=True
    )

    response.raise_for_status()  # Raises httpx.HTTPStatusError for 4xx/5xx
    return response.text


async def scrape_page(page_num: int, client: httpx.AsyncClient) -> list[Story]:
    """Scrape a single HN page. Raises httpx exceptions on failure."""
    html = await fetch_page_html(page_num, client)
    return parse_hn_page(html)


async def scrape_pages(page_nums: list[int]) -> dict[int, list[Story]]:
    """
    Scrape multiple pages concurrently.

    Fail-fast: If any page fails, entire operation fails.
    Raises httpx exceptions directly (no wrapping).
    """
    if not page_nums:
        return {}

    async with httpx.AsyncClient() as client:
        tasks = [scrape_page(page_num, client) for page_num in page_nums]
        stories_lists = await asyncio.gather(*tasks)  # Fail-fast
        return dict(zip(page_nums, stories_lists))


async def scrape_single_page(page_num: int) -> list[Story]:
    """Scrape a single page (helper for testing)."""
    async with httpx.AsyncClient() as client:
        return await scrape_page(page_num, client)

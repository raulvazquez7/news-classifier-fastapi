"""
HTML parser for Hacker News stories
"""

from bs4 import BeautifulSoup, Tag
from src.models import Story
from src.exceptions import HNParseError
import re
from typing import Optional


def parse_story_row(story_row: Tag, subtext_row: Tag) -> Story:
    """
    Parse a single story from HN HTML structure.
    
    Args:
        story_row: <tr class="athing"> element
        subtext_row: Following <tr> with <td class="subtext">
    
    Returns:
        Story object
        
    Raises:
        HNParseError: If required fields are missing or invalid
    """
    try:
        # Extract title and URL
        titleline = story_row.select_one(".titleline")
        if not titleline:
            raise HNParseError("Missing .titleline in story row")
        
        title_link = titleline.select_one("a")
        if not title_link:
            raise HNParseError("Missing title link in story")
        
        title = title_link.get_text(strip=True)
        href = title_link.get("href", "")
        
        # Determine if it's an external URL or Ask HN / Show HN
        if href.startswith("item?id="):
            url = None  # Ask HN, Show HN, etc. (no external URL)
        elif href.startswith("http"):
            url = href  # External URL
        else:
            # Relative URL - prepend HN base
            url = f"https://news.ycombinator.com/{href}"
        
        # Extract metadata from subtext
        subtext = subtext_row.select_one(".subtext")
        if not subtext:
            raise HNParseError("Missing .subtext in subtext row")
        
        # Points
        score_elem = subtext.select_one(".score")
        if score_elem:
            score_text = score_elem.get_text(strip=True)
            points_match = re.search(r'(\d+)', score_text)
            points = int(points_match.group(1)) if points_match else 0
        else:
            # New stories might not have points yet
            points = 0
        
        # Sent by (username)
        user_elem = subtext.select_one(".hnuser")
        if user_elem:
            sent_by = user_elem.get_text(strip=True)
        else:
            sent_by = "unknown"
        
        # Published time
        age_elem = subtext.select_one(".age")
        if age_elem:
            published = age_elem.get_text(strip=True)
        else:
            published = "recently"
        
        # Comments
        # Find all links in subtext, last one is usually comments
        subtext_links = subtext.select("a")
        comments = 0
        for link in reversed(subtext_links):
            link_text = link.get_text(strip=True)
            if "comment" in link_text.lower():
                comments_match = re.search(r'(\d+)', link_text)
                if comments_match:
                    comments = int(comments_match.group(1))
                break
            elif link_text == "discuss":
                # "discuss" means 0 comments
                comments = 0
                break
        
        return Story(
            title=title,
            url=url,
            points=points,
            sent_by=sent_by,
            published=published,
            comments=comments
        )
        
    except Exception as e:
        if isinstance(e, HNParseError):
            raise
        raise HNParseError(f"Failed to parse story: {str(e)}") from e


def parse_hn_page(html: str) -> list[Story]:
    """
    Parse a full Hacker News page HTML.
    
    Args:
        html: HTML content of HN page
    
    Returns:
        List of Story objects (typically 30 stories)
        
    Raises:
        HNParseError: If HTML structure is invalid
    """
    try:
        soup = BeautifulSoup(html, "lxml")
        
        # Find all story rows
        story_rows = soup.select("tr.athing")
        
        if not story_rows:
            raise HNParseError("No stories found in HTML")
        
        stories = []
        
        for story_row in story_rows:
            # Find the next sibling row which contains subtext
            subtext_row = story_row.find_next_sibling("tr")
            
            if not subtext_row or not subtext_row.select_one(".subtext"):
                # Skip if no subtext (might be a spacer or ad)
                continue
            
            try:
                story = parse_story_row(story_row, subtext_row)
                stories.append(story)
            except HNParseError as e:
                # Log error but continue parsing other stories
                print(f"Warning: Failed to parse story: {e}")
                continue
        
        return stories
        
    except Exception as e:
        if isinstance(e, HNParseError):
            raise
        raise HNParseError(f"Failed to parse HN page: {str(e)}") from e

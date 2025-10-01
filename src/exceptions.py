"""
Custom exceptions for the application
"""


class HNScraperError(Exception):
    """Base exception for scraping errors"""
    pass


class HNPageNotFoundError(HNScraperError):
    """Raised when a Hacker News page is not found"""
    pass


class HNParseError(HNScraperError):
    """Raised when HTML parsing fails"""
    pass


class HNTimeoutError(HNScraperError):
    """Raised when request to HN times out"""
    pass


class CacheError(Exception):
    """Base exception for cache errors"""
    pass


class AIClassificationError(Exception):
    """Base exception for AI classification errors"""
    pass


class AIRateLimitError(AIClassificationError):
    """Raised when OpenAI rate limit is hit"""
    pass


class AITimeoutError(AIClassificationError):
    """Raised when OpenAI request times out"""
    pass


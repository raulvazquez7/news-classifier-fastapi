"""
Pydantic models for OpenAI classification
"""

from pydantic import BaseModel, Field
from typing import Literal


class StoryClassification(BaseModel):
    """
    OpenAI classification result for a single story.
    This model is used as structured output for OpenAI Responses API.
    """
    
    category: Literal[
        "ai-ml",
        "programming",
        "security",
        "devops",
        "hardware",
        "science",
        "business",
        "web",
        "mobile",
        "database",
        "math",
        "history",
        "politics",
        "ask-hn",
        "show-hn",
        "launch-hn",
        "job",
        "meta",
        "other"
    ] = Field(..., description="Primary category of the story")
    
    intent: Literal[
        "news",
        "discussion",
        "tutorial",
        "research",
        "opinion",
        "announcement",
        "ask_hn",
        "show_hn",
        "launch_hn",
        "job"
    ] = Field(..., description="Intent or purpose of the story")
    
    tags: list[str] = Field(
        ...,
        min_length=1,
        max_length=6,
        description="Relevant tags (1-6 items)"
    )
    
    confidence: int = Field(
        ...,
        ge=0,
        le=100,
        description="Confidence score (0-100)"
    )
    
    reason_brief: str = Field(
        ...,
        max_length=160,
        description="Brief explanation (max 160 chars)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "category": "ai-ml",
                "intent": "news",
                "tags": ["AI", "Machine Learning", "GPT"],
                "confidence": 90,
                "reason_brief": "Article discussing recent advancements in AI technology."
            }
        }
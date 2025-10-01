"""
Pydantic models for API responses
"""

from pydantic import BaseModel, Field
from typing import List
from .story import Story
from .classification import StoryClassification


class ClassifiedStory(BaseModel):
    """
    A story with its AI classification.
    Combines Story fields with StoryClassification fields.
    """
    
    # Story fields
    title: str
    url: str | None
    points: int
    sent_by: str
    published: str
    comments: int
    
    # Classification fields
    category: str
    intent: str
    tags: List[str]
    confidence: int
    reason_brief: str
    
    @classmethod
    def from_story_and_classification(
        cls,
        story: Story,
        classification: StoryClassification
    ) -> "ClassifiedStory":
        """Combine a Story and its Classification into a ClassifiedStory"""
        return cls(
            # Story data
            title=story.title,
            url=story.url,
            points=story.points,
            sent_by=story.sent_by,
            published=story.published,
            comments=story.comments,
            # Classification data
            category=classification.category,
            intent=classification.intent,
            tags=classification.tags,
            confidence=classification.confidence,
            reason_brief=classification.reason_brief
        )


class ClassificationResponse(BaseModel):
    """
    Response format for /ai/classify/{pages} endpoint
    """
    
    model: str = Field(..., description="OpenAI model used")
    total: int = Field(..., description="Number of classified stories")
    schema_version: str = Field(default="1", description="Schema version")
    items: List[ClassifiedStory] = Field(..., description="Classified stories")
    
    class Config:
        json_schema_extra = {
            "example": {
                "model": "gpt-4o-mini",
                "total": 5,
                "schema_version": "1",
                "items": [
                    {
                        "title": "Show HN: Vectorless RAG",
                        "url": "https://github.com/...",
                        "points": 103,
                        "sent_by": "page_index",
                        "published": "3 hours ago",
                        "comments": 32,
                        "category": "show-hn",
                        "intent": "show_hn",
                        "tags": ["RAG", "Vectorless"],
                        "confidence": 85,
                        "reason_brief": "Showcase of a new retrieval framework."
                    }
                ]
            }
        }
"""
Pydantic model for Hacker News stories
"""

from pydantic import BaseModel, Field, HttpUrl
from typing import Optional


class Story(BaseModel):
    """
    Represents a Hacker News story.
    
    Attributes:
        title: The title of the story
        url: External URL (can be None for Ask HN stories)
        points: Number of upvotes
        sent_by: Username who submitted the story
        published: Time string (e.g., "2 hours ago")
        comments: Number of comments
    """
    
    title: str = Field(..., min_length=1, description="Story title")
    url: Optional[str] = Field(None, description="External URL (None for Ask HN)")
    points: int = Field(..., ge=0, description="Number of upvotes")
    sent_by: str = Field(..., min_length=1, description="Username of submitter")
    published: str = Field(..., min_length=1, description="Time since publication")
    comments: int = Field(..., ge=0, description="Number of comments")
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Show HN: My Awesome Project",
                "url": "https://github.com/user/project",
                "points": 150,
                "sent_by": "username",
                "published": "3 hours ago",
                "comments": 45
            }
        }


class StoryInput(BaseModel):
    """
    Story data to send to OpenAI for classification.
    Subset of Story fields.
    """
    
    index: int = Field(..., ge=0, description="Position in the list")
    title: str
    url: Optional[str]
    points: int
    comments: int
    
    @classmethod
    def from_story(cls, story: Story, index: int) -> "StoryInput":
        """Create StoryInput from a Story object"""
        return cls(
            index=index,
            title=story.title,
            url=story.url,
            points=story.points,
            comments=story.comments
        )
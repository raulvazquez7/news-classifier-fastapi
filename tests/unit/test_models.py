"""
Unit tests for Pydantic models
"""

import pytest
from pydantic import ValidationError
from src.models import Story, StoryInput, StoryClassification, ClassifiedStory


class TestStory:
    """Tests for Story model"""
    
    def test_valid_story(self):
        """Test creating a valid story"""
        story = Story(
            title="Test Story",
            url="https://example.com",
            points=100,
            sent_by="testuser",
            published="2 hours ago",
            comments=25
        )
        
        assert story.title == "Test Story"
        assert story.url == "https://example.com"
        assert story.points == 100
        assert story.comments == 25
    
    def test_story_without_url(self):
        """Test Ask HN story (no URL)"""
        story = Story(
            title="Ask HN: How do you learn new tech?",
            url=None,
            points=50,
            sent_by="curious",
            published="1 hour ago",
            comments=30
        )
        
        assert story.url is None
        assert story.title.startswith("Ask HN")
    
    def test_story_negative_points_fails(self):
        """Test that negative points are rejected"""
        with pytest.raises(ValidationError):
            Story(
                title="Test",
                url="https://example.com",
                points=-10,  # Invalid
                sent_by="user",
                published="1 hour ago",
                comments=0
            )
    
    def test_story_empty_title_fails(self):
        """Test that empty title is rejected"""
        with pytest.raises(ValidationError):
            Story(
                title="",  # Invalid
                url="https://example.com",
                points=10,
                sent_by="user",
                published="1 hour ago",
                comments=0
            )


class TestStoryInput:
    """Tests for StoryInput model"""
    
    def test_from_story(self):
        """Test creating StoryInput from Story"""
        story = Story(
            title="Test Story",
            url="https://example.com",
            points=100,
            sent_by="testuser",
            published="2 hours ago",
            comments=25
        )
        
        story_input = StoryInput.from_story(story, index=0)
        
        assert story_input.index == 0
        assert story_input.title == story.title
        assert story_input.url == story.url
        assert story_input.points == story.points
        assert story_input.comments == story.comments
        # sent_by and published are not included
        assert not hasattr(story_input, "sent_by")


class TestStoryClassification:
    """Tests for StoryClassification model"""
    
    def test_valid_classification(self):
        """Test creating a valid classification"""
        classification = StoryClassification(
            category="ai-ml",
            intent="news",
            tags=["AI", "Machine Learning"],
            confidence=85,
            reason_brief="Article about AI advancements"
        )
        
        assert classification.category == "ai-ml"
        assert classification.intent == "news"
        assert len(classification.tags) == 2
        assert classification.confidence == 85
    
    def test_invalid_category_fails(self):
        """Test that invalid category is rejected"""
        with pytest.raises(ValidationError):
            StoryClassification(
                category="invalid-category",  # Not in Literal
                intent="news",
                tags=["AI"],
                confidence=85,
                reason_brief="Test"
            )
    
    def test_too_many_tags_fails(self):
        """Test that more than 6 tags is rejected"""
        with pytest.raises(ValidationError):
            StoryClassification(
                category="ai-ml",
                intent="news",
                tags=["Tag1", "Tag2", "Tag3", "Tag4", "Tag5", "Tag6", "Tag7"],  # 7 tags
                confidence=85,
                reason_brief="Test"
            )
    
    def test_empty_tags_fails(self):
        """Test that empty tags list is rejected"""
        with pytest.raises(ValidationError):
            StoryClassification(
                category="ai-ml",
                intent="news",
                tags=[],  # Empty
                confidence=85,
                reason_brief="Test"
            )
    
    def test_confidence_out_of_range_fails(self):
        """Test that confidence outside 0-100 is rejected"""
        with pytest.raises(ValidationError):
            StoryClassification(
                category="ai-ml",
                intent="news",
                tags=["AI"],
                confidence=150,  # > 100
                reason_brief="Test"
            )
    
    def test_reason_too_long_fails(self):
        """Test that reason_brief > 160 chars is rejected"""
        with pytest.raises(ValidationError):
            StoryClassification(
                category="ai-ml",
                intent="news",
                tags=["AI"],
                confidence=85,
                reason_brief="x" * 161  # 161 chars
            )


class TestClassifiedStory:
    """Tests for ClassifiedStory model"""
    
    def test_from_story_and_classification(self):
        """Test combining Story and Classification"""
        story = Story(
            title="Test Story",
            url="https://example.com",
            points=100,
            sent_by="testuser",
            published="2 hours ago",
            comments=25
        )
        
        classification = StoryClassification(
            category="ai-ml",
            intent="news",
            tags=["AI", "ML"],
            confidence=90,
            reason_brief="AI news article"
        )
        
        classified = ClassifiedStory.from_story_and_classification(story, classification)
        
        # Check Story fields
        assert classified.title == story.title
        assert classified.url == story.url
        assert classified.points == story.points
        
        # Check Classification fields
        assert classified.category == classification.category
        assert classified.intent == classification.intent
        assert classified.tags == classification.tags
        assert classified.confidence == classification.confidence

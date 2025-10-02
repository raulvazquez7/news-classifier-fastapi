"""
Quick test for OpenAI classification
"""
import asyncio
import os
from dotenv import load_dotenv
from src.models import Story
from src.ai import classify_stories

load_dotenv()

async def main():
    print("🧪 Testing OpenAI Classification...\n")
    
    # Check env vars
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL")
    
    if not api_key:
        print("❌ OPENAI_API_KEY not found in .env")
        return
    
    if not model:
        print("❌ OPENAI_MODEL not found in .env")
        return
    
    print(f"✅ OPENAI_API_KEY: {api_key[:20]}...")
    print(f"✅ OPENAI_MODEL: {model}\n")
    
    # Create test stories
    test_stories = [
        Story(
            title="Show HN: New AI framework for LLMs",
            url="https://github.com/test/ai-framework",
            points=150,
            sent_by="aidev",
            published="2 hours ago",
            comments=45
        ),
        Story(
            title="Ask HN: How do you learn new programming languages?",
            url=None,
            points=75,
            sent_by="curious",
            published="1 hour ago",
            comments=30
        ),
        Story(
            title="Major security vulnerability found in OpenSSL",
            url="https://security.com/openssl-vuln",
            points=500,
            sent_by="securityexpert",
            published="30 minutes ago",
            comments=200
        )
    ]
    
    print(f"📝 Classifying {len(test_stories)} test stories...\n")
    
    try:
        response = await classify_stories(test_stories, max_stories=3)
        
        print(f"✅ Successfully classified {response.total} stories!\n")
        print(f"Model used: {response.model}")
        print(f"Schema version: {response.schema_version}\n")
        
        for i, item in enumerate(response.items, 1):
            print(f"\n{'='*80}")
            print(f"Story {i}: {item.title}")
            print(f"Category: {item.category}")
            print(f"Intent: {item.intent}")
            print(f"Tags: {', '.join(item.tags)}")
            print(f"Confidence: {item.confidence}%")
            print(f"Reason: {item.reason_brief}")
        
        print(f"\n{'='*80}")
        print("🎉 Test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())

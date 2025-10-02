# Hacker News API with AI Classification

A production-ready asynchronous API that scrapes Hacker News and classifies content using OpenAI's latest Responses API with structured outputs.

## 🎯 Overview

This API provides intelligent access to Hacker News content with:
- **Web scraping** of HN HTML (not using the official API)
- **Incremental caching** for performance optimization
- **AI-powered classification** using OpenAI Responses API
- **Fully asynchronous** design for high concurrency
- **Docker deployment** ready for production

## 🚀 Quick Start

### With Docker (Recommended)

```bash
# 1. Clone the repository
git clone <repo-url>
cd <repo-name>

# 2. Configure environment variables
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# 3. Run with Docker Compose
docker compose up -d

# 4. Test endpoints
curl http://localhost:3000/health
curl http://localhost:3000/1 | python -m json.tool
curl http://localhost:3000/ai/classify/1 | python -m json.tool
```

### Local Development

```bash
# 1. Create virtual environment
python3.12 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt
pip install -e .

# 3. Configure environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# 4. Run the API
uvicorn src.main:app --reload

# 5. Access at http://localhost:8000
```

## 📡 API Endpoints

### `GET /` or `GET /1`
Retrieve 30 stories from page 1 of Hacker News.

**Response:**
```json
[
  {
    "title": "Example Story Title",
    "url": "https://example.com/article",
    "points": 150,
    "sent_by": "username",
    "published": "2 hours ago",
    "comments": 42
  }
]
```

### `GET /{number}`
Retrieve stories from N pages (30 stories per page).

**Examples:**
- `/2` → 60 stories (pages 1-2)
- `/3` → 90 stories (pages 1-3)

**Features:**
- Incremental caching (only scrapes missing pages)
- Maximum 10 pages (300 stories)

### `GET /ai/classify/{pages}`
Classify stories using OpenAI with structured outputs.

**Response:**
```json
{
  "model": "gpt-4o-mini",
  "total": 5,
  "schema_version": "1",
  "items": [
    {
      "title": "Show HN: My Project",
      "url": "https://github.com/user/project",
      "points": 100,
      "sent_by": "developer",
      "published": "3 hours ago",
      "comments": 25,
      "category": "show-hn",
      "intent": "show_hn",
      "tags": ["Project", "Open Source"],
      "confidence": 90,
      "reason_brief": "User showcasing their new project."
    }
  ]
}
```

**Classification Schema:**
- **Categories:** `ai-ml`, `programming`, `security`, `devops`, `hardware`, `science`, `business`, `web`, `mobile`, `database`, `math`, `history`, `politics`, `ask-hn`, `show-hn`, `launch-hn`, `job`, `meta`, `other`
- **Intents:** `news`, `discussion`, `tutorial`, `research`, `opinion`, `announcement`, `ask_hn`, `show_hn`, `launch_hn`, `job`
- **Tags:** 1-6 relevant keywords
- **Confidence:** 0-100 score
- **Reason:** Brief explanation (≤160 chars)

**Notes:**
- Only classifies first 5 stories (optimization)
- Uses cache to avoid re-scraping
- Parallel execution (max 3 concurrent OpenAI requests)

### `GET /health`
Health check endpoint for monitoring.

**Response:**
```json
{
  "status": "healthy",
  "cache": {
    "pages_cached": 2,
    "total_stories": 60,
    "cached_page_numbers": [1, 2]
  }
}
```

## 🏗️ Architecture

### Tech Stack

- **Python 3.12+** - Modern Python with type hints
- **FastAPI** - Async web framework with automatic OpenAPI docs
- **httpx** - Async HTTP client for scraping
- **BeautifulSoup4 + lxml** - HTML parsing
- **OpenAI Responses API** - AI classification with structured outputs
- **Pydantic v2** - Data validation and settings management
- **Tenacity** - Retry logic for resilience
- **Docker + Docker Compose** - Containerization

### Project Structure

```
.
├── src/
```

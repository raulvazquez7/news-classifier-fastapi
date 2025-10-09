# Hacker News API with AI Classification

A simple, production-ready API that scrapes Hacker News and classifies content using OpenAI.

## 🎯 What It Does

- Scrapes Hacker News stories (HTML scraping, not official API)
- Caches results to avoid re-scraping
- Classifies stories using OpenAI's Responses API
- Fully asynchronous for high performance

## 🚀 Quick Start

### With Docker (Recommended)

```bash
# 1. Clone and configure
git clone <repo-url>
cd <repo-name>
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# 2. Run
docker compose up -d

# 3. Test
curl http://localhost:3000/health
curl http://localhost:3000/1
curl http://localhost:3000/ai/classify/1
```

### Local Development

```bash
# 1. Setup
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e .

# 2. Configure
cp .env.example .env
# Add your OPENAI_API_KEY to .env

# 3. Run
uvicorn src.main:app --reload

# Access at http://localhost:8000
```

## 📡 API Endpoints

### `GET /{pages}` - Get Stories

Fetch stories from N pages (30 stories per page, max 10 pages).

**Examples:**
- `/1` → 30 stories
- `/2` → 60 stories (pages 1-2)

**Response:**
```json
[
  {
    "title": "Example Story",
    "url": "https://example.com",
    "points": 150,
    "sent_by": "username",
    "published": "2 hours ago",
    "comments": 42
  }
]
```

### `GET /ai/classify/{pages}` - Classify with AI

Classify stories using OpenAI (first 5 stories only).

**Response:**
```json
{
  "model": "gpt-4o-mini",
  "total": 5,
  "items": [
    {
      "title": "Show HN: My Project",
      "category": "show-hn",
      "intent": "show_hn",
      "tags": ["Project", "Open Source"],
      "confidence": 90,
      "reason_brief": "User showcasing their project."
    }
  ]
}
```

**Categories:** `ai-ml`, `programming`, `security`, `devops`, `hardware`, `science`, `business`, `web`, `mobile`, `show-hn`, `ask-hn`, etc.

### `GET /health` - Health Check

```json
{
  "status": "healthy",
  "cache": {
    "pages_cached": 2,
    "total_stories": 60
  }
}
```

## 🏗️ Architecture

### Tech Stack

- **Python 3.12+** with type hints
- **FastAPI** - Async web framework
- **httpx** - Async HTTP client
- **BeautifulSoup4** - HTML parsing
- **OpenAI Responses API** - Structured AI outputs
- **Pydantic v2** - Data validation
- **Docker** - Containerization

### Project Structure

```
src/
├── main.py              # FastAPI app
├── api/
│   └── routes.py        # Endpoints (simple, ~76 lines)
├── services/
│   └── story_service.py # Business logic
├── scrapers/
│   ├── hn_scraper.py    # Async scraping (~70 lines)
│   └── parser.py        # HTML parsing
├── cache/
│   └── manager.py       # Simple cache (~36 lines)
├── ai/
│   ├── classifier.py    # OpenAI integration
│   └── prompts.py       # AI prompts
└── models/              # Pydantic models
```

### How It Works

```
Request → FastAPI
           ↓
       Check cache
           ↓
    Need pages? → Scrape (async, parallel)
           ↓
       Cache results
           ↓
    AI classify? → OpenAI (parallel, max 3 concurrent)
           ↓
       Response (JSON)
```

## 🎯 Design Principles

### 1. **Simple Cache**

Just a dict wrapper: `get()`, `set()`, `stats()`, `clear()`.

```python
cache.set(1, stories)  # Save
cache.get(1)           # Retrieve
```

**Incremental caching:**
- Request `/1` → scrapes page 1
- Request `/3` → scrapes only pages 2-3 (page 1 cached)

### 2. **No Custom Exceptions**

Uses native httpx exceptions for automatic retry compatibility.

```python
# httpx.TimeoutException → tenacity retries automatically
# httpx.HTTPStatusError → tenacity retries automatically
```

### 3. **True Concurrency**

Scrapes multiple pages in parallel with `asyncio.gather()`.

```python
tasks = [scrape_page(p, client) for p in [1, 2, 3]]
results = await asyncio.gather(*tasks)  # All at once!
```

**Performance:** 3 pages in ~2s instead of ~6s.

### 4. **FastAPI Path Validation**

No custom validators - uses FastAPI native constraints.

```python
@router.get("/{pages}")
async def get_stories(
    pages: int = Path(..., ge=1, le=10),  # Auto-validated!
    ...
):
```

### 5. **OpenAI Responses API**

Native structured outputs - no manual JSON parsing.

```python
response = await client.responses.parse(
    model="gpt-4o-mini",
    input=[...],
    text_format=StoryClassification,  # Pydantic model
)
classification = response.output_parsed  # Already validated!
```

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=src --cov-report=html
```

**28 unit tests** covering models, parser, scraper, and cache.

## 📊 Performance

### Scraping
- Single page: ~0.7s
- Cache hit: ~0.001s
- 3 pages concurrently: ~2s (3x faster than sequential)

### AI Classification
- 5 stories in parallel: ~4s
- Cost per story: ~$0.0001 (gpt-4o-mini)
- Total cost for 5 stories: ~$0.0005

## 🔒 Configuration

Create `.env` file:

```bash
OPENAI_API_KEY=sk-proj-your-key-here
OPENAI_MODEL=gpt-4o-mini
LOG_LEVEL=INFO
```

## 🐛 Error Handling

### Automatic Retries
- HN scraping: 3 attempts with exponential backoff
- OpenAI calls: 3 attempts for rate limits
- 30s timeout protection per request

### HTTP Status Codes
- `200` - Success
- `422` - Invalid input (FastAPI validation)
- `502` - HN scraping failed
- `500` - Server error

## 📈 Logging

All operations logged with metrics:

```
✅ Story 0 classified | Category: database | Confidence: 95%
   Latency: 1.90s | Tokens: 521 | Cost: $0.000100
```

## 🎨 API Docs

When running, visit:
- **Swagger UI:** http://localhost:3000/docs
- **ReDoc:** http://localhost:3000/redoc

## 🏭 Production Features

✅ Fully async architecture
✅ Automatic retry logic
✅ Timeout protection
✅ Health checks
✅ Docker deployment
✅ Environment-based config
✅ Type safety with Pydantic
✅ Incremental caching
✅ Structured logging

## 📝 Code Quality

**Simple, readable, maintainable:**
- Routes: 76 lines (was 165)
- Cache: 36 lines (was 135)
- Scraper: 70 lines (was 174)
- Total reduction: **-56% code** in core files

**Design:**
- KISS principle (Keep It Simple)
- No over-engineering
- Native library features over custom code
- Clear separation of concerns

## 🛠️ Development

```bash
# Run locally
uvicorn src.main:app --reload

# Run tests
pytest tests/ -v

# Check types (if mypy installed)
mypy src/

# Format code (if black installed)
black src/ tests/
```

## 📖 License

MIT License - see LICENSE file for details.

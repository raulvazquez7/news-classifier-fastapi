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

```bash
.
├── src/
│ ├── main.py # FastAPI app entry point
│ ├── api/
│ │ ├── routes.py # API endpoints
│ │ └── dependencies.py # Dependency injection
│ ├── scrapers/
│ │ ├── parser.py # HTML parsing logic
│ │ └── hn_scraper.py # Async scraping with retry
│ ├── cache/
│ │ └── manager.py # Incremental cache manager
│ ├── ai/
│ │ ├── classifier.py # OpenAI integration
│ │ ├── prompts.py # Prompt management
│ │ └── pricing.py # Cost calculation
│ ├── models/
│ │ ├── story.py # Story data models
│ │ ├── classification.py # AI classification models
│ │ └── responses.py # API response models
│ └── exceptions.py # Custom exceptions
├── tests/
│ ├── unit/ # Unit tests
│ │ ├── test_models.py
│ │ ├── test_parser.py
│ │ ├── test_scraper.py
│ │ └── test_cache.py
│ └── fixtures/ # Test data
├── config/
│ └── prompts.yaml # AI prompts configuration
├── docker/
│ └── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

### Data Flow

```bash
User Request
↓
FastAPI (routes.py)
↓
CacheManager (check what's missing)
↓
┌─ If pages missing ─┐
│ Scraper (httpx) │ → Hacker News
│ Parser (BS4) │ → Story objects
│ Cache.add_page() │ → Store
└─────────────────────┘
↓
Cache.get_stories_up_to()
↓
┌─ If /ai/classify ──┐
│ AI Classifier │ → OpenAI Responses API
│ (parallel, max 3) │ → Structured outputs
│ Combine results │ → ClassifiedStory
└─────────────────────┘
↓
FastAPI Response (JSON)
↓
User
```


## 🧠 Key Design Decisions

### 1. **Incremental Caching**

**Problem:** Re-scraping the same pages wastes resources and time.

**Solution:** In-memory cache that tracks which pages are already scraped.

**Example:**
- Request `/1` → scrapes page 1, stores in cache
- Request `/3` → scrapes only pages 2 and 3 (page 1 from cache)
- Request `/2` → everything from cache (no scraping)

**Implementation:** `CacheManager` uses set theory to calculate missing pages.

```python
cached = {1, 2}
needed = {1, 2, 3, 4}
missing = needed - cached  # {3, 4}
```

**Trade-off:** Non-persistent (clears on restart) for simplicity.

### 2. **OpenAI Responses API with Structured Outputs**

**Why Responses API?**
- Native structured outputs (guaranteed schema compliance)
- Better integration with Pydantic models
- No manual JSON parsing required
- Production-ready error handling

**Implementation:**
```python
response = await client.responses.parse(
    model="gpt-4o-mini",
    input=[...],
    text_format=StoryClassification,  # Pydantic model
    temperature=0.3
)
classification = response.output_parsed  # Already validated!
```

**Alternative (not used):** Chat Completions API would require manual JSON parsing and validation.

### 3. **Async Everything**

**Why async?**
- Scraping is I/O bound (waiting for network)
- OpenAI calls are I/O bound (waiting for API response)
- Async allows handling multiple requests concurrently

**Performance:** With async, 3 concurrent requests take ~2s instead of ~6s (3x faster).

### 4. **Parallel Classification with Semaphore**

**Problem:** Classifying 5 stories sequentially takes ~10 seconds.

**Solution:** Parallel execution with semaphore to limit concurrency.

```python
semaphore = asyncio.Semaphore(3)  # Max 3 concurrent requests
```

**Result:** 5 stories in ~4 seconds (2.5x faster).

**Why limit to 3?** Avoid hitting OpenAI rate limits.

### 5. **Retry Logic**

**Implementation:** Tenacity decorator with exponential backoff.

```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((AIRateLimitError, AITimeoutError))
)
```

**When it retries:**
- Rate limit errors (temporary)
- Timeout errors (network glitch)

**When it doesn't:**
- Invalid API key (permanent error)
- Parsing errors (code bug)

### 6. **Prompts in YAML**

**Why separate from code?**
- Easy to iterate without code changes
- Version controlled (Git diff shows changes)
- Non-developers can improve prompts
- A/B testing friendly

**Location:** `config/prompts.yaml`

### 7. **Configuration from Environment**

**All sensitive/environment-specific config in `.env`:**
- `OPENAI_API_KEY` - API credentials
- `OPENAI_MODEL` - Model selection (dev vs prod)
- `LOG_LEVEL` - Logging verbosity

**Benefit:** Same code runs in dev, staging, and production with different configs.

## 🧪 Testing

### Run Tests

```bash
# All tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=src --cov-report=html

# Specific test file
pytest tests/unit/test_models.py -v
```

### Test Coverage

- **Models:** 12 tests (Pydantic validation)
- **Parser:** 6 tests (HTML parsing edge cases)
- **Scraper:** 8 tests (async, retry, errors)
- **Cache:** 13 tests (incremental logic)

**Total:** 39 unit tests

### Manual Testing

```bash
# Local
uvicorn src.main:app --reload
curl http://localhost:8000/1

# Docker
docker compose up -d
curl http://localhost:3000/ai/classify/1
```

## 📊 Performance & Costs

### Scraping Performance

- **Single page:** ~0.7s (network + parsing)
- **With cache hit:** ~0.001s (in-memory)
- **30 stories:** ~30ms parsing time

### AI Classification Performance

- **Sequential (old):** ~10s for 5 stories
- **Parallel (current):** ~4s for 5 stories (2.5x faster)
- **Latency per story:** 1.2s - 2.3s

### OpenAI Costs (gpt-4o-mini)

| Metric | Value |
|--------|-------|
| Input tokens per story | ~470 |
| Output tokens per story | ~50 |
| Cost per story | ~$0.0001 |
| Cost for 5 stories | ~$0.0005 |

**Monthly estimates (1000 requests/day):**
- 5000 stories/day × $0.0001 = **$0.50/day**
- **~$15/month**

## 🔒 Environment Variables

Create a `.env` file (see `.env.example`):

```bash
# OpenAI Configuration
OPENAI_API_KEY=sk-proj-your-key-here
OPENAI_MODEL=gpt-4o-mini

# Application Configuration (optional)
LOG_LEVEL=INFO
HN_BASE_URL=https://news.ycombinator.com
API_HOST=0.0.0.0
API_PORT=3000
```

## 🐛 Error Handling

### Retry Logic

Automatic retries for transient failures:
- **HN scraping:** 3 attempts with exponential backoff (2s, 4s, 8s)
- **OpenAI calls:** 3 attempts for rate limits and timeouts
- **Timeout protection:** 30s max per OpenAI request

### Custom Exceptions

- `HNScraperError` - Scraping failures
- `HNPageNotFoundError` - Page doesn't exist
- `HNTimeoutError` - HN too slow
- `AIClassificationError` - OpenAI errors
- `AIRateLimitError` - Rate limit exceeded
- `AITimeoutError` - OpenAI timeout
- `CacheError` - Cache issues

### HTTP Status Codes

- `200` - Success
- `400` - Invalid input (e.g., pages < 1)
- `500` - Server error (scraping failed, AI error, etc.)

## 📈 Monitoring & Observability

### Logs

All operations are logged with structured information:
```bash
✅ Story 0 classified | Category: database | Confidence: 95% |
Latency: 1.90s | Tokens: 521 (in:472, out:49, cached:0) | Cost: $0.000100
```


**Log levels:**
- `INFO` - Normal operations (scraping, caching, classification)
- `WARNING` - Retries, recoverable errors
- `ERROR` - Failures after retries

### Metrics Tracked

- Scraping latency per page
- Cache hit/miss rate
- Classification latency per story
- Token usage (input, output, cached)
- Estimated costs per request
- Success/failure rates

## 🎨 API Documentation

Interactive API documentation available when running:
- **Swagger UI:** http://localhost:3000/docs
- **ReDoc:** http://localhost:3000/redoc

## 🏭 Production Considerations

### Implemented (Production-Ready)

✅ **Async architecture** - High concurrency support  
✅ **Retry logic** - Automatic recovery from transient failures  
✅ **Timeout protection** - Prevents hanging requests  
✅ **Error handling** - Granular exceptions with proper HTTP codes  
✅ **Logging** - Structured logs with metrics  
✅ **Docker deployment** - Containerized application  
✅ **Health checks** - Kubernetes/load balancer ready  
✅ **Environment config** - 12-factor app compliance  
✅ **Type safety** - Full Pydantic validation  
✅ **Incremental caching** - Performance optimization  

### Not Implemented (Would Add for Large-Scale Production)

#### Persistence & Scalability
- **Distributed cache** (Redis/Memcached) - Current cache is in-memory per instance
- **Database** for storing classifications - Enable historical analysis
- **Horizontal scaling** - Load balancer + multiple instances
- **CDN** - Cache responses at edge for popular pages

#### Reliability & Monitoring
- **Circuit breaker** - Stop calling failing services temporarily
- **Rate limiting** - Protect API from abuse (per IP/API key)
- **Metrics pipeline** - Prometheus + Grafana for dashboards
- **Alerting** - PagerDuty/Opsgenie for critical failures
- **Distributed tracing** - OpenTelemetry for request flows

#### Security
- **Authentication** - API keys or OAuth
- **HTTPS** - TLS certificates
- **CORS** - Configured for specific origins (currently allows all)
- **Input sanitization** - Additional validation layers
- **Secrets management** - Vault/AWS Secrets Manager (not .env)

#### Advanced Features
- **Batch classification** - OpenAI Batch API for cost savings
- **Classification caching** - Don't re-classify same stories
- **Webhook notifications** - Real-time updates for new stories
- **GraphQL API** - Flexible querying alternative
- **WebSocket** - Real-time streaming of classifications

#### DevOps
- **CI/CD pipeline** - GitHub Actions / GitLab CI
- **Automated testing** - Integration tests in CI
- **Staging environment** - Pre-production testing
- **Blue-green deployments** - Zero-downtime updates
- **Infrastructure as Code** - Terraform/Pulumi

## 🧪 Development Workflow

### Run Tests

```bash
# All tests with coverage
pytest tests/ -v --cov=src --cov-report=html

# Specific test categories
pytest tests/unit/ -v
pytest tests/integration/ -v

# Watch mode (during development)
pytest-watch
```

### Code Quality

```bash
# Format code
black .

# Lint
ruff check .

# Type checking (if using mypy)
mypy src/
```

### Git Workflow

This project uses conventional commits:

```bash
git commit -m "feat: add new feature"
git commit -m "fix: resolve bug"
git commit -m "docs: update README"
git commit -m "test: add unit tests"
git commit -m "refactor: improve code structure"
```

## 🔧 Troubleshooting

### Docker Issues

**Problem:** Container won't start
```bash
# Check logs
docker compose logs api

# Rebuild without cache
docker compose build --no-cache
```

**Problem:** Port 3000 already in use
```bash
# Change port in docker-compose.yml
ports:
  - "3001:3000"  # Use 3001 externally
```

### API Issues

**Problem:** OpenAI errors
```bash
# Verify .env file
cat .env | grep OPENAI

# Check API key is valid
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

**Problem:** Slow responses
- Check network connection
- Review logs for retry attempts
- Consider reducing parallel requests (semaphore 3 → 2)

## 📝 Technical Decisions Log

### Why BeautifulSoup over Scrapy?
- Lighter weight for simple scraping
- No need for Scrapy's complexity
- Better for single-site scraping

### Why In-Memory Cache over Redis?
- Project requirement: non-persistent cache
- Simpler deployment (no external dependencies)
- Sufficient for single-instance deployment

### Why Responses API over Chat Completions?
- Native structured outputs (guaranteed schema)
- Better Pydantic integration
- Reduced parsing code and bugs

### Why Async over Sync?
- Better performance for I/O bound operations
- Modern Python best practice
- FastAPI is built for async

### Why Semaphore (3) for Parallelization?
- Balance between speed and rate limits
- Avoids overwhelming OpenAI API
- 2.5x faster than sequential
- Empirically tested (works reliably)

### Why YAML for Prompts?
- Separate concerns (code vs configuration)
- Easy iteration without code changes
- Version controlled
- Product owners can modify

## 🚢 Deployment

### Docker Compose (Single Server)

```bash
# Production deployment
docker compose up -d

# View logs
docker compose logs -f

# Update to new version
git pull
docker compose build
docker compose up -d
```

### Kubernetes (Multi-Server)

Example deployment:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: hn-api-ai
spec:
  replicas: 3
  selector:
    matchLabels:
      app: hn-api-ai
  template:
    spec:
      containers:
      - name: api
        image: your-registry/hn-api-ai:latest
        ports:
        - containerPort: 3000
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: openai-secret
              key: api-key
        livenessProbe:
          httpGet:
            path: /health
            port: 3000
          initialDelaySeconds: 30
          periodSeconds: 10
```

### Google Cloud Run (Serverless)

```bash
# Build and push
docker build -t gcr.io/your-project/hn-api-ai .
docker push gcr.io/your-project/hn-api-ai

# Deploy
gcloud run deploy hn-api-ai \
  --image gcr.io/your-project/hn-api-ai \
  --platform managed \
  --set-env-vars OPENAI_API_KEY=$OPENAI_API_KEY,OPENAI_MODEL=gpt-4o-mini
```

**Note:** Cache will be per-instance. For shared cache, add Redis.

## 📚 API Examples

### Python

```python
import httpx

# Get stories
response = httpx.get("http://localhost:3000/2")
stories = response.json()
print(f"Got {len(stories)} stories")

# Classify with AI
response = httpx.get("http://localhost:3000/ai/classify/1")
data = response.json()
for item in data["items"]:
    print(f"{item['title']} → {item['category']}")
```

### JavaScript

```javascript
// Fetch stories
const response = await fetch('http://localhost:3000/1');
const stories = await response.json();
console.log(`Got ${stories.length} stories`);

// Classify with AI
const classifyResponse = await fetch('http://localhost:3000/ai/classify/1');
const data = await classifyResponse.json();
data.items.forEach(item => {
    console.log(`${item.title} → ${item.category}`);
});
```

### cURL

```bash
# Get and format
curl -s http://localhost:3000/1 | jq '.[0]'

# Count stories
curl -s http://localhost:3000/2 | jq '. | length'
# Output: 60

# Filter by category
curl -s http://localhost:3000/ai/classify/1 | \
  jq '.items[] | select(.category == "ai-ml")'
```

## 🤝 Contributing

### Local Setup

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Install dev dependencies (`pip install -r requirements.txt`)
4. Make changes
5. Run tests (`pytest tests/ -v`)
6. Format code (`black .`)
7. Commit (`git commit -m 'feat: add amazing feature'`)
8. Push (`git push origin feature/amazing-feature`)
9. Open Pull Request

### Code Standards

- **Type hints** - All functions must have type annotations
- **Docstrings** - All public functions must be documented
- **Tests** - New features must include tests
- **Formatting** - Use black with line-length=100
- **Linting** - Pass ruff checks

## 📄 License

This project is for educational/technical assessment purposes.

## 📞 Support

For questions or issues:
- Open an issue on GitHub
- Check `/docs` endpoint for API documentation
- Review logs: `docker compose logs -f`

---

**Built with ❤️ using FastAPI, OpenAI, and modern Python best practices.**
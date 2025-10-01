# Hacker News API Test (with AI)

## Goal

Develop an API that scrapes the Hacker News website (https://news.ycombinator.com/) and integrates OpenAI for intelligent content classification (do not use the official Hacker News API).

## API Endpoints

The API will have the following endpoints:

- **`/`** → Behaves the same as `/1`
- **`/{number}`** → Retrieves the specified number of pages from Hacker News
  - Example: `/1` → 30 stories, `/2` → 60 stories (pages 1+2), `/3` → 90 stories, and so on
- **`/ai/classify/{pages}`** → Fetches stories from the `{pages}` result and classifies them with OpenAI

## Behavior

- The API must be **fully asynchronous** 
- Development should follow a **test-driven approach** to ensure correctness
- Once core functionality is implemented, add an **in-memory caching mechanism**:
  - If `/1` is fetched and then `/2`, only page 2 is retrieved
  - If `/2` is fetched and then `/4`, only pages 3 and 4 are retrieved
- Cache must not persist after restart
- The application must be **dockerized** and runnable with **Docker Compose**

## Key Requirements

- **Scraping:** You must scrape the Hacker News **HTML** (https://news.ycombinator.com/) - not the official API
- **Cache:** Ensure that cache is **non-persistent** across app restarts
- **Git:** Maintain all code in a Git repository with meaningful, structured commits
- **Clarity:** Use clear and descriptive naming. Add comments if something might be hard to understand later
- **README:** Provide instructions in the project's `README.md` on how to run the API and the tests

## Expected Output

### `/1`

```json
[
  {
    "title": "The title of the first news article",
    "url": "https://some-url.com/for/this/article",
    "points": 90,
    "sent_by": "pepito",
    "published": "2 hours ago",
    "comments": 24
  }
]
```

### `/ai/classify/1`

```json
{
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
```

## AI Classification

### Input to the model

For each news item, the following fields are passed into the prompt:

```json
{
  "index": 0,
  "title": "Some HN story",
  "url": "https://example.com",
  "points": 100,
  "comments": 25
}
```

Only the **first 5 items** are classified (simplification to keep development fast).

### Model Configuration

- **Model:** Must use `gpt-4o-mini` (mandatory)
- **Endpoint:** Must use OpenAI's **Responses API** → [docs](https://platform.openai.com/docs/api-reference/responses)
- **Output Schema:**
  - **category**:  Must be one of the following fixed categories: `ai-ml`, `programming`, `security`, `devops`, `hardware`, `science`, `business`, `web`, `mobile`, `database`, `math`, `history`, `politics`, `ask-hn`, `show-hn`, `launch-hn`, `job`, `meta`, `other`
  - **intent**: Must be one of the following fixed intents: `news`, `discussion`, `tutorial`, `research`, `opinion`, `announcement`, `ask_hn`, `show_hn`, `launch_hn`, `job`
  - **tags**: list of 1–6 strings
  - **confidence**: integer 0–100
  - **reason_brief**: short explanation (≤160 chars)

## Running the API

Assuming Docker Compose is set up and the app runs on port 3000:

```bash
docker compose up -d
```

Check output:

```bash
curl -s localhost:3000 | jq
curl -s localhost:3000/2 | jq | wc -l   # should be ~60
curl -s localhost:3000/ai/classify/1 | jq
```

---

Feel free to contact us by email if you have any doubt or comment about this challenge. Once you're happy with your solution let us know and invite us to your repo which we kindly ask you to keep it private.

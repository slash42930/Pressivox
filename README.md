# Pressivox

Pressivox is a FastAPI backend for Tavily-powered web search, extraction, crawl, map, and research workflows.

## What this project does

- Runs Tavily search with filtering and ranking
- Supports extraction-aware research summaries
- Stores search and extraction history in SQLite
- Exposes Tavily map/crawl/research-task endpoints for agent-style workflows
- Serves static UI files from `app/static`

## Tavily alignment

The API is designed to match common Tavily CLI and Agent Skills patterns:

- Search style options: depth, topic, time range, include/exclude domains
- Research task workflow: submit task, then poll by task id
- Map/crawl support for site exploration and content gathering
- Structured output that works well for static frontend apps

Relevant docs:

- Tavily CLI: https://docs.tavily.com/documentation/tavily-cli
- Tavily Agent Skills: https://docs.tavily.com/documentation/agent-skills#usage

## Setup

```bash
python -m venv .venv
. .venv/Scripts/activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

## Environment variables

- `TAVILY_API_KEY`: Tavily API key
- `TAVILY_BASE_URL`: default `https://api.tavily.com`
- `DATABASE_URL`: SQLAlchemy connection string
- `API_V1_PREFIX`: default `/api/v1`
- `HTTP_TIMEOUT_SECONDS`: outbound HTTP timeout
- `CORS_ALLOW_ORIGINS`: comma-separated allowed origins (use `*` for local development)

## Security and production defaults

- Keep `.env` local only. Never commit real API keys.
- For production, set `APP_ENV=production` and a specific `CORS_ALLOW_ORIGINS` value, for example:
  - `CORS_ALLOW_ORIGINS=https://pressivox.app,https://www.pressivox.app`
- Rotate `TAVILY_API_KEY` immediately if it was ever exposed.

## Deploy to the web

- Detailed guide: see `DEPLOYMENT.md`
- Security guidance: see `SECURITY.md`

### Docker

```bash
docker build -t pressivox .
docker run -p 8000:8000 --env-file .env pressivox
```

Then open:

- `http://127.0.0.1:8000/static/web-search-backend-ui-mod-1.html`

### Cloud deployment (Render/Railway/Fly)

- Runtime/start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Set environment variables from `.env.example`
- Configure `CORS_ALLOW_ORIGINS` to your frontend domain(s)

## Main endpoints

- `GET /api/v1/health`
- `POST /api/v1/search`
- `GET /api/v1/search/history`
- `POST /api/v1/research`
- `POST /api/v1/extract`
- `GET /api/v1/extract/history`
- `POST /api/v1/map`
- `POST /api/v1/crawl`
- `POST /api/v1/research/tasks`
- `GET /api/v1/research/tasks/{task_id}`

## Static UI

- `http://127.0.0.1:8000/static/web-search-backend-ui-mod-1.html`
- `http://127.0.0.1:8000/static/web-search-backend-ui.html`

The `mod-1` UI is the richer workspace view and is recommended for research workflows.

## Example research request

```json
{
  "query": "AI coding assistants",
  "topic": "general",
  "max_results": 8,
  "summarize": true,
  "extract_top_results": true,
  "search_depth": "advanced",
  "include_answer": true,
  "include_raw_content": true,
  "time_range": "month"
}
```

# Pressivox Deployment Guide

## 1. Prepare Environment

- Copy `.env.example` to `.env`
- Set `TAVILY_API_KEY`
- For production, set explicit origins:
  - `CORS_ALLOW_ORIGINS=https://pressivox.app,https://www.pressivox.app`

## 2. Local Docker Build and Run

```bash
docker build -t pressivox .
docker run -p 8000:8000 --env-file .env pressivox
```

## 3. Health Verification

- Health endpoint: `GET /api/v1/health`
- UI endpoint: `/static/web-search-backend-ui-mod-1.html`
- Run test suite: `pytest -q`
- Compile check: `python -m compileall app`

## 4. Cloud Deployment (Render/Railway/Fly)

- Start command:
  - `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Add all environment variables from `.env.example`
- Configure CORS origins to deployed frontend domains

## 5. Frontend Hosting

- Host `app/static` as static assets (Cloudflare Pages/Netlify)
- Set UI API base URL to deployed backend URL

## 6. Post-Deploy Checks

- Confirm CORS in browser network panel
- Verify search, research, extract, map, crawl endpoints
- Monitor logs for 4xx/5xx spikes

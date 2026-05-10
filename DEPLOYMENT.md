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

## 4a. Vercel and Serverless Database Requirement

- Do not use SQLite for deployed serverless environments.
- Configure `DATABASE_URL` to a persistent Postgres instance (for example Neon, Supabase, Railway Postgres, or Render Postgres).
- Reason: SQLite on serverless instances is ephemeral and can cause users to register on one request path/device and fail login from another device with invalid credentials.

## 4b. Free Setup Option (Neon Postgres)

1. Create a free Neon project:
  - Open https://neon.tech and sign in.
  - Create a new project and copy the connection string.
2. Use pooled SSL URL format for serverless apps:
  - Example:
    - `postgresql+psycopg2://USER:PASSWORD@ep-xxxx-pooler.us-east-1.aws.neon.tech/DBNAME?sslmode=require`
3. Add env variables in Vercel:
  - `DATABASE_URL=<your_neon_connection_string>`
  - `APP_ENV=production`
  - `APP_DEBUG=false`
  - `AUTH_SECRET_KEY=<long-random-secret>`
  - `CORS_ALLOW_ORIGINS=https://your-frontend-domain.com`
4. Redeploy your backend.
5. Verify persistence:
  - Register an account on PC.
  - Log in from phone with the same username/password.

Optional CLI path (if Vercel CLI is installed):

```bash
vercel env add DATABASE_URL production
vercel env add APP_ENV production
vercel env add APP_DEBUG production
vercel env add AUTH_SECRET_KEY production
vercel env add CORS_ALLOW_ORIGINS production
vercel --prod
```

## 5. Frontend Hosting

- Host `app/static` as static assets (Cloudflare Pages/Netlify)
- Set UI API base URL to deployed backend URL

## 6. Post-Deploy Checks

- Confirm CORS in browser network panel
- Verify search, research, extract, map, crawl endpoints
- Monitor logs for 4xx/5xx spikes

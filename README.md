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
- `AUTH_SECRET_KEY`: secret used to sign JWT access tokens
- `AUTH_ALGORITHM`: JWT signing algorithm (default `HS256`)
- `AUTH_ACCESS_TOKEN_EXPIRE_MINUTES`: access token validity window
- `AUTH_REFRESH_TOKEN_EXPIRE_DAYS`: refresh token validity window

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
- For free persistent database hosting, use Neon Postgres free tier and set `DATABASE_URL` to the Neon connection string (`sslmode=require`).
- Do not use SQLite in serverless production deployments.

## Main endpoints

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `GET /api/v1/auth/me`
- `GET /api/v1/auth/admin/check`
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

All endpoints except `GET /api/v1/health` and the `auth` routes require a Bearer token in the `Authorization` header.
`/api/v1/map`, `/api/v1/crawl`, and `/api/v1/research/tasks*` are admin-only routes.

## React frontend

A full React + TypeScript frontend lives in `frontend/`. It uses Vite, Tailwind CSS, Framer Motion, Lenis, and Lucide React.

### Development

Start the backend first, then the frontend dev server in a second terminal:

```bash
# Terminal 1 — backend
uvicorn app.main:app --reload

# Terminal 2 — frontend
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. All `/api/...` requests proxy to `http://localhost:8000` automatically.

### Production build

```bash
cd frontend
npm run build        # output: frontend/dist/
```

Serve `frontend/dist/` as static files from any web host, or configure the FastAPI app to serve them directly.

### Frontend stack

| Package | Version | Purpose |
|---|---|---|
| React | 18.3 | UI framework |
| TypeScript | 5.5 | Type safety |
| Vite | 5.4 | Build tool + dev proxy |
| Tailwind CSS | 3.4 | Utility-first styling |
| Framer Motion | 11 | Animations and transitions |
| Lenis | 1.3 | Smooth scroll |
| Lucide React | 0.427 | Icons |
| @radix-ui/* | latest | Accessible UI primitives (tooltip, dialog, tabs, switch, dropdown, etc.) |
| @fontsource/inter | 5.x | Inter variable font (body) |
| @fontsource/space-grotesk | 5.x | Space Grotesk font (headings) |
| clsx + tailwind-merge | latest | Conditional class merging (cn utility) |
| class-variance-authority | latest | Component variant API |

### Design system

The UI is built as a premium dark AI/SaaS product with:

- **Color palette**: deep `slate-950` base, cyan-to-fuchsia gradient accents, amber for extract
- **Typography**: Space Grotesk (`font-display`) for headings, Inter for body text
- **Glass cards**: `bg-slate-900/60 border border-white/[0.06] backdrop-blur-sm`
- **Spotlight cards**: Mouse-tracking radial highlight effect on interactive cards
- **Glassmorphism navbar**: Sticky top bar with session stats and animated active pill
- **Ambient background**: Floating gradient orbs + subtle mesh grid overlay
- **Animations**: framer-motion fade-up entry, AnimatePresence for section transitions, collapsible filter panels

### New files in `frontend/src/`

| File | Description |
|---|---|
| `lib/utils.ts` | `cn()` helper combining clsx + tailwind-merge |
| `components/ui/Button.tsx` | CVA button: default/secondary/ghost/gradient/fuchsia/amber variants |
| `components/ui/Input.tsx` | Premium input with icon/suffix and glow-on-focus |
| `components/ui/Card.tsx` | Glass card + `StatCard` component |
| `components/ui/Badge.tsx` | CVA badge: cyan/fuchsia/amber/emerald/gradient variants |
| `components/ui/Skeleton.tsx` | Shimmer loading skeleton |
| `components/ui/Textarea.tsx` | Premium textarea with glow focus |
| `components/ui/Label.tsx` | Form label primitive |
| `components/ui/Separator.tsx` | Horizontal/vertical divider |
| `components/effects/BorderBeam.tsx` | Magic UI border beam + `GlowBorder` + `ShimmerButton` |
| `components/effects/AnimatedBackground.tsx` | Ambient orbs + grid + `SpotlightCard` + `RevealSection` |
| `components/effects/TypewriterText.tsx` | Typewriter, `WordReveal`, `GradientText` components |
| `components/effects/BentoGrid.tsx` | Magic UI-style bento grid layout |
| `components/layout/Navbar.tsx` | Sticky glassmorphism navbar with animated active pill |

### Tabs

| Tab | Description |
|---|---|
| Dashboard | Quick search/research chips, session stats, top weekly headlines |
| Search | Full search form, result cards grouped by confidence, compare panel |
| Research | Structured research with key-point summary, markdown export |
| Extract | Pull and read full page content with important passages |
| Histories | Reload recent search and extract history from the backend |
| Info | Product guide and query analyzer field reference |

## Legacy static UI

The original single-file UI is preserved at `app/static/web-search-backend-ui-mod-1.html` and is still served by the backend for reference:

- `http://127.0.0.1:8000/static/web-search-backend-ui-mod-1.html`

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

## Research response notes

`POST /api/v1/research` keeps existing fields (`summary`, `summary_points`, `summary_markdown`, `results`) and now also returns optional structured sections under `sections`:

- `concise_summary`
- `key_findings`
- `detailed_analysis`
- `sources`
- `limitations`
- `suggested_follow_up_queries`
- `confidence`

This preserves backward compatibility while enabling richer frontend rendering.

## Tavily task lifecycle notes

`GET /api/v1/research/tasks/{task_id}` now returns a normalized task envelope for safer polling behavior:

- `task_id`
- `status` (`queued`, `running`, `completed`, `failed`, or `unknown`)
- `is_terminal`
- `result_count`
- `result_sources`
- `error_message`

Network failures and timeouts are mapped to stable API errors (`502`/`504`) without leaking raw internals.

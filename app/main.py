from pathlib import Path

from fastapi import Depends, FastAPI, Request, Response
from fastapi.exceptions import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.deps import require_roles
from app.api.routes.auth import router as auth_router
from app.api.routes.extract import router as extract_router
from app.api.routes.health import router as health_router
from app.api.routes.research import router as research_router
from app.api.routes.search import router as search_router
from app.api.routes.tavily_crawl import router as tavily_crawl_router
from app.api.routes.tavily_map import router as tavily_map_router
from app.api.routes.tavily_research import router as tavily_research_router
from app.core.config import get_settings
from app.core.database import Base, engine
from app.core.limiter import limiter
from app.core.startup_migrations import run_startup_schema_patches

settings = get_settings()
settings.validate_security()
Base.metadata.create_all(bind=engine)
run_startup_schema_patches(engine)

cors_origins = settings.cors_origins_list
allow_credentials = "*" not in cors_origins

BASE_DIR = Path(__file__).resolve().parent
SPA_DIR = BASE_DIR / "static" / "spa"
NOT_FOUND_DETAIL = "Not Found"

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Backend for real-time web and news search using Tavily Search API.",
    # Hide detailed error info in non-dev environments
    openapi_url="/openapi.json" if settings.app_env == "development" else None,
    docs_url="/docs" if settings.app_env == "development" else None,
    redoc_url="/redoc" if settings.app_env == "development" else None,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next) -> Response:
    # Initialize view_rate_limit so slowapi's _inject_headers never raises AttributeError
    # when _check_request_limit finds no matching limits for the endpoint.
    request.state.view_rate_limit = None
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "0"  # modern browsers use CSP instead
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    if settings.app_env == "production":
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
    return response

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

app.include_router(health_router, prefix=settings.api_v1_prefix)
app.include_router(auth_router, prefix=settings.api_v1_prefix)
app.include_router(search_router, prefix=settings.api_v1_prefix)
app.include_router(extract_router, prefix=settings.api_v1_prefix)
app.include_router(research_router, prefix=settings.api_v1_prefix)
app.include_router(tavily_map_router, prefix=settings.api_v1_prefix, dependencies=[Depends(require_roles("admin"))])
app.include_router(tavily_crawl_router, prefix=settings.api_v1_prefix, dependencies=[Depends(require_roles("admin"))])
app.include_router(tavily_research_router, prefix=settings.api_v1_prefix, dependencies=[Depends(require_roles("admin"))])


@app.get("/", include_in_schema=False, responses={404: {"description": "Not Found"}})
async def serve_spa_root() -> FileResponse:
    index_path = SPA_DIR / "index.html"
    if index_path.is_file():
        return FileResponse(index_path)
    raise HTTPException(status_code=404, detail=NOT_FOUND_DETAIL)


@app.get("/{full_path:path}", include_in_schema=False, responses={404: {"description": "Not Found"}})
async def serve_spa_fallback(full_path: str) -> FileResponse:
    if full_path.startswith("api/") or full_path.startswith("static/"):
        raise HTTPException(status_code=404, detail=NOT_FOUND_DETAIL)

    candidate = SPA_DIR / full_path
    if candidate.is_file():
        return FileResponse(candidate)

    index_path = SPA_DIR / "index.html"
    if index_path.is_file():
        return FileResponse(index_path)

    raise HTTPException(status_code=404, detail=NOT_FOUND_DETAIL)
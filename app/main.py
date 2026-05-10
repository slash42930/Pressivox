from pathlib import Path

from fastapi import Depends, FastAPI, Request, Response
from fastapi.exceptions import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from sqlalchemy import inspect, text

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

settings = get_settings()
settings.validate_security()
Base.metadata.create_all(bind=engine)


def ensure_search_history_columns() -> None:
    """Add search_history columns for existing databases if missing."""
    try:
        inspector = inspect(engine)
        if "search_history" not in inspector.get_table_names():
            return

        columns = {column["name"] for column in inspector.get_columns("search_history")}
        column_patches = {
            "user_id": "ALTER TABLE search_history ADD COLUMN user_id INTEGER",
            "session_id": "ALTER TABLE search_history ADD COLUMN session_id VARCHAR(128)",
            "ambiguous": "ALTER TABLE search_history ADD COLUMN ambiguous BOOLEAN DEFAULT 0",
            "selected_source_count": "ALTER TABLE search_history ADD COLUMN selected_source_count INTEGER DEFAULT 0",
            "meaning_group_count": "ALTER TABLE search_history ADD COLUMN meaning_group_count INTEGER DEFAULT 0",
            "has_summary": "ALTER TABLE search_history ADD COLUMN has_summary BOOLEAN DEFAULT 0",
        }

        missing = [statement for name, statement in column_patches.items() if name not in columns]
        if not missing:
            return

        with engine.begin() as connection:
            for statement in missing:
                connection.execute(text(statement))
    except Exception:
        # Non-fatal schema upgrade path for local dev databases.
        pass


def ensure_user_columns() -> None:
    """Add users table columns for existing databases if missing."""
    try:
        inspector = inspect(engine)
        if "users" not in inspector.get_table_names():
            return

        columns = {column["name"] for column in inspector.get_columns("users")}
        missing = []
        if "role" not in columns:
            missing.append("ALTER TABLE users ADD COLUMN role VARCHAR(32) DEFAULT 'user'")

        with engine.begin() as connection:
            for statement in missing:
                connection.execute(text(statement))
            connection.execute(text("UPDATE users SET role='user' WHERE role IS NULL"))
            connection.execute(
                text(
                    "UPDATE users SET role='admin' "
                    "WHERE id=(SELECT MIN(id) FROM users) AND role='user'"
                )
            )
    except Exception:
        pass


def ensure_extracted_document_columns() -> None:
    """Add extracted_documents columns for existing databases if missing."""
    try:
        inspector = inspect(engine)
        if "extracted_documents" not in inspector.get_table_names():
            return

        columns = {column["name"] for column in inspector.get_columns("extracted_documents")}
        missing = []
        if "user_id" not in columns:
            missing.append("ALTER TABLE extracted_documents ADD COLUMN user_id INTEGER")

        if not missing:
            return

        with engine.begin() as connection:
            for statement in missing:
                connection.execute(text(statement))
    except Exception:
        pass


def backfill_history_user_ids() -> None:
    """Associate legacy history rows to the first user if exactly one user exists."""
    try:
        with engine.begin() as connection:
            user_count = connection.execute(text("SELECT COUNT(*) FROM users")).scalar()
            if user_count != 1:
                return

            first_user_id = connection.execute(text("SELECT MIN(id) FROM users")).scalar()
            if first_user_id is None:
                return

            connection.execute(
                text("UPDATE search_history SET user_id=:uid WHERE user_id IS NULL"),
                {"uid": first_user_id},
            )
            connection.execute(
                text("UPDATE extracted_documents SET user_id=:uid WHERE user_id IS NULL"),
                {"uid": first_user_id},
            )
    except Exception:
        pass


ensure_search_history_columns()
ensure_user_columns()
ensure_extracted_document_columns()
backfill_history_user_ids()

cors_origins = settings.cors_origins_list
allow_credentials = "*" not in cors_origins

BASE_DIR = Path(__file__).resolve().parent
SPA_DIR = BASE_DIR / "static" / "spa"

limiter = Limiter(key_func=get_remote_address, default_limits=[])

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
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next) -> Response:
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


@app.get("/", include_in_schema=False)
async def serve_spa_root() -> FileResponse:
    index_path = SPA_DIR / "index.html"
    if index_path.is_file():
        return FileResponse(index_path)
    raise HTTPException(status_code=404, detail="Not Found")


@app.get("/{full_path:path}", include_in_schema=False)
async def serve_spa_fallback(full_path: str) -> FileResponse:
    if full_path.startswith("api/") or full_path.startswith("static/"):
        raise HTTPException(status_code=404, detail="Not Found")

    candidate = SPA_DIR / full_path
    if candidate.is_file():
        return FileResponse(candidate)

    index_path = SPA_DIR / "index.html"
    if index_path.is_file():
        return FileResponse(index_path)

    raise HTTPException(status_code=404, detail="Not Found")
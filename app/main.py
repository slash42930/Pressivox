from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import inspect, text

from app.api.routes.extract import router as extract_router
from app.api.routes.health import router as health_router
from app.api.routes.research import router as research_router
from app.api.routes.search import router as search_router
from app.api.routes.tavily_crawl import router as tavily_crawl_router
from app.api.routes.tavily_map import router as tavily_map_router
from app.api.routes.tavily_research import router as tavily_research_router
from app.core.config import get_settings
from app.core.database import Base, engine
from app.models.extracted_document import ExtractedDocument
from app.models.search import SearchHistory

settings = get_settings()
Base.metadata.create_all(bind=engine)


def ensure_search_history_columns() -> None:
    """Add search_history columns for existing databases if missing."""
    try:
        inspector = inspect(engine)
        if "search_history" not in inspector.get_table_names():
            return

        columns = {column["name"] for column in inspector.get_columns("search_history")}
        column_patches = {
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


ensure_search_history_columns()

cors_origins = settings.cors_origins_list
allow_credentials = "*" not in cors_origins

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Backend for real-time web and news search using Tavily Search API.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

app.include_router(health_router, prefix=settings.api_v1_prefix)
app.include_router(search_router, prefix=settings.api_v1_prefix)
app.include_router(extract_router, prefix=settings.api_v1_prefix)
app.include_router(research_router, prefix=settings.api_v1_prefix)
app.include_router(tavily_map_router, prefix=settings.api_v1_prefix)
app.include_router(tavily_crawl_router, prefix=settings.api_v1_prefix)
app.include_router(tavily_research_router, prefix=settings.api_v1_prefix)
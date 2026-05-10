"""Vercel Python function entrypoint for the FastAPI app."""

from __future__ import annotations

from typing import Callable

from app.main import app as fastapi_app


class PathCompatibilityMiddleware:
    """Normalize request paths so /api/v1 works consistently on Vercel."""

    def __init__(self, app: Callable):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope.get("type") == "http":
            path = scope.get("path", "")
            if path.startswith("/v1/") or path == "/v1":
                scope = dict(scope)
                scope["path"] = f"/api{path}"
            elif path == "/health":
                scope = dict(scope)
                scope["path"] = "/api/v1/health"
        await self.app(scope, receive, send)


app = PathCompatibilityMiddleware(fastapi_app)

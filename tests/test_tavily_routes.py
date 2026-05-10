import asyncio
import httpx
from fastapi.testclient import TestClient

from app.core.security import create_access_token, hash_password
from app.core.database import SessionLocal
from app.main import app
from app.models.user import User
from app.services.tavily_service import ProviderResponseError


client = TestClient(app)


def _ensure_admin_headers() -> dict[str, str]:
    username = "tavily-admin"

    with SessionLocal() as db:
        user = db.query(User).filter(User.username == username).first()
        if user is None:
            user = User(
                username=username,
                password_hash=hash_password("test-pass-123"),
                role="admin",
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        elif user.role != "admin":
            user.role = "admin"
            db.commit()

        access_token, _ = create_access_token(str(user.id))

    return {"Authorization": f"Bearer {access_token}"}


def test_map_returns_502_on_network_error(monkeypatch) -> None:
    async def fake_map(self, **kwargs):
        await asyncio.sleep(0)
        request = httpx.Request("POST", "https://api.tavily.com/map")
        raise httpx.ConnectError("network down", request=request)

    monkeypatch.setattr("app.api.routes.tavily_map.TavilyService.map", fake_map)

    response = client.post(
        "/api/v1/map",
        json={
            "url": "https://example.com",
            "max_depth": 1,
            "max_results": 10,
            "include_subdomains": True,
        },
        headers=_ensure_admin_headers(),
    )

    assert response.status_code == 502
    assert "Tavily network error" in response.json()["detail"]


def test_crawl_returns_400_on_validation_error(monkeypatch) -> None:
    async def fake_crawl(self, **kwargs):
        raise ValueError("urls are required")

    monkeypatch.setattr("app.api.routes.tavily_crawl.TavilyService.crawl", fake_crawl)

    response = client.post(
        "/api/v1/crawl",
        json={
            "urls": ["https://example.com"],
            "max_pages": 10,
            "include_raw_content": False,
            "include_images": False,
        },
        headers=_ensure_admin_headers(),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "urls are required"


def test_research_task_404_passthrough(monkeypatch) -> None:
    async def fake_get_task(self, task_id: str):
        await asyncio.sleep(0)
        request = httpx.Request("GET", f"https://api.tavily.com/research/tasks/{task_id}")
        response = httpx.Response(404, request=request)
        raise httpx.HTTPStatusError("not found", request=request, response=response)

    monkeypatch.setattr(
        "app.api.routes.tavily_research.TavilyService.get_research_task",
        fake_get_task,
    )

    response = client.get(
        "/api/v1/research/tasks/missing-task",
        headers=_ensure_admin_headers(),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Task missing-task not found."


def test_research_task_timeout_maps_to_504(monkeypatch) -> None:
    async def fake_get_task(self, task_id: str):
        await asyncio.sleep(0)
        request = httpx.Request("GET", f"https://api.tavily.com/research/tasks/{task_id}")
        raise httpx.ReadTimeout("timed out", request=request)

    monkeypatch.setattr(
        "app.api.routes.tavily_research.TavilyService.get_research_task",
        fake_get_task,
    )

    response = client.get(
        "/api/v1/research/tasks/slow-task",
        headers=_ensure_admin_headers(),
    )

    assert response.status_code == 504
    assert "timed out" in response.json()["detail"].lower()


def test_research_task_invalid_provider_payload_maps_to_502(monkeypatch) -> None:
    async def fake_get_task(self, task_id: str):
        await asyncio.sleep(0)
        raise ProviderResponseError("invalid response")

    monkeypatch.setattr(
        "app.api.routes.tavily_research.TavilyService.get_research_task",
        fake_get_task,
    )

    response = client.get(
        "/api/v1/research/tasks/bad-task",
        headers=_ensure_admin_headers(),
    )

    assert response.status_code == 502
    assert "invalid response" in response.json()["detail"].lower()

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_static_mod_ui_is_served() -> None:
    response = client.get("/static/web-search-backend-ui-mod-1.html")

    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert "Advanced Research" in response.text
    assert "Copy Markdown" in response.text
    assert "Top News of the Week" in response.text
    assert "Top 3 Romanian" in response.text

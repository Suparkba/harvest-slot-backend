def test_health(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["message"] == "success"
    assert body["error"] is None
    assert body["data"]["status"] == "ok"


def test_health_db_response_shape_without_real_db():
    from fastapi.testclient import TestClient

    from backend.app.main import app

    client = TestClient(app)
    response = client.get("/api/v1/health/db")
    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"data", "message", "error"}
    assert "database" in body["data"]

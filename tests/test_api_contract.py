def test_products_contract(client):
    response = client.get("/api/v1/products")
    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"data", "message", "error"}
    assert body["message"] == "success"
    assert isinstance(body["data"], list)


def test_product_slots_contract(client):
    response = client.get("/api/v1/products/1/slots")
    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"data", "message", "error"}
    assert body["data"][0]["available_kg"] == 85.0


def test_owner_dashboard_contract(client):
    response = client.get(
        "/api/v1/owner/dashboard",
        headers={"Authorization": "Bearer mock-owner-token"},
    )
    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"data", "message", "error"}
    assert set(body["data"].keys()) == {
        "open_slots",
        "new_procurements",
        "quality_waiting",
        "ready_to_ship",
        "return_requests",
    }


def test_owner_ml_prediction_contract(client):
    payload = {
        "farm_id": 1,
        "product_id": 1,
        "features": {
            "past_yield_kg": 900,
            "avg_temperature": 23.5,
        },
    }
    response = client.post(
        "/api/v1/owner/ml/predictions",
        json=payload,
        headers={"Authorization": "Bearer mock-owner-token"},
    )
    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"data", "message", "error"}
    assert body["data"]["prediction_id"] >= 1


def test_login_contract_accepts_json_body(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "owner@test.com", "password": "demo1234!"},
    )
    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"data", "message", "error"}
    assert body["message"] == "success"
    assert body["data"]["token_type"] == "bearer"
    assert body["data"]["role"] == "OWNER"
    assert body["data"]["access_token"]


def test_login_contract_accepts_oauth2_password_form(client):
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "owner@test.com", "password": "demo1234!"},
    )
    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"data", "message", "error"}
    assert body["message"] == "success"
    assert body["data"]["token_type"] == "bearer"
    assert body["data"]["role"] == "OWNER"
    assert body["data"]["access_token"]


def test_oauth2_token_endpoint_returns_standard_response(client):
    response = client.post(
        "/api/v1/auth/token",
        data={"username": "owner@test.com", "password": "demo1234!"},
    )
    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"access_token", "token_type"}
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_oauth2_form_token_authorizes_me_endpoint(client):
    token_response = client.post(
        "/api/v1/auth/token",
        data={"username": "owner@test.com", "password": "demo1234!"},
    )
    token = token_response.json()["access_token"]

    response = client.get(
        "/api/v1/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"data", "message", "error"}
    assert body["data"]["email"] == "owner@test.com"
    assert body["data"]["role"] == "OWNER"


def test_openapi_oauth2_password_flow_points_to_login(client):
    response = client.get("/openapi.json")
    assert response.status_code == 200
    security_scheme = response.json()["components"]["securitySchemes"]["OAuth2PasswordBearer"]
    assert security_scheme["type"] == "oauth2"
    assert security_scheme["flows"]["password"]["tokenUrl"] == "/api/v1/auth/token"

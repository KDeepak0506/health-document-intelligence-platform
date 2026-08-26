from fastapi.testclient import TestClient


def test_health_endpoint(client: TestClient) -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_register_returns_user_without_password(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "name": "A Nurse",
            "email": "nurse@example.com",
            "password": "password123",
            "role": "nurse",
        },
    )

    assert response.status_code == 201
    assert response.json()["email"] == "nurse@example.com"
    assert response.json()["role"] == "nurse"
    assert "password" not in response.json()
    assert "password_hash" not in response.json()


def test_register_rejects_duplicate_email(client: TestClient, registered_user: dict) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Another Doctor",
            "email": registered_user["email"],
            "password": "password123",
            "role": "doctor",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Email is already registered"


def test_login_returns_bearer_token(client: TestClient, registered_user: dict) -> None:
    response = client.post(
        "/api/v1/auth/login",
        data={"username": registered_user["email"], "password": "password123"},
    )

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["access_token"]


def test_login_rejects_wrong_password(client: TestClient, registered_user: dict) -> None:
    response = client.post(
        "/api/v1/auth/login",
        data={"username": registered_user["email"], "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_documents_require_authentication(client: TestClient) -> None:
    response = client.get("/api/v1/documents")

    assert response.status_code == 401
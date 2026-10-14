import pytest
from fastapi.testclient import TestClient

from simple_bank.api.app import create_app
from simple_bank.settings import Settings

PUBLIC_ORIGIN = "https://d1234567890abc.cloudfront.net"


def test_health_check_is_available_without_a_database():
    with TestClient(create_app(settings=Settings(database_url=None))) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_sqlite_development_database_creates_schema_and_accepts_registration():
    settings = Settings(
        database_url="sqlite://",
        auth_code_pepper="synthetic-test-pepper",
        sqlite_create_schema=True,
        public_origin=PUBLIC_ORIGIN,
    )
    payload = {
        "name": "Synthetic SQLite Customer",
        "email": "sqlite-customer@example.test",
        "mobile_number": "+919876543210",
        "username": "sqlite-customer",
        "password": "synthetic development passphrase",
        "account_number_suffix": "0000123456",
    }

    with TestClient(create_app(settings=settings)) as client:
        response = client.post("/api/v1/auth/register", json=payload)

    assert response.status_code == 201
    assert response.json()["transfer_eligible"] is False


def test_local_mock_email_verification_accepts_only_the_fixed_development_code():
    settings = Settings(
        database_url="sqlite://",
        auth_code_pepper="synthetic-test-pepper",
        sqlite_create_schema=True,
        mock_contact_verification=True,
    )
    payload = {
        "name": "Synthetic Mock Customer",
        "email": "mock-customer@example.test",
        "mobile_number": "+919876543210",
        "username": "mock-customer",
        "password": "synthetic mock passphrase",
        "account_number_suffix": "0000123456",
    }

    with TestClient(create_app(settings=settings)) as client:
        registered = client.post("/api/v1/auth/register", json=payload)
        login = client.post(
            "/api/v1/auth/login",
            json={
                "username": payload["username"],
                "password": payload["password"],
            },
        )
        headers = {
            "Origin": "http://testserver",
            "X-CSRF-Token": login.json()["csrf_token"],
        }
        requested = client.post(
            "/api/v1/auth/contact-verification",
            json={"channel": "email"},
            headers=headers,
        )
        rejected = client.post(
            "/api/v1/auth/contact-verification/confirm",
            json={"channel": "email", "code": "0000"},
            headers=headers,
        )
        confirmed = client.post(
            "/api/v1/auth/contact-verification/confirm",
            json={"channel": "email", "code": "1234"},
            headers=headers,
        )

    assert registered.status_code == 201
    assert login.status_code == 200
    assert requested.status_code == 202
    assert requested.json() == {
        "message": "Local mock email is ready. Enter verification code 1234.",
        "code_length": 4,
    }
    assert rejected.status_code == 400
    assert confirmed.status_code == 200
    assert confirmed.json()["transfer_eligible"] is True


@pytest.mark.parametrize(
    "settings_values",
    [
        {"database_url": None},
        {"database_url": "sqlite://", "sqlite_create_schema": False},
        {
            "database_url": "postgresql://localhost/simple_bank",
            "sqlite_create_schema": True,
        },
    ],
)
def test_local_mock_email_verification_requires_schema_creating_sqlite(
    settings_values,
):
    with pytest.raises(ValueError, match="requires SQLite"):
        create_app(
            settings=Settings(
                **settings_values, mock_contact_verification=True
            )
        )


def test_public_origin_allows_cloudfront_origin_and_rejects_other_origins():
    settings = Settings(
        database_url="sqlite://",
        auth_code_pepper="synthetic-test-pepper",
        sqlite_create_schema=True,
        session_cookie_secure=True,
        public_origin=PUBLIC_ORIGIN,
    )
    payload = {
        "name": "Synthetic Origin Customer",
        "email": "origin-customer@example.test",
        "mobile_number": "+919876543210",
        "username": "origin-customer",
        "password": "synthetic origin passphrase",
        "account_number_suffix": "1000000001",
    }

    with TestClient(create_app(settings=settings)) as client:
        registered = client.post("/api/v1/auth/register", json=payload)
        rejected = client.post(
            "/api/v1/auth/login",
            json={"username": payload["username"], "password": payload["password"]},
            headers={"Origin": "https://attacker.example"},
        )
        allowed = client.post(
            "/api/v1/auth/login",
            json={"username": payload["username"], "password": payload["password"]},
            headers={"Origin": PUBLIC_ORIGIN},
        )

    assert registered.status_code == 201
    assert rejected.status_code == 403
    assert allowed.status_code == 200
    assert "Secure" in allowed.headers["set-cookie"]

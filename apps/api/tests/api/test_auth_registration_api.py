from fastapi.testclient import TestClient

from simple_bank.api.app import create_app
from simple_bank.services.auth_service import CustomerAuthService
from simple_bank.settings import Settings


def _client(auth_repository, contact_delivery, frozen_clock):
    service = CustomerAuthService(
        auth_repository,
        contact_delivery,
        settings=Settings(database_url=None, auth_code_pepper="synthetic-test-pepper"),
        clock=frozen_clock,
    )
    return TestClient(
        create_app(
            auth_service=service,
            contact_delivery=contact_delivery,
            settings=Settings(database_url=None, auth_code_pepper="synthetic-test-pepper"),
        )
    )


def _payload(**changes):
    return {
        "name": "Synthetic Customer",
        "email": "customer@example.test",
        "mobile_number": "+919876543210",
        "username": "customer-demo",
        "password": "long synthetic passphrase",
        "account_number_suffix": "0000123456",
    } | changes


def test_registration_returns_masked_account_without_credentials(
    auth_repository, contact_delivery, frozen_clock
):
    response = _client(auth_repository, contact_delivery, frozen_clock).post(
        "/api/v1/auth/register", json=_payload()
    )

    assert response.status_code == 201
    assert response.json()["account_number"] == "XXXX3456"
    assert response.json()["account_type"] == "SAVINGS"
    assert response.json()["status"] == "ACTIVE"
    assert response.json()["transfer_eligible"] is False
    assert "19910000123456" not in response.text
    assert "long synthetic passphrase" not in response.text


def test_invalid_registration_returns_safe_field_error_without_partial_records(
    auth_repository, contact_delivery, frozen_clock
):
    response = _client(auth_repository, contact_delivery, frozen_clock).post(
        "/api/v1/auth/register", json=_payload(account_number_suffix="12345x7890")
    )

    assert response.status_code == 400
    assert response.json()["error_code"] == "INVALID_REGISTRATION"
    assert auth_repository.profiles == {}
    assert auth_repository.accounts == {}


def test_registration_conflict_is_generic_and_does_not_leak_profile(
    auth_repository, contact_delivery, frozen_clock
):
    client = _client(auth_repository, contact_delivery, frozen_clock)
    client.post("/api/v1/auth/register", json=_payload())

    response = client.post(
        "/api/v1/auth/register",
        json=_payload(
            name="Other Synthetic Customer",
            email="other@example.test",
            mobile_number="+919876543211",
            username="other-customer",
            account_number_suffix="0000123456",
        ),
    )

    assert response.status_code == 409
    assert response.json()["error_code"] == "REGISTRATION_CONFLICT"
    assert "customer@example.test" not in response.text
    assert len(auth_repository.profiles) == 1
    assert len(auth_repository.accounts) == 1
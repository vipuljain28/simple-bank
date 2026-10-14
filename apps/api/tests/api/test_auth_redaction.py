import logging
from hashlib import sha256

from fastapi.testclient import TestClient

from simple_bank.api.app import create_app
from simple_bank.security.context import AuthenticatedCustomer
from simple_bank.services.auth_service import CustomerAuthService
from simple_bank.settings import Settings


class SessionContextForRedactionTest:
    def __init__(self, auth_repository, frozen_clock):
        self.auth_repository = auth_repository
        self.frozen_clock = frozen_clock

    def resolve(self, request):
        session_token = request.cookies.get("simple_bank_session")
        csrf_token = request.cookies.get("csrf_token")
        if not session_token or not csrf_token:
            return None
        principal = self.auth_repository.resolve_session(
            sha256(session_token.encode("utf-8")).hexdigest(), self.frozen_clock()
        )
        if principal is None:
            return None
        return AuthenticatedCustomer(
            customer_id=principal.customer_id,
            session_id=principal.session_id,
            display_name=principal.display_name,
            email_verified=principal.email_verified,
            mobile_verified=principal.mobile_verified,
            csrf_token_digest=principal.csrf_token_digest,
        )


def test_auth_responses_and_logs_do_not_leak_secrets(
    auth_repository, contact_delivery, frozen_clock, caplog
):
    settings = Settings(
        database_url=None,
        auth_code_pepper="synthetic-redaction-test-pepper",
    )
    service = CustomerAuthService(
        auth_repository,
        contact_delivery,
        settings=settings,
        clock=frozen_clock,
    )
    client = TestClient(
        create_app(
            auth_service=service,
            contact_delivery=contact_delivery,
            customer_context_provider=SessionContextForRedactionTest(
                auth_repository, frozen_clock
            ),
            settings=settings,
        )
    )
    password = "long synthetic passphrase"
    full_account_number = "19910000123456"
    caplog.set_level(logging.INFO)

    registration = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Synthetic Customer",
            "email": "customer@example.test",
            "mobile_number": "+919876543210",
            "username": "customer-demo",
            "password": password,
            "account_number_suffix": "0000123456",
        },
    )
    assert registration.status_code == 201
    assert full_account_number not in registration.text
    assert password not in registration.text

    login = client.post(
        "/api/v1/auth/login",
        json={"username": "customer-demo", "password": password},
    )
    assert login.status_code == 200
    session_token = client.cookies.get("simple_bank_session")
    assert session_token
    assert "httponly" in login.headers["set-cookie"].lower()
    assert session_token not in login.text
    assert password not in login.text

    session = client.get("/api/v1/auth/session")
    csrf_token = session.json()["csrf_token"]
    headers = {"Origin": "http://testserver", "X-CSRF-Token": csrf_token}
    verification = client.post(
        "/api/v1/auth/contact-verification",
        json={"channel": "email"},
        headers=headers,
    )
    verification_code = contact_delivery.sent[-1][2]
    assert verification.status_code == 202
    assert verification_code not in verification.text

    client.post(
        "/api/v1/auth/contact-verification/confirm",
        json={"channel": "email", "code": verification_code},
        headers=headers,
    )
    reset_request = client.post(
        "/api/v1/auth/password-reset/request",
        json={"username": "customer-demo", "channel": "email"},
        headers=headers,
    )
    reset_code = contact_delivery.sent[-1][2]
    assert reset_request.status_code == 202
    assert reset_code not in reset_request.text
    assert session_token not in caplog.text
    assert verification_code not in caplog.text
    assert reset_code not in caplog.text
    assert password not in caplog.text
    assert full_account_number not in caplog.text
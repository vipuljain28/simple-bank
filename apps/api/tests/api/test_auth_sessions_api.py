from hashlib import sha256
from dataclasses import replace

from fastapi.testclient import TestClient

from simple_bank.api.app import create_app
from simple_bank.domain.auth import ContactChannel
from simple_bank.security.context import AuthenticatedCustomer
from simple_bank.services.auth_service import CustomerAuthService
from simple_bank.settings import Settings


class MemoryCustomerContextProvider:
    def __init__(self, repository, clock):
        self.repository = repository
        self.clock = clock

    def resolve(self, request):
        token = request.cookies.get("simple_bank_session")
        if not token:
            return None
        principal = self.repository.resolve_session(
            sha256(token.encode("utf-8")).hexdigest(), self.clock()
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


def _client(auth_repository, contact_delivery, frozen_clock):
    service = CustomerAuthService(
        auth_repository,
        contact_delivery,
        settings=Settings(database_url=None, auth_code_pepper="synthetic-test-pepper"),
        clock=frozen_clock,
    )
    app = create_app(
        auth_service=service,
        contact_delivery=contact_delivery,
        customer_context_provider=MemoryCustomerContextProvider(
            auth_repository, frozen_clock
        ),
        settings=Settings(database_url=None, auth_code_pepper="synthetic-test-pepper"),
    )
    return TestClient(app)


def test_anonymous_session_status_is_public_and_sets_csrf_cookie():
    client = TestClient(create_app())

    response = client.get("/api/v1/auth/session")

    assert response.status_code == 200
    assert response.json()["authenticated"] is False
    assert response.json()["csrf_token"]
    assert "csrf_token=" in response.headers["set-cookie"]


def test_login_sets_httponly_session_cookie_and_csrf_token(
    auth_repository, contact_delivery, frozen_clock
):
    _client(auth_repository, contact_delivery, frozen_clock).post(
        "/api/v1/auth/register",
        json={
            "name": "Synthetic Customer",
            "email": "customer@example.test",
            "mobile_number": "+919876543210",
            "username": "customer-demo",
            "password": "long synthetic passphrase",
            "account_number_suffix": "0000123456",
        },
    )
    client = _client(auth_repository, contact_delivery, frozen_clock)

    response = client.post(
        "/api/v1/auth/login",
        json={"username": "customer-demo", "password": "long synthetic passphrase"},
    )

    assert response.status_code == 200
    assert response.json()["authenticated"] is True
    assert response.json()["csrf_token"]
    assert client.cookies.get("simple_bank_session")
    assert "httponly" in response.headers["set-cookie"].lower()


def test_sign_out_requires_session_and_matching_csrf_token(
    auth_repository, contact_delivery, frozen_clock
):
    _client(auth_repository, contact_delivery, frozen_clock).post(
        "/api/v1/auth/register",
        json={
            "name": "Synthetic Customer",
            "email": "customer@example.test",
            "mobile_number": "+919876543210",
            "username": "customer-demo",
            "password": "long synthetic passphrase",
            "account_number_suffix": "0000123456",
        },
    )
    client = _client(auth_repository, contact_delivery, frozen_clock)
    login = client.post(
        "/api/v1/auth/login",
        json={"username": "customer-demo", "password": "long synthetic passphrase"},
    )
    token = login.json()["csrf_token"]

    rejected = client.post(
        "/api/v1/auth/logout", headers={"Origin": "http://testserver"}
    )
    assert rejected.status_code == 403

    accepted = client.post(
        "/api/v1/auth/logout",
        headers={"Origin": "http://testserver", "X-CSRF-Token": token},
    )
    assert accepted.status_code == 204
    status = client.get("/api/v1/auth/session")
    assert status.json()["authenticated"] is False


def test_wrong_password_returns_generic_401(auth_repository, contact_delivery, frozen_clock):
    client = _client(auth_repository, contact_delivery, frozen_clock)
    client.post(
        "/api/v1/auth/register",
        json={
            "name": "Synthetic Customer",
            "email": "customer@example.test",
            "mobile_number": "+919876543210",
            "username": "customer-demo",
            "password": "long synthetic passphrase",
            "account_number_suffix": "0000123456",
        },
    )

    known = client.post(
        "/api/v1/auth/login",
        json={"username": "customer-demo", "password": "wrong synthetic password"},
    )
    unknown = client.post(
        "/api/v1/auth/login",
        json={"username": "nobody-demo", "password": "wrong synthetic password"},
    )

    assert known.status_code == unknown.status_code == 401
    assert known.json() == unknown.json()


def test_contact_verification_request_and_confirmation_updates_eligibility(
    auth_repository, contact_delivery, frozen_clock
):
    client = _client(auth_repository, contact_delivery, frozen_clock)
    client.post(
        "/api/v1/auth/register",
        json={
            "name": "Synthetic Customer",
            "email": "customer@example.test",
            "mobile_number": "+919876543210",
            "username": "customer-demo",
            "password": "long synthetic passphrase",
            "account_number_suffix": "0000123456",
        },
    )
    login = client.post(
        "/api/v1/auth/login",
        json={"username": "customer-demo", "password": "long synthetic passphrase"},
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
    assert requested.status_code == 202
    assert contact_delivery.sent[-1][:2] == (
        ContactChannel.EMAIL,
        "customer@example.test",
    )

    confirmed = client.post(
        "/api/v1/auth/contact-verification/confirm",
        json={"channel": "email", "code": contact_delivery.sent[-1][2]},
        headers=headers,
    )
    assert confirmed.status_code == 200
    assert confirmed.json()["transfer_eligible"] is True


def test_password_reset_request_is_generic_for_unknown_and_unverified_contacts(
    auth_repository, contact_delivery, frozen_clock
):
    client = _client(auth_repository, contact_delivery, frozen_clock)
    client.post(
        "/api/v1/auth/register",
        json={
            "name": "Synthetic Customer",
            "email": "customer@example.test",
            "mobile_number": "+919876543210",
            "username": "customer-demo",
            "password": "long synthetic passphrase",
            "account_number_suffix": "0000123456",
        },
    )
    headers = {"Origin": "http://testserver"}

    unknown = client.post(
        "/api/v1/auth/password-reset/request",
        json={"username": "unknown-demo", "channel": "email"},
        headers=headers,
    )
    unverified = client.post(
        "/api/v1/auth/password-reset/request",
        json={"username": "customer-demo", "channel": "email"},
        headers=headers,
    )

    assert unknown.status_code == unverified.status_code == 202
    assert unknown.json() == unverified.json()
    assert contact_delivery.sent == []


def test_cross_origin_cookie_write_is_rejected(
    auth_repository, contact_delivery, frozen_clock
):
    client = _client(auth_repository, contact_delivery, frozen_clock)
    client.post(
        "/api/v1/auth/register",
        json={
            "name": "Synthetic Customer",
            "email": "customer@example.test",
            "mobile_number": "+919876543210",
            "username": "customer-demo",
            "password": "long synthetic passphrase",
            "account_number_suffix": "0000123456",
        },
    )
    login = client.post(
        "/api/v1/auth/login",
        json={"username": "customer-demo", "password": "long synthetic passphrase"},
    )

    response = client.post(
        "/api/v1/auth/logout",
        headers={
            "Origin": "https://attacker.example",
            "X-CSRF-Token": login.json()["csrf_token"],
        },
    )

    assert response.status_code == 403
    assert client.get("/api/v1/auth/session").json()["authenticated"] is True


def test_password_reset_revokes_existing_session_and_requires_fresh_login(
    auth_repository, contact_delivery, frozen_clock
):
    client = _client(auth_repository, contact_delivery, frozen_clock)
    client.post(
        "/api/v1/auth/register",
        json={
            "name": "Synthetic Customer",
            "email": "customer@example.test",
            "mobile_number": "+919876543210",
            "username": "customer-demo",
            "password": "long synthetic passphrase",
            "account_number_suffix": "0000123456",
        },
    )
    profile = auth_repository.get_profile_by_username("customer-demo")
    auth_repository.profiles[profile.customer_id] = replace(
        profile, email_verified_at=frozen_clock()
    )
    login = client.post(
        "/api/v1/auth/login",
        json={"username": "customer-demo", "password": "long synthetic passphrase"},
    )
    request = client.post(
        "/api/v1/auth/password-reset/request",
        json={"username": "customer-demo", "channel": "email"},
        headers={"Origin": "http://testserver"},
    )
    assert request.status_code == 202
    reset_code = contact_delivery.sent[-1][2]

    reset = client.post(
        "/api/v1/auth/password-reset/confirm",
        json={"reset_code": reset_code, "new_password": "replacement synthetic passphrase"},
        headers={"Origin": "http://testserver"},
    )

    assert reset.status_code == 204
    assert client.get("/api/v1/auth/session").json()["authenticated"] is False
    relogin = client.post(
        "/api/v1/auth/login",
        json={"username": "customer-demo", "password": "replacement synthetic passphrase"},
    )
    assert relogin.status_code == 200
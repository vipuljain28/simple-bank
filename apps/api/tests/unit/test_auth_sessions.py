from datetime import timedelta

import pytest
from argon2 import PasswordHasher
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from simple_bank.domain.auth import ContactChannel, RegistrationCommand
from simple_bank.domain.auth_errors import (
    InvalidCredentials,
    InvalidOrExpiredChallenge,
    LoginTemporarilyThrottled,
)
from simple_bank.services.auth_service import CustomerAuthService
from simple_bank.security.context import (
    AuthenticatedCustomer,
    DatabaseCustomerContextProvider,
    get_authenticated_customer,
)
from simple_bank.settings import Settings


def _service(auth_repository, contact_delivery, frozen_clock):
    service = CustomerAuthService(
        auth_repository,
        contact_delivery,
        settings=Settings(database_url=None, auth_code_pepper="synthetic-test-pepper"),
        clock=frozen_clock,
        password_hasher=PasswordHasher(time_cost=1, memory_cost=8192, parallelism=1),
    )
    result = service.register(
        RegistrationCommand(
            name="Synthetic Customer",
            email="customer@example.test",
            mobile_number="+919876543210",
            username="customer-demo",
            password="long synthetic passphrase",
            account_number_suffix="0000123456",
        )
    )
    return service, result.customer_id


def test_successful_login_returns_opaque_session_and_csrf_tokens(
    auth_repository, contact_delivery, frozen_clock
):
    service, customer_id = _service(auth_repository, contact_delivery, frozen_clock)

    grant = service.login("CUSTOMER-DEMO", "long synthetic passphrase")

    assert grant.customer_id == customer_id
    assert grant.session_token
    assert grant.csrf_token
    assert grant.session_token != grant.csrf_token
    stored_session = auth_repository.sessions[grant.session_id]
    assert stored_session.token_digest != grant.session_token
    assert stored_session.csrf_token_digest != grant.csrf_token
    assert stored_session.created_at == frozen_clock()


def test_unknown_username_and_wrong_password_share_generic_failure(
    auth_repository, contact_delivery, frozen_clock
):
    service, _ = _service(auth_repository, contact_delivery, frozen_clock)

    with pytest.raises(InvalidCredentials) as known:
        service.login("customer-demo", "wrong synthetic password")
    with pytest.raises(InvalidCredentials) as unknown:
        service.login("unknown-demo", "wrong synthetic password")

    assert known.value.code == unknown.value.code
    assert known.value.message == unknown.value.message


def test_fifth_failure_starts_cooldown_and_valid_login_works_after_expiry(
    auth_repository, contact_delivery, frozen_clock
):
    service, customer_id = _service(auth_repository, contact_delivery, frozen_clock)

    for _ in range(5):
        with pytest.raises(InvalidCredentials):
            service.login("customer-demo", "wrong synthetic password")
    with pytest.raises(LoginTemporarilyThrottled):
        service.login("customer-demo", "long synthetic passphrase")

    frozen_clock.advance(minutes=15)
    grant = service.login("customer-demo", "long synthetic passphrase")
    assert grant.customer_id == customer_id


def test_contact_verification_is_single_use_and_enables_transfers(
    auth_repository, contact_delivery, frozen_clock
):
    service, customer_id = _service(auth_repository, contact_delivery, frozen_clock)
    service.request_contact_verification(customer_id, ContactChannel.EMAIL)
    channel, destination, code = contact_delivery.sent[-1]

    assert channel == ContactChannel.EMAIL
    assert destination == "customer@example.test"
    result = service.confirm_contact_verification(customer_id, channel, code)

    assert result.transfer_eligible is True
    assert auth_repository.get_profile_by_id(customer_id).email_verified_at == frozen_clock()
    with pytest.raises(InvalidOrExpiredChallenge):
        service.confirm_contact_verification(customer_id, channel, code)


def test_expired_contact_code_does_not_verify_contact(
    auth_repository, contact_delivery, frozen_clock
):
    service, customer_id = _service(auth_repository, contact_delivery, frozen_clock)
    service.request_contact_verification(customer_id, ContactChannel.MOBILE)
    channel, _, code = contact_delivery.sent[-1]
    frozen_clock.advance(minutes=10, seconds=1)

    with pytest.raises(InvalidOrExpiredChallenge):
        service.confirm_contact_verification(customer_id, channel, code)

    assert auth_repository.get_profile_by_id(customer_id).mobile_verified_at is None


def test_password_reset_requires_verified_contact_and_revokes_sessions(
    auth_repository, contact_delivery, frozen_clock
):
    service, customer_id = _service(auth_repository, contact_delivery, frozen_clock)
    with pytest.raises(InvalidOrExpiredChallenge):
        service.request_password_reset("customer-demo", ContactChannel.EMAIL)
    assert contact_delivery.sent == []

    service.request_contact_verification(customer_id, ContactChannel.EMAIL)
    channel, _, verification_code = contact_delivery.sent[-1]
    service.confirm_contact_verification(customer_id, channel, verification_code)
    grant = service.login("customer-demo", "long synthetic passphrase")

    service.request_password_reset("customer-demo", ContactChannel.EMAIL)
    _, destination, reset_code = contact_delivery.sent[-1]
    assert destination == "customer@example.test"
    service.confirm_password_reset(reset_code, "new synthetic passphrase")

    assert auth_repository.sessions[grant.session_id].revoked_at == frozen_clock()
    with pytest.raises(InvalidCredentials):
        service.login("customer-demo", "long synthetic passphrase")
    assert service.login("customer-demo", "new synthetic passphrase").customer_id == customer_id


def test_logout_revokes_session(auth_repository, contact_delivery, frozen_clock):
    service, _ = _service(auth_repository, contact_delivery, frozen_clock)
    grant = service.login("customer-demo", "long synthetic passphrase")

    service.logout(grant.session_id)

    assert auth_repository.sessions[grant.session_id].revoked_at == frozen_clock()


def _protected_client(auth_repository, frozen_clock):
    app = FastAPI()
    app.state.customer_context_provider = DatabaseCustomerContextProvider(
        auth_repository,
        Settings(database_url=None),
        clock=frozen_clock,
    )

    @app.get("/protected")
    def protected(customer: AuthenticatedCustomer = Depends(get_authenticated_customer)):
        return {"customer_id": customer.customer_id}

    return TestClient(app)


def test_session_expires_after_five_minutes_of_inactivity(
    auth_repository, contact_delivery, frozen_clock
):
    service, _ = _service(auth_repository, contact_delivery, frozen_clock)
    grant = service.login("customer-demo", "long synthetic passphrase")
    client = _protected_client(auth_repository, frozen_clock)
    client.cookies.set("simple_bank_session", grant.session_token)

    assert client.get("/protected").status_code == 200
    frozen_clock.advance(minutes=5)
    assert client.get("/protected").status_code == 401


def test_session_expires_at_one_hour_even_with_recent_activity(
    auth_repository, contact_delivery, frozen_clock
):
    service, _ = _service(auth_repository, contact_delivery, frozen_clock)
    grant = service.login("customer-demo", "long synthetic passphrase")
    client = _protected_client(auth_repository, frozen_clock)
    client.cookies.set("simple_bank_session", grant.session_token)

    for _ in range(14):
        frozen_clock.advance(minutes=4)
        assert client.get("/protected").status_code == 200
    frozen_clock.advance(minutes=4)
    assert client.get("/protected").status_code == 401
from decimal import Decimal
from hashlib import sha256

from fastapi.testclient import TestClient
import pytest

from simple_bank.api.app import create_app
from simple_bank.domain.errors import TransferError
from simple_bank.security.context import AuthenticatedCustomer
from simple_bank.services.transfer_service import TransferService


class FixedCustomerContext:
    def __init__(self, customer: AuthenticatedCustomer | None):
        self.customer = customer

    def resolve(self, request):
        return self.customer


def _client(transfer_repository, verifier_factory, customer):
    amount = Decimal("25.00")
    verifier = verifier_factory(
        customer_id="customer-001",
        request_id="req-auth-001",
        from_account="000000001001",
        to_account="000000002002",
        amount=amount,
    )
    return TestClient(
        create_app(
            transfer_service=TransferService(transfer_repository, verifier),
            customer_context_provider=FixedCustomerContext(customer),
        ),
        headers={
            "Origin": "http://testserver",
            "X-CSRF-Token": "synthetic-transfer-csrf",
        },
    )


def _payload(**changes):
    return {
        "request_id": "req-auth-001",
        "verification_proof": "synthetic-verification-proof",
        "from_account": "000000001001",
        "to_account": "000000002002",
        "amount": "25.00",
    } | changes


def _with_csrf(client):
    client.cookies.set("csrf_token", "synthetic-transfer-csrf")
    return client


def test_missing_session_is_401_before_transfer_mutation(
    transfer_repository, verifier_factory
):
    client = _with_csrf(_client(transfer_repository, verifier_factory, None))

    response = client.post("/api/v1/transfers", json=_payload())

    assert response.status_code == 401
    assert transfer_repository.accounts["000000001001"].balance == Decimal("500.00")
    assert transfer_repository.transfers == {}


def test_valid_session_reaches_transfer_service_under_session_identity(
    transfer_repository, verifier_factory
):
    client = _client(
        transfer_repository,
        verifier_factory,
        AuthenticatedCustomer(
            customer_id="customer-001",
            session_id="session-demo",
            email_verified=True,
            csrf_token_digest=sha256(b"synthetic-transfer-csrf").hexdigest(),
        ),
    )
    _with_csrf(client)

    response = client.post("/api/v1/transfers", json=_payload())

    assert response.status_code == 201
    assert response.json()["from_account"] == "XXXX1001"
    assert len(transfer_repository.transfers) == 1
    assert transfer_repository.accounts["000000001001"].balance == Decimal("475.00")


def test_unverified_session_is_rejected_before_transfer_mutation(
    transfer_repository, verifier_factory
):
    client = _client(
        transfer_repository,
        verifier_factory,
        AuthenticatedCustomer(
            customer_id="customer-001",
            session_id="session-demo",
            csrf_token_digest=sha256(b"synthetic-transfer-csrf").hexdigest(),
        ),
    )
    _with_csrf(client)

    response = client.post("/api/v1/transfers", json=_payload())

    assert response.status_code == 403
    assert response.json()["error_code"] == "CONTACT_VERIFICATION_REQUIRED"
    assert transfer_repository.accounts["000000001001"].balance == Decimal("500.00")
    assert transfer_repository.transfers == {}


def test_request_body_cannot_supply_or_override_customer_identity(
    transfer_repository, verifier_factory
):
    client = _client(
        transfer_repository,
        verifier_factory,
        AuthenticatedCustomer(
            customer_id="customer-001",
            session_id="session-demo",
            email_verified=True,
            csrf_token_digest=sha256(b"synthetic-transfer-csrf").hexdigest(),
        ),
    )
    _with_csrf(client)

    response = client.post(
        "/api/v1/transfers", json=_payload(customer_id="another-customer")
    )

    assert response.status_code == 400
    assert response.json()["error_code"] == "INVALID_REQUEST"
    assert transfer_repository.accounts["000000001001"].balance == Decimal("500.00")
    assert transfer_repository.transfers == {}


def test_malformed_account_identifier_is_rejected_without_mutation(
    transfer_repository, verifier_factory
):
    client = _with_csrf(
        _client(
            transfer_repository,
            verifier_factory,
            AuthenticatedCustomer(
                customer_id="customer-001",
                session_id="session-demo",
                email_verified=True,
                csrf_token_digest=sha256(b"synthetic-transfer-csrf").hexdigest(),
            ),
        )
    )

    response = client.post(
        "/api/v1/transfers", json=_payload(from_account="not-an-account")
    )

    assert response.status_code == 400
    assert response.json()["error_code"] == "INVALID_REQUEST"
    assert transfer_repository.accounts["000000001001"].balance == Decimal("500.00")
    assert transfer_repository.transfers == {}
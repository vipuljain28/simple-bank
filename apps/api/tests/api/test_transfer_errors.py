from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal
from hashlib import sha256

from fastapi.testclient import TestClient
import pytest

from simple_bank.security.context import AuthenticatedCustomer
from simple_bank.services.transfer_service import TransferService
from simple_bank.api.app import create_app
from simple_bank.domain.transfers import TransferRecord


class FixedCustomerContext:
    def resolve(self, request):
        return AuthenticatedCustomer(
            "customer-001",
            session_id="session-demo",
            email_verified=True,
            csrf_token_digest=sha256(b"synthetic-transfer-csrf").hexdigest(),
        )


def _client(repository, verifier_factory):
    amount = Decimal("25.00")
    verifier = verifier_factory(
        customer_id="customer-001",
        request_id="req-api-001",
        from_account="000000001001",
        to_account="000000002002",
        amount=amount,
    )
    service = TransferService(repository, verifier)
    app = create_app(
        transfer_service=service,
        customer_context_provider=FixedCustomerContext(),
    )
    client = TestClient(
        app,
        headers={
            "Origin": "http://testserver",
            "X-CSRF-Token": "synthetic-transfer-csrf",
        },
    )
    client.cookies.set("csrf_token", "synthetic-transfer-csrf")
    return client


def _payload(**changes):
    payload = {
        "request_id": "req-api-001",
        "verification_proof": "synthetic-verification-proof",
        "from_account": "000000001001",
        "to_account": "000000002002",
        "amount": "25.00",
    }
    return payload | changes


def test_success_is_versioned_and_masks_account_numbers(transfer_repository, verifier_factory):
    response = _client(transfer_repository, verifier_factory).post(
        "/api/v1/transfers", json=_payload()
    )

    assert response.status_code == 201
    assert response.json()["from_account"] == "XXXX1001"
    assert response.json()["to_account"] == "XXXX2002"
    assert "000000001001" not in response.text
    assert "000000002002" not in response.text


def test_invalid_amount_maps_to_documented_400_error_without_mutation(
    transfer_repository, verifier_factory
):
    response = _client(transfer_repository, verifier_factory).post(
        "/api/v1/transfers", json=_payload(amount="0.00")
    )

    assert response.status_code == 400
    assert response.json()["error_code"] == "INVALID_AMOUNT"
    assert transfer_repository.accounts["000000001001"].balance == Decimal("5000.00")
    assert transfer_repository.transfers == {}


def test_unowned_sender_returns_generic_forbidden_without_mutation(transfer_repository, verifier_factory):
    transfer_repository.accounts["000000001001"] = transfer_repository.accounts[
        "000000001001"
    ].__class__("000000001001", "other-customer", Decimal("500.00"), "ACTIVE", "SAVINGS")
    response = _client(transfer_repository, verifier_factory).post(
        "/api/v1/transfers", json=_payload()
    )

    assert response.status_code == 403
    assert response.json()["error_code"] == "FORBIDDEN"
    assert "000000001001" not in response.text
    assert transfer_repository.accounts["000000001001"].balance == Decimal("500.00")
    assert transfer_repository.transfers == {}


@pytest.mark.parametrize(
    "rule,status_code,error_code",
    [
        ("insufficient", 422, "INSUFFICIENT_BALANCE"),
        ("daily_limit", 422, "DAILY_LIMIT_EXCEEDED"),
        ("same_account", 422, "SAME_ACCOUNT"),
        ("inactive", 422, "ACCOUNT_INACTIVE"),
        ("request_conflict", 409, "REQUEST_ID_CONFLICT"),
        ("verification", 403, "VERIFICATION_REQUIRED"),
    ],
)
def test_business_rejections_map_to_the_documented_api_error(
    transfer_repository, verifier_factory, rule, status_code, error_code
):
    request_id = "req-api-001"
    if rule == "insufficient":
        transfer_repository.accounts["000000001001"] = replace(
            transfer_repository.accounts["000000001001"], balance=Decimal("10.00")
        )
    elif rule == "daily_limit":
        transfer_repository.transfers[("customer-001", "prior")] = TransferRecord(
            "txn-prior",
            "customer-001",
            "prior",
            "000000001001",
            "000000002002",
            Decimal("99990.00"),
            "ACCEPTED",
            datetime.now(UTC),
        )
    elif rule == "inactive":
        transfer_repository.accounts["000000002002"] = replace(
            transfer_repository.accounts["000000002002"], status="INACTIVE"
        )
    elif rule == "request_conflict":
        transfer_repository.transfers[("customer-001", request_id)] = TransferRecord(
            "txn-prior",
            "customer-001",
            request_id,
            "000000001001",
            "000000002002",
            Decimal("30.00"),
            "ACCEPTED",
            datetime.now(UTC),
        )

    payload = _payload(
        to_account="000000001001" if rule == "same_account" else "000000002002",
        verification_proof="invalid-proof" if rule == "verification" else "synthetic-verification-proof",
    )
    initial_sender_balance = transfer_repository.accounts["000000001001"].balance
    initial_recipient_balance = transfer_repository.accounts["000000002002"].balance
    initial_transfer_count = len(transfer_repository.transfers)

    response = _client(transfer_repository, verifier_factory).post(
        "/api/v1/transfers", json=payload
    )

    assert response.status_code == status_code
    assert response.json()["error_code"] == error_code
    assert transfer_repository.accounts["000000001001"].balance == initial_sender_balance
    assert transfer_repository.accounts["000000002002"].balance == initial_recipient_balance
    assert len(transfer_repository.transfers) == initial_transfer_count
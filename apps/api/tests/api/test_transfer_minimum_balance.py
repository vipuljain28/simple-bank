"""API tests for minimum balance enforcement on transfers."""
from decimal import Decimal
from hashlib import sha256

from fastapi.testclient import TestClient
import pytest

from simple_bank.api.app import create_app
from simple_bank.domain.transfer_repository import AccountSnapshot
from simple_bank.security.context import AuthenticatedCustomer
from simple_bank.services.transfer_service import TransferService


class FixedCustomerContext:
    def __init__(self, customer: AuthenticatedCustomer | None):
        self.customer = customer

    def resolve(self, request):
        return self.customer


def _client(transfer_repository, verifier_factory, customer, settings=None):
    amount = Decimal("4000.00")
    verifier = verifier_factory(
        customer_id="customer-001",
        request_id="req-min-001",
        from_account="000000001001",
        to_account="000000002002",
        amount=amount,
    )
    client = TestClient(
        create_app(
            transfer_service=TransferService(
                transfer_repository,
                verifier,
                settings=settings,
            ),
            customer_context_provider=FixedCustomerContext(customer),
        ),
        headers={
            "Origin": "http://testserver",
            "X-CSRF-Token": "synthetic-transfer-csrf",
        },
    )
    client.cookies.set("csrf_token", "synthetic-transfer-csrf")
    return client


def _payload(request_id="req-min-001", amount="4000.00", **changes):
    return {
        "request_id": request_id,
        "verification_proof": "synthetic-verification-proof",
        "from_account": "000000001001",
        "to_account": "000000002002",
        "amount": amount,
    } | changes


def test_transfer_leaving_balance_at_minimum_is_accepted(
    transfer_repository, verifier_factory, test_settings
):
    """Test: Transfer leaving exactly at minimum balance threshold is accepted."""
    # Account balance: 5000, transfer 4000, minimum 1000 → balance after = 1000 ✓
    customer = AuthenticatedCustomer(
        customer_id="customer-001",
        session_id="session-demo",
        email_verified=True,
        csrf_token_digest=sha256(b"synthetic-transfer-csrf").hexdigest(),
    )
    client = _client(transfer_repository, verifier_factory, customer, settings=test_settings)
    
    response = client.post("/api/v1/transfers", json=_payload())
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "ACCEPTED"
    assert data["from_account"] == "XXXX1001"
    assert data["to_account"] == "XXXX2002"
    assert data["amount"] == "4000.00"
    
    # Verify balances updated
    assert transfer_repository.accounts["000000001001"].balance == Decimal("1000.00")
    assert transfer_repository.accounts["000000002002"].balance == Decimal("6000.00")


def test_transfer_below_minimum_is_rejected(
    transfer_repository, verifier_factory, test_settings
):
    """Test: Transfer that would leave balance below minimum is rejected."""
    # Account balance: 5000, transfer 4001, minimum 1000 → balance after = 999 ✗
    customer = AuthenticatedCustomer(
        customer_id="customer-001",
        session_id="session-demo",
        email_verified=True,
        csrf_token_digest=sha256(b"synthetic-transfer-csrf").hexdigest(),
    )
    client = _client(transfer_repository, verifier_factory, customer, settings=test_settings)
    
    response = client.post(
        "/api/v1/transfers",
        json=_payload(request_id="req-min-002", amount="4001.00"),
    )
    assert response.status_code == 400
    data = response.json()
    assert data["error_code"] == "MIN_BALANCE_REQUIRED"
    assert "balance" in data["message"].lower() or "minimum" in data["message"].lower()
    
    # Verify no masked account number leak
    assert "000000001001" not in data["message"]
    assert "000000002002" not in data["message"]
    
    # Verify balances unchanged (atomicity)
    assert transfer_repository.accounts["000000001001"].balance == Decimal("5000.00")
    assert transfer_repository.accounts["000000002002"].balance == Decimal("2000.00")


def test_transfer_below_minimum_by_penny_is_rejected(
    transfer_repository, verifier_factory, test_settings
):
    """Test: Even a transfer by 0.01 below minimum is rejected."""
    # Account balance: 5000, transfer 4000.01, minimum 1000 → balance after = 999.99 ✗
    customer = AuthenticatedCustomer(
        customer_id="customer-001",
        session_id="session-demo",
        email_verified=True,
        csrf_token_digest=sha256(b"synthetic-transfer-csrf").hexdigest(),
    )
    client = _client(transfer_repository, verifier_factory, customer, settings=test_settings)
    
    response = client.post(
        "/api/v1/transfers",
        json=_payload(request_id="req-min-003", amount="4000.01"),
    )
    assert response.status_code == 400
    data = response.json()
    assert data["error_code"] == "MIN_BALANCE_REQUIRED"


def test_minimum_balance_applies_per_account_independently(
    transfer_repository, verifier_factory, test_settings
):
    """Test: Minimum balance is enforced for each account independently."""
    # Set up a second account with moderate balance
    transfer_repository.accounts["000000003003"] = AccountSnapshot(
        "000000003003", "customer-001", Decimal("1500.00"), "ACTIVE", "SAVINGS"
    )
    
    customer = AuthenticatedCustomer(
        customer_id="customer-001",
        session_id="session-demo",
        email_verified=True,
        csrf_token_digest=sha256(b"synthetic-transfer-csrf").hexdigest(),
    )
    
    # First transfer: from high-balance (5000) to low-balance (1500)
    verifier1 = verifier_factory(
        customer_id="customer-001",
        request_id="req-high",
        from_account="000000001001",
        to_account="000000003003",
        amount=Decimal("3000.00"),
    )
    client1 = TestClient(
        create_app(
            transfer_service=TransferService(
                transfer_repository,
                verifier1,
                settings=test_settings,
            ),
            customer_context_provider=FixedCustomerContext(customer),
        ),
        headers={
            "Origin": "http://testserver",
            "X-CSRF-Token": "synthetic-transfer-csrf",
        },
    )
    client1.cookies.set("csrf_token", "synthetic-transfer-csrf")
    
    response1 = client1.post(
        "/api/v1/transfers",
        json={
            "request_id": "req-high",
            "verification_proof": "synthetic-verification-proof",
            "from_account": "000000001001",
            "to_account": "000000003003",
            "amount": "3000.00",
        },
    )
    assert response1.status_code == 201
    # After transfer: account 1 = 2000, account 3 = 4500
    assert transfer_repository.accounts["000000001001"].balance == Decimal("2000.00")
    assert transfer_repository.accounts["000000003003"].balance == Decimal("4500.00")
    
    # Second transfer: from account 3 (4500) trying to transfer 3500
    # 4500 - 3500 = 1000, which is exactly the minimum, so it should succeed
    verifier2 = verifier_factory(
        customer_id="customer-001",
        request_id="req-low",
        from_account="000000003003",
        to_account="000000001001",
        amount=Decimal("3500.00"),
    )
    client2 = TestClient(
        create_app(
            transfer_service=TransferService(
                transfer_repository,
                verifier2,
                settings=test_settings,
            ),
            customer_context_provider=FixedCustomerContext(customer),
        ),
        headers={
            "Origin": "http://testserver",
            "X-CSRF-Token": "synthetic-transfer-csrf",
        },
    )
    client2.cookies.set("csrf_token", "synthetic-transfer-csrf")
    
    response2 = client2.post(
        "/api/v1/transfers",
        json={
            "request_id": "req-low",
            "verification_proof": "synthetic-verification-proof",
            "from_account": "000000003003",
            "to_account": "000000001001",
            "amount": "3500.00",
        },
    )
    # This should succeed because 4500 - 3500 = 1000 (exactly at minimum)
    assert response2.status_code == 201
    assert transfer_repository.accounts["000000003003"].balance == Decimal("1000.00")
    assert transfer_repository.accounts["000000001001"].balance == Decimal("5500.00")


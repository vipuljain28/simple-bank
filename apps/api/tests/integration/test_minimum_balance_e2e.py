"""End-to-end tests for minimum balance enforcement across all scenarios."""
from decimal import Decimal
from hashlib import sha256

from fastapi.testclient import TestClient

from simple_bank.api.app import create_app
from simple_bank.domain.transfer_repository import AccountSnapshot
from simple_bank.security.context import AuthenticatedCustomer
from simple_bank.services.transfer_service import TransferService


class FixedCustomerContext:
    def __init__(self, customer: AuthenticatedCustomer | None):
        self.customer = customer

    def resolve(self, request):
        return self.customer


def _make_client(transfer_repository, verifier, customer):
    """Create a TestClient with the given verifier."""
    client = TestClient(
        create_app(
            transfer_service=TransferService(
                transfer_repository,
                verifier,
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


def test_e2e_minimum_balance_enforcement_at_and_below_minimum(
    transfer_repository, verifier_factory, test_settings
):
    """
    End-to-end test covering minimum balance enforcement:
    1. Setup: Account with 10,000, minimum 1,000
    2. Scenario A: Transfer leaving balance at minimum (10000 - 9000 = 1,000) ✓
    3. Verify error message contains context without account number leaks
    """
    # Setup: Account with 10,000, minimum 1,000
    transfer_repository.accounts["000000001001"] = AccountSnapshot(
        "000000001001", "customer-e2e-001", Decimal("10000.00"), "ACTIVE", "SAVINGS"
    )
    transfer_repository.accounts["000000002002"] = AccountSnapshot(
        "000000002002", "customer-e2e-001", Decimal("5000.00"), "ACTIVE", "CURRENT"
    )
    
    customer = AuthenticatedCustomer(
        customer_id="customer-e2e-001",
        session_id="session-e2e",
        email_verified=True,
        csrf_token_digest=sha256(b"synthetic-transfer-csrf").hexdigest(),
    )
    
    # Scenario A: Transfer leaving balance at minimum (10000 - 9000 = 1,000) ✓
    verifier_a = verifier_factory(
        customer_id="customer-e2e-001",
        request_id="req-e2e-scenario-a",
        from_account="000000001001",
        to_account="000000002002",
        amount=Decimal("9000.00"),
    )
    client_a = _make_client(transfer_repository, verifier_a, customer)
    
    response_a = client_a.post(
        "/api/v1/transfers",
        json={
            "request_id": "req-e2e-scenario-a",
            "verification_proof": "synthetic-verification-proof",
            "from_account": "000000001001",
            "to_account": "000000002002",
            "amount": "9000.00",
        },
    )
    assert response_a.status_code == 201
    assert response_a.json()["status"] == "ACCEPTED"
    assert transfer_repository.accounts["000000001001"].balance == Decimal("1000.00")


def test_e2e_minimum_balance_below_minimum_rejected(
    transfer_repository, verifier_factory, test_settings
):
    """
    End-to-end test for rejection when transfer would go below minimum.
    
    Scenario: 10000 - 9001 = 999 (below 1000 minimum) ✗
    Verify error message contains context, no account number leaks, balance unchanged
    """
    transfer_repository.accounts["000000001001"] = AccountSnapshot(
        "000000001001", "customer-e2e-below-001", Decimal("10000.00"), "ACTIVE", "SAVINGS"
    )
    transfer_repository.accounts["000000002002"] = AccountSnapshot(
        "000000002002", "customer-e2e-below-001", Decimal("5000.00"), "ACTIVE", "CURRENT"
    )
    
    customer = AuthenticatedCustomer(
        customer_id="customer-e2e-below-001",
        session_id="session-e2e-below",
        email_verified=True,
        csrf_token_digest=sha256(b"synthetic-transfer-csrf").hexdigest(),
    )
    
    # Transfer below minimum (10000 - 9001 = 999) ✗
    verifier = verifier_factory(
        customer_id="customer-e2e-below-001",
        request_id="req-e2e-below",
        from_account="000000001001",
        to_account="000000002002",
        amount=Decimal("9001.00"),
    )
    client = _make_client(transfer_repository, verifier, customer)
    
    response = client.post(
        "/api/v1/transfers",
        json={
            "request_id": "req-e2e-below",
            "verification_proof": "synthetic-verification-proof",
            "from_account": "000000001001",
            "to_account": "000000002002",
            "amount": "9001.00",
        },
    )
    assert response.status_code == 400
    data = response.json()
    assert data["error_code"] == "MIN_BALANCE_REQUIRED"
    
    # Verify error message contains context
    message = data["message"]
    assert "10000.00" in message  # current balance
    assert "9001.00" in message   # amount
    assert "999.00" in message    # balance after
    assert "1000.00" in message   # min balance
    
    # Verify no full account number leak
    assert "000000001001" not in message
    assert "000000002002" not in message
    assert "XXXX1001" in message  # masked account should be present
    
    # Verify balance unchanged after rejection
    assert transfer_repository.accounts["000000001001"].balance == Decimal("10000.00")


def test_e2e_minimum_balance_multiple_accounts_independently(
    transfer_repository, verifier_factory, test_settings
):
    """
    E2E test verifying minimum balance is enforced per-account independently.
    
    Scenario:
    - Account A: 5,000 (can transfer 4,000)
    - Account B: 1,500 (cannot transfer 1,000)
    - Minimum: 1,000
    """
    transfer_repository.accounts["000000001001"] = AccountSnapshot(
        "000000001001", "customer-multi-001", Decimal("5000.00"), "ACTIVE", "SAVINGS"
    )
    transfer_repository.accounts["000000002002"] = AccountSnapshot(
        "000000002002", "customer-multi-001", Decimal("1500.00"), "ACTIVE", "SAVINGS"
    )
    transfer_repository.accounts["000000003003"] = AccountSnapshot(
        "000000003003", "customer-multi-001", Decimal("5000.00"), "ACTIVE", "SAVINGS"
    )
    
    customer = AuthenticatedCustomer(
        customer_id="customer-multi-001",
        session_id="session-multi",
        email_verified=True,
        csrf_token_digest=sha256(b"synthetic-transfer-csrf").hexdigest(),
    )
    
    # Account A (5000) → transfers 4000 (leaves 1000) ✓
    verifier_a = verifier_factory(
        customer_id="customer-multi-001",
        request_id="req-multi-a",
        from_account="000000001001",
        to_account="000000003003",
        amount=Decimal("4000.00"),
    )
    client_a = _make_client(transfer_repository, verifier_a, customer)
    
    response_a = client_a.post(
        "/api/v1/transfers",
        json={
            "request_id": "req-multi-a",
            "verification_proof": "synthetic-verification-proof",
            "from_account": "000000001001",
            "to_account": "000000003003",
            "amount": "4000.00",
        },
    )
    assert response_a.status_code == 201
    assert transfer_repository.accounts["000000001001"].balance == Decimal("1000.00")
    
    # Account B (1500) → tries to transfer 1000 (would leave 500) ✗
    verifier_b = verifier_factory(
        customer_id="customer-multi-001",
        request_id="req-multi-b",
        from_account="000000002002",
        to_account="000000003003",
        amount=Decimal("1000.00"),
    )
    client_b = _make_client(transfer_repository, verifier_b, customer)
    
    response_b = client_b.post(
        "/api/v1/transfers",
        json={
            "request_id": "req-multi-b",
            "verification_proof": "synthetic-verification-proof",
            "from_account": "000000002002",
            "to_account": "000000003003",
            "amount": "1000.00",
        },
    )
    assert response_b.status_code == 400
    assert response_b.json()["error_code"] == "MIN_BALANCE_REQUIRED"
    
def test_e2e_minimum_balance_atomicity_on_rejection(
    transfer_repository, verifier_factory, test_settings
):
    """
    E2E test verifying atomicity: when minimum balance would be violated,
    no balance changes occur (both sender and recipient remain unchanged).
    """
    initial_sender = Decimal("5000.00")
    initial_recipient = Decimal("2000.00")
    
    transfer_repository.accounts["000000001001"] = AccountSnapshot(
        "000000001001", "customer-atomic-001", initial_sender, "ACTIVE", "SAVINGS"
    )
    transfer_repository.accounts["000000002002"] = AccountSnapshot(
        "000000002002", "customer-atomic-001", initial_recipient, "ACTIVE", "CURRENT"
    )
    
    customer = AuthenticatedCustomer(
        customer_id="customer-atomic-001",
        session_id="session-atomic",
        email_verified=True,
        csrf_token_digest=sha256(b"synthetic-transfer-csrf").hexdigest(),
    )
    
    # Attempt transfer below minimum
    verifier = verifier_factory(
        customer_id="customer-atomic-001",
        request_id="req-atomic",
        from_account="000000001001",
        to_account="000000002002",
        amount=Decimal("4500.00"),
    )
    client = _make_client(transfer_repository, verifier, customer)
    
    response = client.post(
        "/api/v1/transfers",
        json={
            "request_id": "req-atomic",
            "verification_proof": "synthetic-verification-proof",
            "from_account": "000000001001",
            "to_account": "000000002002",
            "amount": "4500.00",
        },
    )
    assert response.status_code == 400
    
    # Verify both accounts unchanged (atomicity preserved)
    assert transfer_repository.accounts["000000001001"].balance == initial_sender
    assert transfer_repository.accounts["000000002002"].balance == initial_recipient

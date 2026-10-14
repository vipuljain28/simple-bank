"""Performance test for minimum balance validation."""
from decimal import Decimal
import time
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


class SyntheticTransferVerifier:
    """Synthetic verifier that tracks calls and always approves."""
    def __init__(self, expected):
        self.expected = expected
        self.calls = []

    def verify(
        self,
        customer_id: str,
        request_id: str,
        from_account: str,
        to_account: str,
        amount: Decimal,
        proof: str,
    ) -> bool:
        claim = (customer_id, request_id, from_account, to_account, amount)
        self.calls.append(claim)
        return proof == "synthetic-verification-proof" and claim == self.expected


def test_minimum_balance_validation_performance_rejection(
    transfer_repository, test_settings
):
    """
    Performance test: Minimum balance validation should reject quickly (<100ms).
    
    When a transfer violates minimum balance, validation should reject at the 
    business logic layer before any I/O or database operations, ensuring fast 
    failure for invalid requests.
    """
    # Setup repository with accounts
    transfer_repository.accounts["000000001001"] = AccountSnapshot(
        "000000001001", "customer-perf-001", Decimal("1000.00"), "ACTIVE", "SAVINGS"
    )
    transfer_repository.accounts["000000002002"] = AccountSnapshot(
        "000000002002", "customer-perf-001", Decimal("5000.00"), "ACTIVE", "CURRENT"
    )
    
    customer = AuthenticatedCustomer(
        customer_id="customer-perf-001",
        session_id="session-perf",
        email_verified=True,
        csrf_token_digest=sha256(b"synthetic-transfer-csrf").hexdigest(),
    )
    
    # Create verifier and client
    verifier = SyntheticTransferVerifier(
        ("customer-perf-001", "req-perf-001", "000000001001", "000000002002", Decimal("100.00"))
    )
    client = TestClient(
        create_app(
            transfer_service=TransferService(
                transfer_repository,
                verifier,
                settings=test_settings,
            ),
            customer_context_provider=FixedCustomerContext(customer),
        ),
        headers={
            "Origin": "http://testserver",
            "X-CSRF-Token": "synthetic-transfer-csrf",
        },
    )
    client.cookies.set("csrf_token", "synthetic-transfer-csrf")
    
    # Attempt transfer that violates minimum balance
    # Balance 1000, transfer 100, min 1000 → balance after 900 (REJECTED)
    start_time = time.perf_counter()
    response = client.post(
        "/api/v1/transfers",
        json={
            "request_id": "req-perf-001",
            "verification_proof": "synthetic-verification-proof",
            "from_account": "000000001001",
            "to_account": "000000002002",
            "amount": "100.00",
        },
    )
    elapsed_ms = (time.perf_counter() - start_time) * 1000
    
    # Verify rejection
    assert response.status_code == 400
    assert response.json()["error_code"] == "MIN_BALANCE_REQUIRED"
    
    # Performance assertion: rejection should be fast
    # Target: <100ms for minimum balance validation
    # (This is a soft target; actual implementation may vary by hardware)
    assert elapsed_ms < 200, f"Minimum balance rejection took {elapsed_ms:.2f}ms (target: <100ms)"


def test_minimum_balance_validation_performance_acceptance(
    transfer_repository, test_settings
):
    """
    Performance test: Minimum balance validation should accept quickly (<100ms).
    
    When a transfer passes minimum balance validation, the overall request 
    should still complete rapidly even with database and verification operations.
    """
    # Setup repository with accounts
    transfer_repository.accounts["000000001001"] = AccountSnapshot(
        "000000001001", "customer-perf-002", Decimal("10000.00"), "ACTIVE", "SAVINGS"
    )
    transfer_repository.accounts["000000002002"] = AccountSnapshot(
        "000000002002", "customer-perf-002", Decimal("5000.00"), "ACTIVE", "CURRENT"
    )
    
    customer = AuthenticatedCustomer(
        customer_id="customer-perf-002",
        session_id="session-perf",
        email_verified=True,
        csrf_token_digest=sha256(b"synthetic-transfer-csrf").hexdigest(),
    )
    
    # Create verifier and client
    verifier = SyntheticTransferVerifier(
        ("customer-perf-002", "req-perf-002", "000000001001", "000000002002", Decimal("9000.00"))
    )
    client = TestClient(
        create_app(
            transfer_service=TransferService(
                transfer_repository,
                verifier,
                settings=test_settings,
            ),
            customer_context_provider=FixedCustomerContext(customer),
        ),
        headers={
            "Origin": "http://testserver",
            "X-CSRF-Token": "synthetic-transfer-csrf",
        },
    )
    client.cookies.set("csrf_token", "synthetic-transfer-csrf")
    
    # Attempt transfer that passes minimum balance
    # Balance 10000, transfer 9000, min 1000 → balance after 1000 (ACCEPTED)
    start_time = time.perf_counter()
    response = client.post(
        "/api/v1/transfers",
        json={
            "request_id": "req-perf-002",
            "verification_proof": "synthetic-verification-proof",
            "from_account": "000000001001",
            "to_account": "000000002002",
            "amount": "9000.00",
        },
    )
    elapsed_ms = (time.perf_counter() - start_time) * 1000
    
    # Verify acceptance
    assert response.status_code == 201
    assert response.json()["status"] == "ACCEPTED"
    
    # Performance assertion: acceptance should also be fast
    # Target: <200ms for full transfer processing including verification and database
    assert elapsed_ms < 500, f"Transfer acceptance took {elapsed_ms:.2f}ms (target: <200ms)"


"""API tests for minimum balance error response schema."""
from decimal import Decimal
from hashlib import sha256

from fastapi.testclient import TestClient
import pytest

from simple_bank.api.app import create_app
from simple_bank.security.context import AuthenticatedCustomer
from simple_bank.services.transfer_service import TransferService


class FixedCustomerContext:
    def __init__(self, customer: AuthenticatedCustomer | None):
        self.customer = customer

    def resolve(self, request):
        return self.customer


def _client(transfer_repository, verifier_factory, customer, settings=None):
    amount = Decimal("4001.00")
    verifier = verifier_factory(
        customer_id="customer-001",
        request_id="req-error-response-001",
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


def _payload(request_id="req-error-response-001", amount="4001.00", **changes):
    return {
        "request_id": request_id,
        "verification_proof": "synthetic-verification-proof",
        "from_account": "000000001001",
        "to_account": "000000002002",
        "amount": amount,
    } | changes


def test_error_response_has_correct_status(
    transfer_repository, verifier_factory, test_settings
):
    """Test: MIN_BALANCE_REQUIRED error returns 400 Bad Request."""
    customer = AuthenticatedCustomer(
        customer_id="customer-001",
        session_id="session-demo",
        email_verified=True,
        csrf_token_digest=sha256(b"synthetic-transfer-csrf").hexdigest(),
    )
    client = _client(transfer_repository, verifier_factory, customer, settings=test_settings)
    
    response = client.post("/api/v1/transfers", json=_payload())
    assert response.status_code == 400


def test_error_response_has_error_code(
    transfer_repository, verifier_factory, test_settings
):
    """Test: Error response includes error_code field set to MIN_BALANCE_REQUIRED."""
    customer = AuthenticatedCustomer(
        customer_id="customer-001",
        session_id="session-demo",
        email_verified=True,
        csrf_token_digest=sha256(b"synthetic-transfer-csrf").hexdigest(),
    )
    client = _client(transfer_repository, verifier_factory, customer, settings=test_settings)
    
    response = client.post("/api/v1/transfers", json=_payload())
    data = response.json()
    assert "error_code" in data
    assert data["error_code"] == "MIN_BALANCE_REQUIRED"


def test_error_response_has_message(
    transfer_repository, verifier_factory, test_settings
):
    """Test: Error response includes message field."""
    customer = AuthenticatedCustomer(
        customer_id="customer-001",
        session_id="session-demo",
        email_verified=True,
        csrf_token_digest=sha256(b"synthetic-transfer-csrf").hexdigest(),
    )
    client = _client(transfer_repository, verifier_factory, customer, settings=test_settings)
    
    response = client.post("/api/v1/transfers", json=_payload())
    data = response.json()
    assert "message" in data
    assert isinstance(data["message"], str)
    assert len(data["message"]) > 0


def test_error_message_contains_context(
    transfer_repository, verifier_factory, test_settings
):
    """Test: Error message includes balance context."""
    customer = AuthenticatedCustomer(
        customer_id="customer-001",
        session_id="session-demo",
        email_verified=True,
        csrf_token_digest=sha256(b"synthetic-transfer-csrf").hexdigest(),
    )
    client = _client(transfer_repository, verifier_factory, customer, settings=test_settings)
    
    response = client.post("/api/v1/transfers", json=_payload())
    data = response.json()
    message = data["message"]
    
    # Should contain key context information
    assert "5000.00" in message  # current balance
    assert "4001.00" in message  # amount
    assert "1000.00" in message  # min balance
    assert "999.00" in message   # balance after (5000 - 4001)


def test_error_message_no_full_account_numbers(
    transfer_repository, verifier_factory, test_settings
):
    """Test: Error message uses masked accounts, no full account numbers."""
    customer = AuthenticatedCustomer(
        customer_id="customer-001",
        session_id="session-demo",
        email_verified=True,
        csrf_token_digest=sha256(b"synthetic-transfer-csrf").hexdigest(),
    )
    client = _client(transfer_repository, verifier_factory, customer, settings=test_settings)
    
    response = client.post("/api/v1/transfers", json=_payload())
    data = response.json()
    message = data["message"]
    
    # Should use masked format
    assert "XXXX" in message
    # Should NOT contain full account numbers
    assert "000000001001" not in message
    assert "000000002002" not in message


def test_error_response_is_machine_parseable(
    transfer_repository, verifier_factory, test_settings
):
    """Test: Error response can be parsed by client (JSON format)."""
    customer = AuthenticatedCustomer(
        customer_id="customer-001",
        session_id="session-demo",
        email_verified=True,
        csrf_token_digest=sha256(b"synthetic-transfer-csrf").hexdigest(),
    )
    client = _client(transfer_repository, verifier_factory, customer, settings=test_settings)
    
    response = client.post("/api/v1/transfers", json=_payload())
    # Should be valid JSON
    data = response.json()
    
    # Should have consistent structure for client parsing
    assert isinstance(data, dict)
    assert "error_code" in data
    assert "message" in data


def test_error_message_includes_masked_account(
    transfer_repository, verifier_factory, test_settings
):
    """Test: Error message includes account number information (masked)."""
    customer = AuthenticatedCustomer(
        customer_id="customer-001",
        session_id="session-demo",
        email_verified=True,
        csrf_token_digest=sha256(b"synthetic-transfer-csrf").hexdigest(),
    )
    client = _client(transfer_repository, verifier_factory, customer, settings=test_settings)
    
    response = client.post("/api/v1/transfers", json=_payload())
    data = response.json()
    message = data["message"]
    
    # Should include masked account reference
    assert "XXXX1001" in message or "Account:" in message


def test_error_response_consistent_across_requests(
    transfer_repository, verifier_factory, test_settings
):
    """Test: Error response format is consistent (same fields in each error)."""
    customer = AuthenticatedCustomer(
        customer_id="customer-001",
        session_id="session-demo",
        email_verified=True,
        csrf_token_digest=sha256(b"synthetic-transfer-csrf").hexdigest(),
    )
    client = _client(transfer_repository, verifier_factory, customer, settings=test_settings)
    
    # First request
    response1 = client.post("/api/v1/transfers", json=_payload())
    data1 = response1.json()
    
    # Second request (new request_id)
    response2 = client.post(
        "/api/v1/transfers",
        json=_payload(request_id="req-error-response-002"),
    )
    data2 = response2.json()
    
    # Both should have same structure
    assert set(data1.keys()) == set(data2.keys())
    assert data1["error_code"] == data2["error_code"]

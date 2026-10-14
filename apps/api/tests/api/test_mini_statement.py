"""API tests for mini statement endpoint."""
from datetime import UTC, datetime
from decimal import Decimal
from hashlib import sha256
from uuid import uuid4

from fastapi.testclient import TestClient
import pytest

from simple_bank.api.app import create_app
from simple_bank.persistence.models import Account, Customer, Transaction
from simple_bank.security.context import AuthenticatedCustomer
from simple_bank.persistence.database import create_database_engine, create_session_factory
from simple_bank.persistence.models import Base


class FixedCustomerContext:
    """Mock customer context provider for testing."""
    def __init__(self, customer: AuthenticatedCustomer | None):
        self.customer = customer

    def resolve(self, request):
        return self.customer


@pytest.fixture
def test_database():
    """Create a test database with mini statement test data."""
    # Use in-memory SQLite
    engine = create_database_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = create_session_factory(engine)
    
    # Seed with test data
    with session_factory() as session:
        # Create customers
        customer1 = Customer(customer_id="customer-001")
        customer2 = Customer(customer_id="customer-002")
        session.add_all([customer1, customer2])
        session.flush()
        
        # Create accounts
        account1 = Account(
            account_number="000000001001",
            customer_id="customer-001",
            balance=Decimal("3000.00"),
            status="ACTIVE",
            account_type="SAVINGS"
        )
        account2 = Account(
            account_number="000000002002",
            customer_id="customer-002",
            balance=Decimal("2000.00"),
            status="ACTIVE",
            account_type="CURRENT"
        )
        session.add_all([account1, account2])
        session.flush()
        
        # Create transactions
        txn1 = Transaction(
            transaction_id=str(uuid4()),
            customer_id="customer-001",
            request_id=f"req-{uuid4()}",
            from_account="000000001001",
            to_account="000000002002",
            amount=Decimal("500.00"),
            status="ACCEPTED",
            created_at=datetime(2026, 10, 14, 10, 0, 0, tzinfo=UTC)
        )
        txn2 = Transaction(
            transaction_id=str(uuid4()),
            customer_id="customer-002",
            request_id=f"req-{uuid4()}",
            from_account="000000002002",
            to_account="000000001001",
            amount=Decimal("300.00"),
            status="ACCEPTED",
            created_at=datetime(2026, 10, 14, 12, 0, 0, tzinfo=UTC)
        )
        txn3 = Transaction(
            transaction_id=str(uuid4()),
            customer_id="customer-001",
            request_id=f"req-{uuid4()}",
            from_account="000000001001",
            to_account="000000002002",
            amount=Decimal("200.00"),
            status="ACCEPTED",
            created_at=datetime(2026, 10, 14, 14, 0, 0, tzinfo=UTC)
        )
        session.add_all([txn1, txn2, txn3])
        session.commit()
        
        # Update account balances based on transactions
        # Account 001: started with 5000, sent 500, received 300, sent 200 = 4600
        # Account 002: started with 2000, received 500, sent 300, received 200 = 2400
        session.query(Account).filter(Account.account_number == "000000001001").update(
            {"balance": Decimal("4600.00")}
        )
        session.query(Account).filter(Account.account_number == "000000002002").update(
            {"balance": Decimal("2400.00")}
        )
        session.commit()
    
    yield session_factory
    engine.dispose()


def test_mini_statement_requires_authentication(test_database):
    """Test: Unauthenticated requests to mini statement get 401."""
    client = TestClient(
        create_app(
            customer_context_provider=FixedCustomerContext(None)
        )
    )
    
    response = client.get("/api/v1/accounts/000000001001/mini-statement")
    assert response.status_code == 401


def test_mini_statement_returns_404_for_unauthorized_account(test_database):
    """Test: Accessing another customer's account returns 404 (enumeration prevention)."""
    customer = AuthenticatedCustomer(
        customer_id="customer-001",
        session_id="session-demo",
        email_verified=True,
    )
    
    app = create_app(
        customer_context_provider=FixedCustomerContext(customer)
    )
    app.state.session_factory = test_database
    client = TestClient(app)
    
    # Customer 001 tries to access Customer 002's account
    response = client.get("/api/v1/accounts/000000002002/mini-statement")
    assert response.status_code == 404


def test_mini_statement_returns_404_for_nonexistent_account(test_database):
    """Test: Accessing a non-existent account returns 404."""
    customer = AuthenticatedCustomer(
        customer_id="customer-001",
        session_id="session-demo",
        email_verified=True,
    )
    
    app = create_app(
        customer_context_provider=FixedCustomerContext(customer)
    )
    app.state.session_factory = test_database
    client = TestClient(app)
    
    response = client.get("/api/v1/accounts/000000009999/mini-statement")
    assert response.status_code == 404


def test_mini_statement_happy_path(test_database):
    """Test: Authorized customer gets mini statement with last 3 transactions."""
    customer = AuthenticatedCustomer(
        customer_id="customer-001",
        session_id="session-demo",
        email_verified=True,
    )
    
    app = create_app(
        customer_context_provider=FixedCustomerContext(customer)
    )
    app.state.session_factory = test_database
    client = TestClient(app)
    
    response = client.get("/api/v1/accounts/000000001001/mini-statement")
    assert response.status_code == 200
    
    data = response.json()
    assert data["account_number"] == "XXXX1001"
    assert data["current_balance"] == "4600.00"
    assert len(data["transactions"]) == 3
    
    # Verify account number is masked
    assert data["account_number"].startswith("XXXX")
    assert not data["account_number"].startswith("00000000")


def test_mini_statement_account_number_masking(test_database):
    """Test: Account numbers are masked in response."""
    customer = AuthenticatedCustomer(
        customer_id="customer-001",
        session_id="session-demo",
        email_verified=True,
    )
    
    app = create_app(
        customer_context_provider=FixedCustomerContext(customer)
    )
    app.state.session_factory = test_database
    client = TestClient(app)
    
    response = client.get("/api/v1/accounts/000000001001/mini-statement")
    assert response.status_code == 200
    
    data = response.json()
    # Main account number masked
    assert data["account_number"] == "XXXX1001"
    
    # Other account numbers in transactions masked
    for txn in data["transactions"]:
        assert "XXXX" in txn["description"]
        assert not "00000000" in txn["description"]


def test_mini_statement_decimal_precision(test_database):
    """Test: All monetary amounts use exactly 2 decimal places."""
    customer = AuthenticatedCustomer(
        customer_id="customer-001",
        session_id="session-demo",
        email_verified=True,
    )
    
    app = create_app(
        customer_context_provider=FixedCustomerContext(customer)
    )
    app.state.session_factory = test_database
    client = TestClient(app)
    
    response = client.get("/api/v1/accounts/000000001001/mini-statement")
    assert response.status_code == 200
    
    data = response.json()
    # Current balance has 2 decimal places
    assert data["current_balance"].count(".") == 1
    parts = data["current_balance"].split(".")
    assert len(parts[1]) == 2
    
    # Transaction amounts have 2 decimal places
    for txn in data["transactions"]:
        amount_parts = txn["amount"].split(".")
        assert len(amount_parts[1]) == 2
        
        balance_parts = txn["balance_after"].split(".")
        assert len(balance_parts[1]) == 2


def test_mini_statement_transaction_classification(test_database):
    """Test: Transactions are classified as DEBIT or CREDIT correctly."""
    customer = AuthenticatedCustomer(
        customer_id="customer-001",
        session_id="session-demo",
        email_verified=True,
    )
    
    app = create_app(
        customer_context_provider=FixedCustomerContext(customer)
    )
    app.state.session_factory = test_database
    client = TestClient(app)
    
    response = client.get("/api/v1/accounts/000000001001/mini-statement")
    assert response.status_code == 200
    
    data = response.json()
    # Account 001 sent 500 (DEBIT), received 300 (CREDIT), sent 200 (DEBIT)
    # In newest-first order: DEBIT (200), CREDIT (300), DEBIT (500)
    assert data["transactions"][0]["type"] == "DEBIT"
    assert data["transactions"][0]["amount"] == "200.00"
    
    assert data["transactions"][1]["type"] == "CREDIT"
    assert data["transactions"][1]["amount"] == "300.00"
    
    assert data["transactions"][2]["type"] == "DEBIT"
    assert data["transactions"][2]["amount"] == "500.00"


def test_mini_statement_iso8601_timestamps(test_database):
    """Test: Timestamps are ISO 8601 format with IST timezone."""
    customer = AuthenticatedCustomer(
        customer_id="customer-001",
        session_id="session-demo",
        email_verified=True,
    )
    
    app = create_app(
        customer_context_provider=FixedCustomerContext(customer)
    )
    app.state.session_factory = test_database
    client = TestClient(app)
    
    response = client.get("/api/v1/accounts/000000001001/mini-statement")
    assert response.status_code == 200
    
    data = response.json()
    for txn in data["transactions"]:
        timestamp = txn["timestamp"]
        # Should end with +05:30 (IST timezone offset)
        assert timestamp.endswith("+05:30"), f"Expected IST offset, got {timestamp}"
        # Should have T between date and time
        assert "T" in timestamp


def test_mini_statement_newest_first_ordering(test_database):
    """Test: Transactions are ordered newest first."""
    customer = AuthenticatedCustomer(
        customer_id="customer-001",
        session_id="session-demo",
        email_verified=True,
    )
    
    app = create_app(
        customer_context_provider=FixedCustomerContext(customer)
    )
    app.state.session_factory = test_database
    client = TestClient(app)
    
    response = client.get("/api/v1/accounts/000000001001/mini-statement")
    assert response.status_code == 200
    
    data = response.json()
    # Transactions should be in order: most recent first
    # Created order: 10:00 (500), 12:00 (300), 14:00 (200)
    # Response order should be: 14:00, 12:00, 10:00
    assert data["transactions"][0]["amount"] == "200.00"  # 14:00
    assert data["transactions"][1]["amount"] == "300.00"  # 12:00
    assert data["transactions"][2]["amount"] == "500.00"  # 10:00

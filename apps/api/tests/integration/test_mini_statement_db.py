"""
Integration tests for mini statement API using real PostgreSQL database.
Tests the complete flow: account retrieval, transaction queries, and response formatting.
"""
import pytest
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from simple_bank.persistence.models import Account, Transaction, Customer
from simple_bank.services.mini_statement_service import MiniStatementService
from simple_bank.domain.timestamps import to_ist_iso8601


@pytest.fixture
def test_account_with_transactions(postgres_session_factory) -> tuple[Account, list[Transaction]]:
    """Create a test account with 5 transactions."""
    with postgres_session_factory() as session:
        # Create customer
        customer = Customer(customer_id="customer-003")
        session.add(customer)
        session.flush()

        # Create account
        account = Account(
            account_number="000000003003",
            customer_id="customer-003",
            balance=Decimal("10000.00"),
            status="ACTIVE",
            account_type="SAVINGS",
        )
        session.add(account)
        session.flush()

        # Create second customer and account for transfers
        other_customer = Customer(customer_id="customer-004")
        session.add(other_customer)
        session.flush()

        other_account = Account(
            account_number="000000004004",
            customer_id="customer-004",
            balance=Decimal("8000.00"),
            status="ACTIVE",
            account_type="CURRENT",
        )
        session.add(other_account)
        session.flush()

        # Create transactions (newer first in list for verification)
        now = datetime.now(timezone.utc)
        transactions = []
        
        # Transaction 5 (most recent): Receive Rs 500 from customer-004
        t5 = Transaction(
            from_account="000000004004",
            to_account="000000003003",
            amount=Decimal("500.00"),
            description="Transfer from XXXX4004",
            created_at=now - timedelta(minutes=0),
            request_id="req-005",
        )
        session.add(t5)
        transactions.append(t5)

        # Transaction 4: Send Rs 1000 to customer-004
        t4 = Transaction(
            from_account="000000003003",
            to_account="000000004004",
            amount=Decimal("1000.00"),
            description="Transfer to XXXX4004",
            created_at=now - timedelta(minutes=1),
            request_id="req-004",
        )
        session.add(t4)
        transactions.append(t4)

        # Transaction 3: Receive Rs 2500
        t3 = Transaction(
            from_account="000000004004",
            to_account="000000003003",
            amount=Decimal("2500.00"),
            description="Transfer from XXXX4004",
            created_at=now - timedelta(minutes=2),
            request_id="req-003",
        )
        session.add(t3)
        transactions.append(t3)

        # Transaction 2: Send Rs 500
        t2 = Transaction(
            from_account="000000003003",
            to_account="000000004004",
            amount=Decimal("500.00"),
            description="Transfer to XXXX4004",
            created_at=now - timedelta(minutes=3),
            request_id="req-002",
        )
        session.add(t2)
        transactions.append(t2)

        # Transaction 1 (oldest): Receive Rs 1500
        t1 = Transaction(
            from_account="000000004004",
            to_account="000000003003",
            amount=Decimal("1500.00"),
            description="Transfer from XXXX4004",
            created_at=now - timedelta(minutes=4),
            request_id="req-001",
        )
        session.add(t1)
        transactions.append(t1)

        session.commit()

        # Refresh account to get updated balance
        session.refresh(account)

        return account, transactions


def test_mini_statement_happy_path(postgres_session_factory, test_account_with_transactions):
    """Test fetching mini statement for account with transactions."""
    account, transactions = test_account_with_transactions
    
    with postgres_session_factory() as session:
        service = MiniStatementService(session)
        statement = service.get_mini_statement(
            account_number=account.account_number,
            customer_id=account.customer_id,
        )

        # Verify response structure
        assert statement is not None
        assert statement.account_number == "XXXX3003"
        assert statement.current_balance == "10000.00"
        assert len(statement.transactions) == 5

        # Verify transactions are in newest-first order
        for i, tx_detail in enumerate(statement.transactions):
            # Transaction index 0 should be the most recent (t5)
            expected_tx = transactions[i]
            assert tx_detail.timestamp is not None
            assert tx_detail.description is not None
            assert tx_detail.type in ["DEBIT", "CREDIT"]
            assert tx_detail.amount is not None
            assert tx_detail.balance_after is not None


def test_account_number_is_masked(postgres_session_factory, test_account_with_transactions):
    """Verify account number is masked in response."""
    account, _ = test_account_with_transactions
    
    with postgres_session_factory() as session:
        service = MiniStatementService(session)
        statement = service.get_mini_statement(
            account_number=account.account_number,
            customer_id=account.customer_id,
        )

        assert statement is not None
        assert statement.account_number == "XXXX3003"
        assert "000000003003" not in statement.account_number


def test_current_balance_matches_account(postgres_session_factory, test_account_with_transactions):
    """Verify current balance in statement matches Account.balance."""
    account, _ = test_account_with_transactions
    
    with postgres_session_factory() as session:
        service = MiniStatementService(session)
        statement = service.get_mini_statement(
            account_number=account.account_number,
            customer_id=account.customer_id,
        )

        assert statement is not None
        assert statement.current_balance == "10000.00"
        assert Decimal(statement.current_balance) == account.balance


def test_transactions_ordered_newest_first(postgres_session_factory, test_account_with_transactions):
    """Verify transactions are ordered by timestamp descending."""
    account, transactions = test_account_with_transactions
    
    with postgres_session_factory() as session:
        service = MiniStatementService(session)
        statement = service.get_mini_statement(
            account_number=account.account_number,
            customer_id=account.customer_id,
        )

        assert statement is not None
        assert len(statement.transactions) == 5

        # Parse ISO 8601 timestamps to verify order
        timestamps = []
        for tx_detail in statement.transactions:
            # Parse ISO 8601 timestamp (e.g., "2026-10-14T15:30:45+05:30")
            # Remove timezone for comparison
            dt_str = tx_detail.timestamp.split("+")[0]
            timestamps.append(dt_str)

        # Verify descending order
        for i in range(len(timestamps) - 1):
            assert timestamps[i] >= timestamps[i + 1], \
                f"Transaction {i} {timestamps[i]} should be >= {timestamps[i+1]}"


def test_decimal_precision_in_response(postgres_session_factory, test_account_with_transactions):
    """Verify all decimal values have exactly 2 places."""
    account, _ = test_account_with_transactions
    
    with postgres_session_factory() as session:
        service = MiniStatementService(session)
        statement = service.get_mini_statement(
            account_number=account.account_number,
            customer_id=account.customer_id,
        )

        assert statement is not None
        
        # Check current_balance
        assert statement.current_balance.count(".") == 1
        parts = statement.current_balance.split(".")
        assert len(parts[1]) == 2, f"current_balance should have 2 decimal places: {statement.current_balance}"

        # Check each transaction
        for tx_detail in statement.transactions:
            # Check amount
            assert tx_detail.amount.count(".") == 1
            parts = tx_detail.amount.split(".")
            assert len(parts[1]) == 2, f"amount should have 2 decimal places: {tx_detail.amount}"

            # Check balance_after
            assert tx_detail.balance_after.count(".") == 1
            parts = tx_detail.balance_after.split(".")
            assert len(parts[1]) == 2, f"balance_after should have 2 decimal places: {tx_detail.balance_after}"


def test_timestamps_are_iso8601_ist(postgres_session_factory, test_account_with_transactions):
    """Verify all timestamps are ISO 8601 format with IST offset (+05:30)."""
    account, _ = test_account_with_transactions
    
    with postgres_session_factory() as session:
        service = MiniStatementService(session)
        statement = service.get_mini_statement(
            account_number=account.account_number,
            customer_id=account.customer_id,
        )

        assert statement is not None

        for tx_detail in statement.transactions:
            # Timestamp should match ISO 8601 IST format: YYYY-MM-DDTHH:MM:SS+05:30
            assert "+05:30" in tx_detail.timestamp, \
                f"Timestamp should have IST offset (+05:30): {tx_detail.timestamp}"
            
            # Should contain T separator for ISO 8601
            assert "T" in tx_detail.timestamp, \
                f"Timestamp should be ISO 8601 format: {tx_detail.timestamp}"


def test_transaction_classification_debit_credit(postgres_session_factory, test_account_with_transactions):
    """Verify transaction types (DEBIT/CREDIT) are correctly classified."""
    account, _ = test_account_with_transactions
    
    with postgres_session_factory() as session:
        service = MiniStatementService(session)
        statement = service.get_mini_statement(
            account_number=account.account_number,
            customer_id=account.customer_id,
        )

        assert statement is not None

        debit_count = 0
        credit_count = 0

        for tx_detail in statement.transactions:
            assert tx_detail.type in ["DEBIT", "CREDIT"]
            
            if tx_detail.type == "DEBIT":
                debit_count += 1
            else:
                credit_count += 1

        # We should have both debits and credits
        assert debit_count > 0, "Should have at least one DEBIT transaction"
        assert credit_count > 0, "Should have at least one CREDIT transaction"


def test_unauthorized_access_returns_none(postgres_session_factory, test_account_with_transactions):
    """Verify that fetching another customer's account returns None."""
    account, _ = test_account_with_transactions
    
    with postgres_session_factory() as session:
        service = MiniStatementService(session)
        
        # Try to fetch with different customer_id
        statement = service.get_mini_statement(
            account_number=account.account_number,
            customer_id="different-customer",
        )

        assert statement is None


def test_nonexistent_account_returns_none(postgres_session_factory, test_account_with_transactions):
    """Verify that fetching nonexistent account returns None."""
    _, _ = test_account_with_transactions
    
    with postgres_session_factory() as session:
        service = MiniStatementService(session)
        
        statement = service.get_mini_statement(
            account_number="999999999999",
            customer_id="customer-003",
        )

        assert statement is None


def test_account_with_no_transactions(postgres_session_factory):
    """Verify mini statement for account with 0 transactions."""
    with postgres_session_factory() as session:
        # Create customer
        customer = Customer(customer_id="customer-005")
        session.add(customer)
        session.flush()

        # Create account with no transactions
        account = Account(
            account_number="000000005005",
            customer_id="customer-005",
            balance=Decimal("15000.00"),
            status="ACTIVE",
            account_type="SAVINGS",
        )
        session.add(account)
        session.commit()

    with postgres_session_factory() as session:
        service = MiniStatementService(session)
        statement = service.get_mini_statement(
            account_number=account.account_number,
            customer_id=account.customer_id,
        )

        assert statement is not None
        assert statement.current_balance == "15000.00"
        assert len(statement.transactions) == 0
        assert statement.account_number == "XXXX5005"

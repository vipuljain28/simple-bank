"""Unit tests for mini statement response schemas."""
import pytest
from decimal import Decimal
from pydantic import ValidationError

from simple_bank.api.schemas.mini_statement_schema import (
    TransactionDetail,
    MiniStatementResponse,
)


class TestTransactionDetail:
    """Tests for TransactionDetail schema."""
    
    def test_valid_transaction_detail(self):
        """Test: Valid transaction detail serializes correctly."""
        txn = TransactionDetail(
            timestamp="2026-10-14T15:30:45+05:30",
            type="DEBIT",
            amount="1000.00",
            balance_after="4000.00",
            description="Transfer to XXXX5678"
        )
        assert txn.timestamp == "2026-10-14T15:30:45+05:30"
        assert txn.type == "DEBIT"
        assert txn.amount == "1000.00"
        assert txn.balance_after == "4000.00"
        assert txn.description == "Transfer to XXXX5678"
    
    def test_transaction_type_must_be_debit_or_credit(self):
        """Test: Transaction type is enum-validated."""
        with pytest.raises(ValidationError):
            TransactionDetail(
                timestamp="2026-10-14T15:30:45+05:30",
                type="INVALID",
                amount="1000.00",
                balance_after="4000.00",
                description="Transfer"
            )
    
    def test_amount_must_have_two_decimal_places(self):
        """Test: Amount must be a string with exactly 2 decimal places."""
        # Valid: 1000.00
        txn = TransactionDetail(
            timestamp="2026-10-14T15:30:45+05:30",
            type="DEBIT",
            amount="1000.00",
            balance_after="4000.00",
            description="Transfer"
        )
        assert txn.amount == "1000.00"
        
        # Invalid: 1000.5 (only 1 decimal place)
        with pytest.raises(ValidationError):
            TransactionDetail(
                timestamp="2026-10-14T15:30:45+05:30",
                type="DEBIT",
                amount="1000.5",
                balance_after="4000.00",
                description="Transfer"
            )
        
        # Invalid: 1000 (no decimal point)
        with pytest.raises(ValidationError):
            TransactionDetail(
                timestamp="2026-10-14T15:30:45+05:30",
                type="DEBIT",
                amount="1000",
                balance_after="4000.00",
                description="Transfer"
            )
    
    def test_balance_after_must_have_two_decimal_places(self):
        """Test: balance_after must have exactly 2 decimal places."""
        # Invalid: 4000.5
        with pytest.raises(ValidationError):
            TransactionDetail(
                timestamp="2026-10-14T15:30:45+05:30",
                type="DEBIT",
                amount="1000.00",
                balance_after="4000.5",
                description="Transfer"
            )
    
    def test_timestamp_must_be_iso8601_with_ist_offset(self):
        """Test: Timestamp must be ISO 8601 with IST (+05:30) offset."""
        # Invalid: wrong offset
        with pytest.raises(ValidationError):
            TransactionDetail(
                timestamp="2026-10-14T15:30:45+00:00",
                type="DEBIT",
                amount="1000.00",
                balance_after="4000.00",
                description="Transfer"
            )
        
        # Invalid: no offset
        with pytest.raises(ValidationError):
            TransactionDetail(
                timestamp="2026-10-14T15:30:45",
                type="DEBIT",
                amount="1000.00",
                balance_after="4000.00",
                description="Transfer"
            )


class TestMiniStatementResponse:
    """Tests for MiniStatementResponse schema."""
    
    def test_valid_mini_statement_response(self):
        """Test: Valid mini statement response."""
        response = MiniStatementResponse(
            account_number="XXXX1001",
            current_balance="5000.00",
            transactions=[
                TransactionDetail(
                    timestamp="2026-10-14T15:30:45+05:30",
                    type="CREDIT",
                    amount="500.00",
                    balance_after="5000.00",
                    description="Transfer from XXXX2002"
                )
            ]
        )
        assert response.account_number == "XXXX1001"
        assert response.current_balance == "5000.00"
        assert len(response.transactions) == 1
        assert response.transactions[0].type == "CREDIT"
    
    def test_account_number_must_be_masked_xxxx_format(self):
        """Test: Account number must be masked (XXXX + 4 digits)."""
        # Invalid: no XXXX prefix
        with pytest.raises(ValidationError):
            MiniStatementResponse(
                account_number="123456789",
                current_balance="5000.00"
            )
        
        # Invalid: wrong length
        with pytest.raises(ValidationError):
            MiniStatementResponse(
                account_number="XXXX123",
                current_balance="5000.00"
            )
        
        # Invalid: non-digits after XXXX
        with pytest.raises(ValidationError):
            MiniStatementResponse(
                account_number="XXXXABCD",
                current_balance="5000.00"
            )
    
    def test_current_balance_must_have_two_decimal_places(self):
        """Test: current_balance must be string with 2 decimal places."""
        # Valid
        response = MiniStatementResponse(
            account_number="XXXX1001",
            current_balance="5000.00"
        )
        assert response.current_balance == "5000.00"
        
        # Invalid: 1 decimal place
        with pytest.raises(ValidationError):
            MiniStatementResponse(
                account_number="XXXX1001",
                current_balance="5000.5"
            )
    
    def test_transactions_default_to_empty_list(self):
        """Test: transactions default to empty list."""
        response = MiniStatementResponse(
            account_number="XXXX1001",
            current_balance="5000.00"
        )
        assert response.transactions == []
    
    def test_transactions_max_10_items(self):
        """Test: transactions list is limited to 10 items."""
        # Create 11 transactions
        transactions = [
            TransactionDetail(
                timestamp="2026-10-14T15:30:45+05:30",
                type="DEBIT",
                amount=f"{i}.00",
                balance_after=f"{5000 - i}.00",
                description=f"Transaction {i}"
            )
            for i in range(1, 12)
        ]
        
        # Should fail validation
        with pytest.raises(ValueError, match="Max 10 transactions"):
            MiniStatementResponse(
                account_number="XXXX1001",
                current_balance="5000.00",
                transactions=transactions
            )
        
        # 10 should be OK
        response = MiniStatementResponse(
            account_number="XXXX1001",
            current_balance="5000.00",
            transactions=transactions[:10]
        )
        assert len(response.transactions) == 10
    
    def test_all_amounts_are_strings_not_floats(self):
        """Test: Decimal values are strings, not floats (no float representation)."""
        response = MiniStatementResponse(
            account_number="XXXX1001",
            current_balance="1234.56",
            transactions=[
                TransactionDetail(
                    timestamp="2026-10-14T15:30:45+05:30",
                    type="DEBIT",
                    amount="999.99",
                    balance_after="234.57",
                    description="Transfer"
                )
            ]
        )
        
        # All amounts should be strings
        assert isinstance(response.current_balance, str)
        assert isinstance(response.transactions[0].amount, str)
        assert isinstance(response.transactions[0].balance_after, str)
        
        # No float representation issues
        assert response.current_balance == "1234.56"
        assert response.transactions[0].amount == "999.99"


class TestMiniStatementSerialization:
    """Tests for JSON serialization."""
    
    def test_mini_statement_serializes_to_valid_json(self):
        """Test: MiniStatementResponse serializes to valid JSON."""
        response = MiniStatementResponse(
            account_number="XXXX1001",
            current_balance="5000.00",
            transactions=[
                TransactionDetail(
                    timestamp="2026-10-14T15:30:45+05:30",
                    type="CREDIT",
                    amount="500.00",
                    balance_after="5000.00",
                    description="Salary Deposit"
                ),
                TransactionDetail(
                    timestamp="2026-10-14T14:20:30+05:30",
                    type="DEBIT",
                    amount="100.00",
                    balance_after="4500.00",
                    description="Transfer to XXXX2002"
                )
            ]
        )
        
        json_data = response.model_dump()
        
        # Verify structure
        assert json_data["account_number"] == "XXXX1001"
        assert json_data["current_balance"] == "5000.00"
        assert len(json_data["transactions"]) == 2
        assert json_data["transactions"][0]["type"] == "CREDIT"
        assert json_data["transactions"][1]["type"] == "DEBIT"
        
        # Verify amounts are strings (not floats)
        assert isinstance(json_data["transactions"][0]["amount"], str)
        assert json_data["transactions"][0]["amount"] == "500.00"

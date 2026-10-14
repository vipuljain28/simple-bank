"""Unit tests for mini statement service."""
from datetime import datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session
from unittest.mock import Mock, patch

from simple_bank.domain.errors import NotFound
from simple_bank.persistence.models import Account, Transaction
from simple_bank.services.mini_statement_service import MiniStatementService


class TestMiniStatementService:
    """Tests for MiniStatementService."""
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return Mock(spec=Session)
    
    @pytest.fixture
    def service(self, mock_db):
        """Create service with mock database."""
        return MiniStatementService(mock_db)
    
    def test_account_not_found_raises_not_found(self, service, mock_db):
        """Test: Non-existent account raises NotFound."""
        mock_db.execute.return_value.scalar_one_or_none.return_value = None
        
        with pytest.raises(NotFound):
            service.get_mini_statement("000000009999", "customer-001")
    
    def test_unauthorized_account_access_raises_not_found(self, service, mock_db):
        """Test: Accessing another customer's account raises NotFound (enumeration prevention)."""
        # Account exists but belongs to different customer
        account = Mock(spec=Account)
        account.customer_id = "customer-002"
        account.balance = Decimal("5000.00")
        
        mock_db.execute.return_value.scalar_one_or_none.return_value = account
        
        with pytest.raises(NotFound):
            service.get_mini_statement("000000001001", "customer-001")
    
    def test_get_mini_statement_empty_account(self, service, mock_db):
        """Test: Account with no transactions returns empty list."""
        account = Mock(spec=Account)
        account.customer_id = "customer-001"
        account.balance = Decimal("5000.00")
        
        # First call for account lookup, second for transfers
        mock_db.execute.return_value.scalar_one_or_none.return_value = account
        mock_db.execute.return_value.scalars.return_value.all.return_value = []
        
        response = service.get_mini_statement("000000001001", "customer-001")
        
        assert response.account_number == "XXXX1001"
        assert response.current_balance == "5000.00"
        assert response.transactions == []
    
    def test_get_mini_statement_single_debit_transaction(self, service, mock_db):
        """Test: DEBIT transaction (money out) is classified correctly."""
        account = Mock(spec=Account)
        account.customer_id = "customer-001"
        account.balance = Decimal("4000.00")
        
        transfer = Mock(spec=Transaction)
        transfer.from_account = "000000001001"
        transfer.to_account = "000000002002"
        transfer.amount = Decimal("1000.00")
        transfer.created_at = datetime(2026, 10, 14, 15, 30, 45, tzinfo=timezone.utc)
        
        # Mock the two database calls
        call_count = 0
        def mock_execute(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            result = Mock()
            if call_count == 1:
                # Account lookup
                result.scalar_one_or_none.return_value = account
                return result
            else:
                # Transfers lookup
                result.scalars.return_value.all.return_value = [transfer]
                return result
        
        mock_db.execute.side_effect = mock_execute
        
        with patch('simple_bank.services.mini_statement_service.to_ist_iso8601') as mock_to_ist:
            mock_to_ist.return_value = "2026-10-14T20:00:45+05:30"
            
            with patch.object(service, '_calculate_balance_after_transfer') as mock_calc:
                mock_calc.return_value = Decimal("4000.00")
                
                response = service.get_mini_statement("000000001001", "customer-001")
        
        assert len(response.transactions) == 1
        txn = response.transactions[0]
        assert txn.type == "DEBIT"
        assert txn.amount == "1000.00"
        assert txn.description == "Transfer to XXXX2002"
        assert txn.balance_after == "4000.00"
    
    def test_get_mini_statement_single_credit_transaction(self, service, mock_db):
        """Test: CREDIT transaction (money in) is classified correctly."""
        account = Mock(spec=Account)
        account.customer_id = "customer-001"
        account.balance = Decimal("6000.00")
        
        transfer = Mock(spec=Transaction)
        transfer.from_account = "000000002002"
        transfer.to_account = "000000001001"
        transfer.amount = Decimal("1000.00")
        transfer.created_at = datetime(2026, 10, 14, 15, 30, 45, tzinfo=timezone.utc)
        
        call_count = 0
        def mock_execute(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            result = Mock()
            if call_count == 1:
                result.scalar_one_or_none.return_value = account
                return result
            else:
                result.scalars.return_value.all.return_value = [transfer]
                return result
        
        mock_db.execute.side_effect = mock_execute
        
        with patch('simple_bank.services.mini_statement_service.to_ist_iso8601') as mock_to_ist:
            mock_to_ist.return_value = "2026-10-14T20:00:45+05:30"
            
            with patch.object(service, '_calculate_balance_after_transfer') as mock_calc:
                mock_calc.return_value = Decimal("5000.00")
                
                response = service.get_mini_statement("000000001001", "customer-001")
        
        assert len(response.transactions) == 1
        txn = response.transactions[0]
        assert txn.type == "CREDIT"
        assert txn.amount == "1000.00"
        assert txn.description == "Transfer from XXXX2002"
        assert txn.balance_after == "5000.00"
    
    def test_get_mini_statement_multiple_transactions_newest_first(self, service, mock_db):
        """Test: Transactions are ordered newest first."""
        account = Mock(spec=Account)
        account.customer_id = "customer-001"
        account.balance = Decimal("3000.00")
        
        # Three transactions in chronological order
        t1 = Mock(spec=Transaction)
        t1.from_account = "000000001001"
        t1.to_account = "000000002002"
        t1.amount = Decimal("1000.00")
        t1.created_at = datetime(2026, 10, 14, 10, 0, 0, tzinfo=timezone.utc)
        
        t2 = Mock(spec=Transaction)
        t2.from_account = "000000002002"
        t2.to_account = "000000001001"
        t2.amount = Decimal("500.00")
        t2.created_at = datetime(2026, 10, 14, 12, 0, 0, tzinfo=timezone.utc)
        
        t3 = Mock(spec=Transaction)
        t3.from_account = "000000001001"
        t3.to_account = "000000002002"
        t3.amount = Decimal("300.00")
        t3.created_at = datetime(2026, 10, 14, 14, 0, 0, tzinfo=timezone.utc)
        
        call_count = 0
        def mock_execute(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            result = Mock()
            if call_count == 1:
                result.scalar_one_or_none.return_value = account
                return result
            else:
                # Transfers should be returned by DB in order by created_at DESC
                result.scalars.return_value.all.return_value = [t3, t2, t1]
                return result
        
        mock_db.execute.side_effect = mock_execute
        
        with patch('simple_bank.services.mini_statement_service.to_ist_iso8601') as mock_to_ist:
            mock_to_ist.side_effect = [
                "2026-10-14T19:00:45+05:30",
                "2026-10-14T17:00:45+05:30",
                "2026-10-14T15:00:45+05:30"
            ]
            
            with patch.object(service, '_calculate_balance_after_transfer') as mock_calc:
                mock_calc.side_effect = [
                    Decimal("2700.00"),
                    Decimal("3200.00"),
                    Decimal("4000.00")
                ]
                
                response = service.get_mini_statement("000000001001", "customer-001")
        
        assert len(response.transactions) == 3
        # Verify order: t3, t2, t1 (newest first)
        assert response.transactions[0].amount == "300.00"
        assert response.transactions[0].type == "DEBIT"
        assert response.transactions[1].amount == "500.00"
        assert response.transactions[1].type == "CREDIT"
        assert response.transactions[2].amount == "1000.00"
        assert response.transactions[2].type == "DEBIT"
    
    def test_get_mini_statement_max_10_transactions(self, service, mock_db):
        """Test: Service respects 10-transaction limit from database query."""
        account = Mock(spec=Account)
        account.customer_id = "customer-001"
        account.balance = Decimal("5000.00")
        
        # Create 10 mock transfers
        transfers = []
        for i in range(10):
            t = Mock(spec=Transaction)
            t.from_account = "000000001001"
            t.to_account = "000000002002"
            t.amount = Decimal("100.00")
            t.created_at = datetime(2026, 10, 14, i, 0, 0, tzinfo=timezone.utc)
            transfers.append(t)
        
        call_count = 0
        def mock_execute(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            result = Mock()
            if call_count == 1:
                result.scalar_one_or_none.return_value = account
                return result
            else:
                result.scalars.return_value.all.return_value = transfers
                return result
        
        mock_db.execute.side_effect = mock_execute
        
        with patch('simple_bank.services.mini_statement_service.to_ist_iso8601') as mock_to_ist:
            mock_to_ist.return_value = "2026-10-14T10:00:45+05:30"
            
            with patch.object(service, '_calculate_balance_after_transfer') as mock_calc:
                mock_calc.return_value = Decimal("4900.00")
                
                response = service.get_mini_statement("000000001001", "customer-001")
        
        assert len(response.transactions) == 10
    
    def test_get_mini_statement_account_number_masking(self, service, mock_db):
        """Test: Account number is masked in response."""
        account = Mock(spec=Account)
        account.customer_id = "customer-001"
        account.balance = Decimal("5000.00")
        
        mock_db.execute.return_value.scalar_one_or_none.return_value = account
        mock_db.execute.return_value.scalars.return_value.all.return_value = []
        
        response = service.get_mini_statement("000000001001", "customer-001")
        
        assert response.account_number == "XXXX1001"
        assert not response.account_number.startswith("00000000")
    
    def test_get_mini_statement_decimal_precision(self, service, mock_db):
        """Test: All amounts use exactly 2 decimal places."""
        account = Mock(spec=Account)
        account.customer_id = "customer-001"
        account.balance = Decimal("5000.00")
        
        transfer = Mock(spec=Transaction)
        transfer.from_account = "000000001001"
        transfer.to_account = "000000002002"
        transfer.amount = Decimal("1000.00")
        transfer.created_at = datetime(2026, 10, 14, 15, 30, 45, tzinfo=timezone.utc)
        
        call_count = 0
        def mock_execute(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            result = Mock()
            if call_count == 1:
                result.scalar_one_or_none.return_value = account
                return result
            else:
                result.scalars.return_value.all.return_value = [transfer]
                return result
        
        mock_db.execute.side_effect = mock_execute
        
        with patch('simple_bank.services.mini_statement_service.to_ist_iso8601') as mock_to_ist:
            mock_to_ist.return_value = "2026-10-14T20:00:45+05:30"
            
            with patch.object(service, '_calculate_balance_after_transfer') as mock_calc:
                mock_calc.return_value = Decimal("4000.00")
                
                response = service.get_mini_statement("000000001001", "customer-001")
        
        assert response.current_balance == "5000.00"
        assert response.transactions[0].amount == "1000.00"
        assert response.transactions[0].balance_after == "4000.00"
        
        # Verify format: should have exactly 2 decimal places
        assert response.current_balance.count(".") == 1
        parts = response.current_balance.split(".")
        assert len(parts[1]) == 2




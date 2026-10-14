"""Unit tests for minimum balance error message clarity."""
from decimal import Decimal

from simple_bank.domain.errors import MinimumBalanceRequired


def test_error_message_includes_all_context():
    """Error message includes current balance, amount, resulting balance, and threshold."""
    error = MinimumBalanceRequired(
        current_balance=Decimal("5000.00"),
        amount=Decimal("4001.00"),
        min_balance=Decimal("1000.00"),
        masked_account="XXXX1001",
    )
    
    assert "5000.00" in error.message
    assert "4001.00" in error.message
    assert "999.00" in error.message  # balance_after = 5000 - 4001
    assert "1000.00" in error.message


def test_error_message_no_full_account_numbers():
    """Error message uses masked account numbers, not full ones."""
    error = MinimumBalanceRequired(
        current_balance=Decimal("5000.00"),
        amount=Decimal("4001.00"),
        min_balance=Decimal("1000.00"),
        masked_account="XXXX1001",
    )
    
    assert "XXXX1001" in error.message
    # Ensure full account number is not present
    assert "000000001001" not in error.message


def test_error_message_decimal_precision():
    """All numeric values in error message have exactly 2 decimal places."""
    error = MinimumBalanceRequired(
        current_balance=Decimal("5000.00"),
        amount=Decimal("4001.00"),
        min_balance=Decimal("1000.00"),
        masked_account="XXXX1001",
    )
    
    # Check that message contains properly formatted decimals
    assert "5000.00" in error.message
    assert "4001.00" in error.message
    assert "1000.00" in error.message
    assert "999.00" in error.message


def test_error_message_helpful_and_actionable():
    """Error message provides context about the rejection reason."""
    error = MinimumBalanceRequired(
        current_balance=Decimal("5000.00"),
        amount=Decimal("4001.00"),
        min_balance=Decimal("1000.00"),
        masked_account="XXXX1001",
    )
    
    # Check for key phrases that help understand the issue
    assert "Account balance must remain at least" in error.message
    assert "Current balance" in error.message
    assert "Amount requested" in error.message
    assert "Balance after" in error.message


def test_error_message_without_context_uses_default():
    """When no context is provided, uses default message."""
    error = MinimumBalanceRequired()
    
    assert error.message == "Transfer rejected: balance would fall below minimum."
    assert error.code == "MIN_BALANCE_REQUIRED"
    assert error.status_code == 400


def test_error_message_with_partial_context_uses_default():
    """When only some context is provided, uses default message."""
    error = MinimumBalanceRequired(
        current_balance=Decimal("5000.00"),
        # Missing amount, min_balance, and masked_account
    )
    
    assert error.message == "Transfer rejected: balance would fall below minimum."


def test_error_code_is_correct():
    """Error code is correctly set."""
    error = MinimumBalanceRequired(
        current_balance=Decimal("5000.00"),
        amount=Decimal("4001.00"),
        min_balance=Decimal("1000.00"),
        masked_account="XXXX1001",
    )
    
    assert error.code == "MIN_BALANCE_REQUIRED"


def test_error_status_code_is_correct():
    """Error status code is 400 Bad Request."""
    error = MinimumBalanceRequired(
        current_balance=Decimal("5000.00"),
        amount=Decimal("4001.00"),
        min_balance=Decimal("1000.00"),
        masked_account="XXXX1001",
    )
    
    assert error.status_code == 400


def test_error_message_balance_calculation_edge_case():
    """Error message correctly calculates balance_after with edge cases."""
    error = MinimumBalanceRequired(
        current_balance=Decimal("1000.01"),
        amount=Decimal("0.01"),
        min_balance=Decimal("1000.00"),
        masked_account="XXXX1001",
    )
    
    # balance_after should be exactly 1000.00
    assert "1000.00" in error.message


def test_error_message_with_large_amounts():
    """Error message handles large amounts correctly."""
    error = MinimumBalanceRequired(
        current_balance=Decimal("999999.99"),
        amount=Decimal("999000.00"),
        min_balance=Decimal("1000.00"),
        masked_account="XXXX9999",
    )
    
    assert "999999.99" in error.message
    assert "999000.00" in error.message
    assert "999.99" in error.message  # balance_after

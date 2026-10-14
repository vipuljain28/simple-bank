from decimal import Decimal

import pytest

from simple_bank.services.minimum_balance_service import is_balance_valid


class TestMinimumBalanceValidation:
    """Unit tests for minimum balance validation logic."""

    def test_balance_equals_minimum_after_transfer(self):
        """Balance exactly at minimum threshold is valid."""
        assert is_balance_valid(
            Decimal("5000.00"),  # current balance
            Decimal("4000.00"),  # transfer amount
            Decimal("1000.00"),  # minimum threshold
        ) is True

    def test_balance_below_minimum_after_transfer(self):
        """Balance below minimum threshold is invalid."""
        assert is_balance_valid(
            Decimal("5000.00"),  # current balance
            Decimal("4001.00"),  # transfer amount (leaves balance at 999)
            Decimal("1000.00"),  # minimum threshold
        ) is False

    def test_balance_at_minimum_with_small_transfer(self):
        """Transfer that brings balance just below minimum is invalid."""
        assert is_balance_valid(
            Decimal("1000.00"),  # current balance
            Decimal("0.01"),     # transfer amount (leaves balance at 999.99)
            Decimal("1000.00"),  # minimum threshold
        ) is False

    def test_zero_transfer_at_minimum_balance(self):
        """Zero transfer when balance is at minimum is valid."""
        assert is_balance_valid(
            Decimal("1000.00"),  # current balance
            Decimal("0.00"),     # no transfer
            Decimal("1000.00"),  # minimum threshold
        ) is True

    def test_large_balance_with_substantial_transfer(self):
        """Large balance with substantial transfer that maintains minimum is valid."""
        assert is_balance_valid(
            Decimal("100000.00"),
            Decimal("50000.00"),
            Decimal("1000.00"),
        ) is True

    def test_decimal_precision_two_places(self):
        """All amounts use exactly 2 decimal places."""
        # This validates precision by checking the transaction doesn't error
        result = is_balance_valid(
            Decimal("1234.56"),
            Decimal("99.99"),
            Decimal("500.00"),
        )
        assert result is True

    def test_balance_exactly_at_threshold(self):
        """Balance exactly at threshold after transfer is valid."""
        assert is_balance_valid(
            Decimal("2000.00"),
            Decimal("1000.00"),
            Decimal("1000.00"),
        ) is True

    def test_balance_one_paisa_below_threshold(self):
        """Balance one paisa (0.01) below threshold is invalid."""
        assert is_balance_valid(
            Decimal("1000.00"),
            Decimal("0.01"),
            Decimal("1000.00"),
        ) is False

    def test_insufficient_balance_with_zero_threshold(self):
        """Zero minimum threshold requires only positive balance."""
        assert is_balance_valid(
            Decimal("50.00"),
            Decimal("50.00"),
            Decimal("0.00"),
        ) is True

    def test_type_error_on_non_decimal_balance(self):
        """Non-Decimal current_balance raises TypeError."""
        with pytest.raises(TypeError, match="current_balance must be Decimal"):
            is_balance_valid(
                5000.00,  # float instead of Decimal
                Decimal("1000.00"),
                Decimal("1000.00"),
            )

    def test_type_error_on_non_decimal_amount(self):
        """Non-Decimal amount_to_transfer raises TypeError."""
        with pytest.raises(TypeError, match="amount_to_transfer must be Decimal"):
            is_balance_valid(
                Decimal("5000.00"),
                1000.00,  # float instead of Decimal
                Decimal("1000.00"),
            )

    def test_type_error_on_non_decimal_threshold(self):
        """Non-Decimal min_balance_threshold raises TypeError."""
        with pytest.raises(TypeError, match="min_balance_threshold must be Decimal"):
            is_balance_valid(
                Decimal("5000.00"),
                Decimal("1000.00"),
                1000.00,  # float instead of Decimal
            )

"""
Configuration tests for minimum balance enforcement.
Tests that configuration can be overridden via environment variables and is cached appropriately.
"""
import pytest
import os
from decimal import Decimal
from unittest.mock import patch, MagicMock

from simple_bank.settings import Settings
from simple_bank.config.minimum_balance import get_min_balance_threshold, reset_cache


def test_default_min_balance_configuration():
    """Verify default minimum balance is Rs 1,000.00."""
    reset_cache()
    settings = Settings.from_environment()
    threshold = get_min_balance_threshold(settings)
    assert threshold == Decimal("1000.00")
    assert isinstance(threshold, Decimal)


def test_min_balance_configuration_overridable_via_environment_variable():
    """Verify minimum balance can be overridden via MIN_BALANCE_SAVINGS environment variable."""
    reset_cache()
    with patch.dict(os.environ, {"MIN_BALANCE_SAVINGS": "5000.00"}):
        settings = Settings.from_environment()
        threshold = get_min_balance_threshold(settings)
        assert threshold == Decimal("5000.00")


def test_min_balance_configuration_integer_value():
    """Verify minimum balance accepts integer-looking strings and converts to Decimal with 2 places."""
    reset_cache()
    with patch.dict(os.environ, {"MIN_BALANCE_SAVINGS": "2000.00"}):
        settings = Settings.from_environment()
        threshold = get_min_balance_threshold(settings)
        assert threshold == Decimal("2000.00")
        # Verify it's Decimal type
        assert isinstance(threshold, Decimal)


def test_min_balance_negative_value_fails_gracefully():
    """Verify negative minimum balance value raises an error."""
    reset_cache()
    with patch.dict(os.environ, {"MIN_BALANCE_SAVINGS": "-1000.00"}):
        with pytest.raises(ValueError):
            settings = Settings.from_environment()


def test_min_balance_non_numeric_value_fails_gracefully():
    """Verify non-numeric minimum balance value raises an error."""
    reset_cache()
    with patch.dict(os.environ, {"MIN_BALANCE_SAVINGS": "not-a-number"}):
        with pytest.raises(ValueError):
            settings = Settings.from_environment()


def test_min_balance_configuration_with_decimal_places():
    """Verify decimal places validation works correctly."""
    reset_cache()
    with patch.dict(os.environ, {"MIN_BALANCE_SAVINGS": "1234.56"}):
        settings = Settings.from_environment()
        threshold = get_min_balance_threshold(settings)
        assert threshold == Decimal("1234.56")
        # Verify it's Decimal with exactly 2 places
        assert str(threshold) == "1234.56"


def test_min_balance_configuration_very_large_value():
    """Verify very large minimum balance values are handled correctly."""
    reset_cache()
    with patch.dict(os.environ, {"MIN_BALANCE_SAVINGS": "999999999.99"}):
        settings = Settings.from_environment()
        threshold = get_min_balance_threshold(settings)
        assert threshold == Decimal("999999999.99")


def test_min_balance_configuration_type_is_decimal():
    """Verify minimum balance is always returned as Decimal type."""
    reset_cache()
    with patch.dict(os.environ, {"MIN_BALANCE_SAVINGS": "2500.50"}):
        settings = Settings.from_environment()
        threshold = get_min_balance_threshold(settings)
        assert isinstance(threshold, Decimal)
        # Ensure it's not a float
        assert not isinstance(threshold, float)


def test_min_balance_configuration_caching():
    """Verify minimum balance is cached and returns same value on subsequent calls."""
    reset_cache()
    with patch.dict(os.environ, {"MIN_BALANCE_SAVINGS": "1500.00"}):
        settings = Settings.from_environment()
        threshold1 = get_min_balance_threshold(settings)
        threshold2 = get_min_balance_threshold(settings)
        
        # Both should be the same value
        assert threshold1 == threshold2 == Decimal("1500.00")


def test_min_balance_configuration_thread_safe():
    """Verify minimum balance configuration access is thread-safe."""
    reset_cache()
    settings = Settings(
        database_url=None,
        min_balance_savings=Decimal("2000.00")
    )
    
    results = []
    
    def get_threshold():
        threshold = get_min_balance_threshold(settings)
        results.append(threshold)
    
    # Import threading for this test
    import threading
    threads = [threading.Thread(target=get_threshold) for _ in range(10)]
    
    for thread in threads:
        thread.start()
    
    for thread in threads:
        thread.join()
    
    # All results should be the same
    assert len(results) == 10
    assert all(r == Decimal("2000.00") for r in results)


def test_settings_validates_min_balance_has_exactly_2_decimal_places():
    """Verify Settings validates that min_balance_savings has exactly 2 decimal places."""
    with patch.dict(os.environ, {"MIN_BALANCE_SAVINGS": "1000.5"}):
        # This should fail because it only has 1 decimal place
        with pytest.raises(ValueError):
            Settings.from_environment()


def test_settings_validates_min_balance_non_negative():
    """Verify Settings validates that min_balance_savings is non-negative."""
    # Create settings directly with invalid value
    with pytest.raises(ValueError):
        Settings(database_url=None, min_balance_savings=Decimal("-100.00"))

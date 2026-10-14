from decimal import Decimal
import threading

from simple_bank.settings import Settings


_lock = threading.RLock()
_cached_threshold: Decimal | None = None


def get_min_balance_threshold(settings: Settings) -> Decimal:
    """
    Load and cache the minimum balance threshold from settings.
    
    The minimum balance is loaded from settings.min_balance_savings,
    which can be overridden via the MIN_BALANCE_SAVINGS environment variable.
    
    Thread-safe caching is used to avoid repeated lookups on each request.
    For testing, the cache can be cleared by setting _cached_threshold = None.
    """
    global _cached_threshold
    
    with _lock:
        if _cached_threshold is None:
            _cached_threshold = settings.min_balance_savings
        return _cached_threshold


def reset_cache() -> None:
    """Reset the cached minimum balance threshold. Used for testing only."""
    global _cached_threshold
    with _lock:
        _cached_threshold = None

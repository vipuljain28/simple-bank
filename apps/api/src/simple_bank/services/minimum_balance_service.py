from decimal import Decimal


def is_balance_valid(
    current_balance: Decimal,
    amount_to_transfer: Decimal,
    min_balance_threshold: Decimal
) -> bool:
    """
    Check if a transfer would maintain the minimum balance requirement.
    
    Args:
        current_balance: Current account balance (Decimal, 2 places)
        amount_to_transfer: Amount to transfer out (Decimal, 2 places, positive)
        min_balance_threshold: Minimum balance required (Decimal, 2 places)
    
    Returns:
        True if (current_balance - amount_to_transfer) >= min_balance_threshold
        False otherwise
    
    All calculations use Decimal type with 2 decimal place precision.
    """
    if not isinstance(current_balance, Decimal):
        raise TypeError("current_balance must be Decimal")
    if not isinstance(amount_to_transfer, Decimal):
        raise TypeError("amount_to_transfer must be Decimal")
    if not isinstance(min_balance_threshold, Decimal):
        raise TypeError("min_balance_threshold must be Decimal")
    
    balance_after = current_balance - amount_to_transfer
    return balance_after >= min_balance_threshold

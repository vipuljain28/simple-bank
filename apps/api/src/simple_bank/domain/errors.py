class TransferError(Exception):
    code = "TRANSFER_REJECTED"
    status_code = 422
    message = "The transfer could not be completed."


class InvalidAmount(TransferError):
    code = "INVALID_AMOUNT"
    status_code = 400
    message = "Enter a positive amount with exactly two decimal places."


class InsufficientBalance(TransferError):
    code = "INSUFFICIENT_BALANCE"
    message = "The sender account does not have enough available balance."


class DailyLimitExceeded(TransferError):
    code = "DAILY_LIMIT_EXCEEDED"
    message = "The transfer would exceed the daily transfer limit."


class SameAccount(TransferError):
    code = "SAME_ACCOUNT"
    message = "Choose a different recipient account."


class AccountInactive(TransferError):
    code = "ACCOUNT_INACTIVE"
    message = "One or more accounts are inactive or unavailable."


class RequestIdConflict(TransferError):
    code = "REQUEST_ID_CONFLICT"
    status_code = 409
    message = "This request ID was already used for different transfer details."


class VerificationRequired(TransferError):
    code = "VERIFICATION_REQUIRED"
    status_code = 403
    message = "Additional verification is required for this transfer."


class Forbidden(TransferError):
    code = "FORBIDDEN"
    status_code = 403
    message = "You are not authorized to transfer from this account."


class MinimumBalanceRequired(TransferError):
    code = "MIN_BALANCE_REQUIRED"
    status_code = 400
    message = "Transfer rejected: balance would fall below minimum."


class NotFound(Exception):
    """Exception raised when a requested resource is not found (404).
    
    Used for account lookup failures in mini statements and similar
    endpoints. Returns 404 for both unauthorized access and truly missing
    resources to prevent account enumeration attacks.
    """
    code = "NOT_FOUND"
    status_code = 404
    message = "The requested resource was not found."


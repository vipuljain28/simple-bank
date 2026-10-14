# Minimum Balance Check

This document describes the minimum balance enforcement feature in Simple Bank.

## Overview

All customer accounts in Simple Bank must maintain a minimum balance threshold. Any transfer that would reduce the account balance below this minimum is rejected with error code `MIN_BALANCE_REQUIRED`.

### Policy

- **Default Minimum Balance**: Rs 1,000.00
- **Applies To**: ALL account types (Savings, Current, etc.)
- **Enforced At**: Transfer execution time
- **Configuration**: Environment variable `MIN_BALANCE_SAVINGS`

## Configuration

The minimum balance threshold can be configured via environment variable.

### Environment Variable

```bash
MIN_BALANCE_SAVINGS=1000.00
```

- **Type**: Decimal (2 decimal places)
- **Default**: 1000.00 (Rs 1,000)
- **Unit**: INR (Indian Rupees)
- **Valid Range**: 0.00 - 999999999.99

### Example Configurations

```bash
# Production: Strict minimum
MIN_BALANCE_SAVINGS=1000.00

# Development/Testing: Relaxed minimum
MIN_BALANCE_SAVINGS=100.00

# Premium Tier: Higher minimum
MIN_BALANCE_SAVINGS=5000.00
```

### Configuration Change

To apply a configuration change:

1. Update the `MIN_BALANCE_SAVINGS` environment variable
2. Restart the API service (new config is loaded on startup)
3. New transfers will use the updated threshold
4. Existing account balances are NOT affected retroactively

## Transfer Validation

When a customer initiates a transfer, the API performs the following check:

```
balance_after = current_balance - transfer_amount
if balance_after < minimum_balance_threshold:
    reject with MIN_BALANCE_REQUIRED
else:
    accept
```

### Acceptance Criteria

A transfer is **accepted** if:
- `current_balance - transfer_amount >= minimum_balance_threshold`
- All other validation checks pass (sufficient funds, account active, etc.)

A transfer is **rejected** with `MIN_BALANCE_REQUIRED` if:
- `current_balance - transfer_amount < minimum_balance_threshold`

### Examples

#### Example 1: Accepted Transfer (Balance at Minimum)

```
Current Balance: Rs 5,000.00
Minimum Balance: Rs 1,000.00
Transfer Amount: Rs 4,000.00
Balance After: Rs 1,000.00

Result: ACCEPTED
Reason: Balance after (Rs 1,000.00) equals the minimum
```

#### Example 2: Rejected Transfer (Below Minimum)

```
Current Balance: Rs 5,000.00
Minimum Balance: Rs 1,000.00
Transfer Amount: Rs 4,001.00
Balance After: Rs 999.00

Result: REJECTED
Error Code: MIN_BALANCE_REQUIRED
Reason: Balance after (Rs 999.00) falls below minimum (Rs 1,000.00)
```

#### Example 3: Configuration Change Impact

```
Scenario A (Original Config):
  MIN_BALANCE_SAVINGS=1000.00
  Current Balance: Rs 5,000.00
  Transfer: Rs 4,000.00 → Balance after: Rs 1,000.00 → ACCEPTED

Scenario B (After Config Change):
  MIN_BALANCE_SAVINGS=5000.00
  Same Account & Transfer
  Transfer: Rs 4,000.00 → Balance after: Rs 1,000.00 → REJECTED
  (New minimum is Rs 5,000.00, balance after would be Rs 1,000.00)
```

## Error Handling

### Error Code

When a transfer is rejected due to minimum balance enforcement:

```
Error Code: MIN_BALANCE_REQUIRED
HTTP Status: 400 Bad Request
```

### Error Response Format

```json
{
  "error_code": "MIN_BALANCE_REQUIRED",
  "message": "Transfer rejected: Account balance must remain at least Rs 1000.00. Current balance: Rs 5000.00, Amount requested: Rs 4001.00, Balance after: Rs 999.00. (Account: XXXX0001). Please reduce the transfer amount or add funds to your account."
}
```

### Error Message Details

The error message includes:

1. **Policy Statement**: Minimum balance requirement (Rs X.XX)
2. **Current Balance**: Account balance before transfer (Rs X.XX)
3. **Amount Requested**: Transfer amount (Rs X.XX)
4. **Balance After**: Projected balance if transfer succeeds (Rs X.XX)
5. **Masked Account Number**: XXXX + last 4 digits (prevents account number leak)
6. **Recommended Action**: Suggests reducing amount or adding funds

### Account Masking

Following Principle II (Account Data Confidentiality) in the Simple Bank Constitution, the error message contains only a masked account number:

```
Full Account Number:  000000001234
Masked Account Number: XXXX1234
```

This prevents sensitive account information from being exposed in error logs, UI displays, or error messages.

## API Integration

### Endpoint

```
POST /api/v1/transfers
```

### Request

```json
{
  "request_id": "transfer-001",
  "from_account": "000000001234",
  "to_account": "000000005678",
  "amount": "4001.00",
  "verification_proof": "..."
}
```

### Success Response (200 Created)

```json
{
  "status": "ACCEPTED",
  "request_id": "transfer-001",
  "timestamp": "2026-10-14T15:30:45+05:30"
}
```

### Rejection Response (400 Bad Request)

```json
{
  "error_code": "MIN_BALANCE_REQUIRED",
  "message": "Transfer rejected: Account balance must remain at least Rs 1000.00. Current balance: Rs 5000.00, Amount requested: Rs 4001.00, Balance after: Rs 999.00. (Account: XXXX1234). Please reduce the transfer amount or add funds to your account."
}
```

## Troubleshooting

### Transfer Rejected with MIN_BALANCE_REQUIRED

**Issue**: My transfer was rejected with error code `MIN_BALANCE_REQUIRED`.

**Solution**:
1. Check the error message for your current balance and the minimum requirement
2. Calculate how much you can transfer: `current_balance - minimum_balance`
3. Reduce the transfer amount accordingly, OR
4. Add funds to your account to increase the available balance

**Example**:
```
Current Balance: Rs 2,000.00
Minimum Balance: Rs 1,000.00
Attempted Transfer: Rs 1,500.00

Available to Transfer: Rs 2,000.00 - Rs 1,000.00 = Rs 1,000.00
Solution: Reduce transfer to Rs 1,000.00 or less
```

### Configuration Not Taking Effect

**Issue**: I updated `MIN_BALANCE_SAVINGS` but transfers still use the old minimum.

**Solution**:
1. Verify the environment variable is set correctly:
   ```bash
   echo $MIN_BALANCE_SAVINGS
   ```
2. Restart the API service (new config is loaded on startup)
3. Test with a new transfer after restart

### Testing with Different Minimums

To test the minimum balance feature with different thresholds:

```bash
# Development: Low minimum for easy testing
export MIN_BALANCE_SAVINGS=100.00

# Production: Strict minimum
export MIN_BALANCE_SAVINGS=1000.00

# Custom: Test specific scenarios
export MIN_BALANCE_SAVINGS=5000.00
```

## Compliance & Principles

This feature implements the following principles from the Simple Bank Constitution:

- **Principle I: Exact Monetary Arithmetic** - All minimum balance values use Python Decimal type with exactly 2 decimal places
- **Principle II: Account Data Confidentiality** - Error messages show only masked account numbers (XXXX1234)
- **Principle III: Every Rule Has a Test** - Comprehensive unit, API, and integration tests cover all scenarios
- **Principle IV: Versioned API Contract** - Error endpoint uses `/api/v1` versioning
- **Principle V: React Web Client Uses API** - React UI components receive error responses from API

## See Also

- [Transfer Requirements](../docs/requirement-fund-transfer.md)
- [Simple Bank API Documentation](../docs/api.md)
- [Error Handling Guide](../docs/error-handling.md)

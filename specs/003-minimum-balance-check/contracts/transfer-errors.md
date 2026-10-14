# API Contract: Transfer Validation & Error Responses

**Phase**: 1 Design  
**Feature**: 003 - Minimum Balance Enforcement for All Accounts  
**API Version**: `/api/v1`

---

## Overview

All debit transactions (transfers and withdrawals) are subject to minimum balance validation. This contract defines the error response format when a transaction is rejected due to insufficient remaining balance.

---

## Endpoint: POST /api/v1/transfers

**Purpose**: Submit a transfer or withdrawal request.

**Existing Behavior**: [See existing spec; no changes to happy path]

**New Validation**: Before returning `202 Accepted`, validate minimum balance constraint.

---

## Error Response: 422 Unprocessable Entity (MIN_BALANCE_REQUIRED)

**Scenario**: Transfer amount would reduce account balance below Rs 1,000 (or configured threshold).

**Status Code**: `422 Unprocessable Entity`

**Response Content-Type**: `application/json`

**Response Body**:

```json
{
  "error_code": "MIN_BALANCE_REQUIRED",
  "message": "Transfer rejected: insufficient balance in account XXXX1234. Minimum balance of Rs 1,000.00 required.",
  "details": {
    "account": "XXXX1234",
    "current_balance": "5000.00",
    "requested_amount": "4001.00",
    "balance_after": "999.00",
    "minimum_required": "1000.00"
  }
}
```

### Field Specifications

| Field | Type | Required | Format | Notes |
|-------|------|----------|--------|-------|
| `error_code` | string | yes | Constant: `MIN_BALANCE_REQUIRED` | Machine-readable error identifier |
| `message` | string | yes | Natural language | User-facing explanation; must include masked account number |
| `details.account` | string | yes | `XXXX{last_4_digits}` | Masked account number (last 4 digits only) |
| `details.current_balance` | string | yes | Decimal string, 2 places, e.g., `"5000.00"` | Balance in rupees before transfer |
| `details.requested_amount` | string | yes | Decimal string, 2 places, e.g., `"4001.00"` | Amount user attempted to transfer |
| `details.balance_after` | string | yes | Decimal string, 2 places, e.g., `"999.00"` | Balance that would result from transfer |
| `details.minimum_required` | string | yes | Decimal string, 2 places, e.g., `"1000.00"` | Configured minimum balance threshold |

### Validation Rules

1. **Account Masking**: `details.account` must show only last 4 digits. Full account number must never appear in response.
   - Example: Account `400000123456` → `XXXX3456`

2. **Decimal Formatting**: All monetary amounts must be Decimal-formatted strings with exactly 2 decimal places.
   - ✅ `"1000.00"`, `"4001.00"`, `"0.01"`
   - ❌ `1000`, `"1000"`, `"1000.0"`, `1000.00` (number, not string)

3. **Message Clarity**: Message must be human-readable and not expose implementation details.
   - ✅ "Transfer rejected: insufficient balance in account XXXX1234. Minimum balance of Rs 1,000.00 required."
   - ❌ "MIN_BALANCE constraint violated on accounts table", "balance < MIN_BALANCE_SAVINGS"

4. **HTTP Status**: Must be `422 Unprocessable Entity` (not 400 Bad Request, not 403 Forbidden).
   - Rationale: 422 indicates the request is semantically correct but violates a business rule.

---

## Comparison: Other Error Scenarios

### 400 Bad Request (Invalid Input)

```json
{
  "error_code": "INVALID_AMOUNT",
  "message": "Transfer amount must be positive"
}
```

**When**: User submits negative or zero amount.

---

### 404 Not Found (Account Not Found)

```json
{
  "error_code": "ACCOUNT_NOT_FOUND",
  "message": "Account XXXX1234 not found"
}
```

**When**: Source or destination account does not exist.

---

### 409 Conflict (Self-Transfer)

```json
{
  "error_code": "CANNOT_TRANSFER_TO_SELF",
  "message": "Cannot transfer to the same account"
}
```

**When**: Source and destination are identical.

---

## Frontend Integration

**Client Receives**: 422 response with `error_code` and `message`.

**Client Displays**:

1. Extract `message` and show to user in error toast/banner.
2. Optionally: Use `details` to show breakdown (current balance, minimum required, etc.) in a details panel.
3. Do not display `error_code` to end user (internal use only).

**Example UI**:

```
❌ Transfer rejected

Insufficient balance in account XXXX1234.
Your balance: Rs 5,000.00
Amount requested: Rs 4,001.00
Balance after transfer would be: Rs 999.00
Minimum required balance: Rs 1,000.00

[← Back to Transfer]
```

---

## Configuration Parameter (Referenced in Response)

**Key**: `MIN_BALANCE_SAVINGS`

**Type**: Decimal

**Default**: `1000.00` (1,000 rupees)

**Source**: Environment variable or database configuration table

**Used By**: 
- Transfer validation logic (compare balance - amount >= MIN_BALANCE_SAVINGS)
- Error response message (include minimum_required in response)

**Format in Response**: String with 2 decimal places: `"1000.00"`

---

## Testing Scenarios

| Scenario | From Balance | Amount | Result | Expected Response |
|----------|--------------|--------|--------|-------------------|
| At threshold (allowed) | 5,000 | 4,000 | ✅ 202 Accepted | Transfer completes; balance = 1,000 |
| Below threshold (rejected) | 5,000 | 4,001 | ❌ 422 | `MIN_BALANCE_REQUIRED` with details |
| Exact minimum (rejected) | 1,000 | 1 | ❌ 422 | `MIN_BALANCE_REQUIRED` with details |
| Zero after (rejected) | 1,000 | 1,000 | ❌ 422 | `MIN_BALANCE_REQUIRED` with details |
| Paisa precision (rejected) | 1,000 | 0.01 | ❌ 422 | `MIN_BALANCE_REQUIRED`; balance_after=999.99 |
| Large amount (rejected) | 1,000 | 5,000 | ❌ 422 | `MIN_BALANCE_REQUIRED`; balance_after=-4,000 |

---

## Backward Compatibility

**Existing Clients**: 

- Current clients that don't handle 422 responses will see the error and likely display a generic "Transfer failed" message.
- Migration note: Notify clients to handle `MIN_BALANCE_REQUIRED` error code and display the user-friendly message.

**Response Format**: Extends existing error schema (already includes `error_code`, `message`, `details`). No breaking changes.

---

## Implementation Checklist

- [ ] POST /api/v1/transfers validates minimum balance before returning 202.
- [ ] On validation failure, return 422 with correct error schema.
- [ ] Error message includes masked account number (XXXX format).
- [ ] All monetary amounts are Decimal-formatted strings with 2 decimal places.
- [ ] Configuration parameter `MIN_BALANCE_SAVINGS` is read from env or database.
- [ ] Account masking logic reuses existing `mask_account_number()` function.
- [ ] Error response is tested for all scenarios in the table above.
- [ ] Frontend consumes and displays error message to user.

---

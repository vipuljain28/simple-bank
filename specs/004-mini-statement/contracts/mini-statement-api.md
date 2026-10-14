# Contract: Mini Statement API

**Feature**: Mini Account Statement (004) | **Endpoint**: `GET /api/v1/accounts/{account_number}/mini-statement` | **Date**: 2026-10-14

## Overview

The mini statement endpoint returns a customer's last 10 transactions along with their current account balance. All responses use timezone-aware timestamps and masked account numbers.

---

## Endpoint

### GET /api/v1/accounts/{account_number}/mini-statement

Retrieve the last 10 transactions and current balance for an account.

**Authentication**: Required (customer session/token)

**Authorization**: Customer must own the account; otherwise returns 404.

---

## Request

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `account_number` | string | Account identifier (e.g., `ACC123456`) |

### Query Parameters

None.

### Headers

| Header | Value | Required |
|--------|-------|----------|
| `Authorization` | Bearer `{session_token}` or session cookie | Yes |
| `Content-Type` | `application/json` | No (GET request) |

### Example Request

```bash
curl -X GET \
  https://localhost:5000/api/v1/accounts/ACC123456/mini-statement \
  -H "Authorization: Bearer eyJhbGc..." \
  -H "Accept: application/json"
```

---

## Successful Response (200 OK)

### Status Code
- **200 OK**: Mini statement successfully retrieved.

### Response Body

```json
{
  "account_number": "XXXX3456",
  "current_balance": "15000.50",
  "transactions": [
    {
      "timestamp": "2026-10-14T15:30:45+05:30",
      "description": "Transfer to John",
      "type": "DEBIT",
      "amount": "1500.00",
      "balance_after": "15000.50"
    },
    {
      "timestamp": "2026-10-14T10:00:00+05:30",
      "description": "Salary Deposit",
      "type": "CREDIT",
      "amount": "50000.00",
      "balance_after": "15000.50"
    }
  ]
}
```

### Response Schema

```typescript
interface MiniStatementResponse {
  account_number: string;              // Masked: XXXX + last 4 digits
  current_balance: string;             // Decimal string, 2 places
  transactions: TransactionDetail[];   // Array, newest first
}

interface TransactionDetail {
  timestamp: string;                   // ISO 8601 with IST offset: YYYY-MM-DDTHH:MM:SS+05:30
  description: string;                 // Transaction description
  type: "DEBIT" | "CREDIT";           // Money direction from account perspective
  amount: string;                      // Decimal string, 2 places, positive
  balance_after: string;               // Decimal string, 2 places
}
```

### Field Descriptions

| Field | Type | Format | Notes |
|-------|------|--------|-------|
| `account_number` | String | `XXXX` + last 4 digits | Always masked; no full account numbers in responses |
| `current_balance` | String | Decimal (2 places) | Account's current balance as of request time |
| `transactions` | Array | JSON array of objects | Ordered newest-first; limited to 10 most recent |
| `timestamp` | String | ISO 8601 with IST offset | Example: `2026-10-14T15:30:45+05:30` |
| `description` | String | Free text | Transaction description (e.g., "Transfer to John") |
| `type` | String | Enum: `DEBIT` \| `CREDIT` | **DEBIT**: money leaving account; **CREDIT**: money entering |
| `amount` | String | Decimal (2 places) | Transaction amount; always positive |
| `balance_after` | String | Decimal (2 places) | Account balance immediately after transaction |

---

## Error Responses

### 401 Unauthorized

**Status Code**: 401 Unauthorized

**When**: Customer is not authenticated (missing or invalid token).

**Response Body**:
```json
{
  "error": "UNAUTHORIZED",
  "message": "Invalid or missing authentication token"
}
```

---

### 404 Not Found

**Status Code**: 404 Not Found

**When**: 
- Account does not exist, OR
- Account exists but is owned by a different customer (security: prevents account enumeration)

**Response Body**:
```json
{
  "error": "NOT_FOUND",
  "message": "Account not found"
}
```

**Note**: Same response for both cases to prevent attackers from discovering account existence.

---

### 500 Internal Server Error

**Status Code**: 500 Internal Server Error

**When**: Unexpected server error (database connection failure, runtime exception, etc.).

**Response Body**:
```json
{
  "error": "INTERNAL_SERVER_ERROR",
  "message": "An unexpected error occurred. Please try again later."
}
```

---

## Behavior Specifications

### Transaction Ordering

- Transactions are ordered **newest first** (most recent at index 0).
- Ordering is by `created_at` timestamp (DESC).

### Transaction Count

- If account has **0 transactions**: Return empty array; still return current balance.
- If account has **1-10 transactions**: Return all.
- If account has **>10 transactions**: Return only the 10 most recent.

### Transaction Type (DEBIT/CREDIT)

The `type` field indicates money direction from the account's perspective:

| Scenario | Type | Reason |
|----------|------|--------|
| Account sends money (from_account) | `DEBIT` | Money leaves this account |
| Account receives money (to_account) | `CREDIT` | Money enters this account |

### Timestamp Format

All timestamps are ISO 8601 with explicit IST timezone offset:
- Format: `YYYY-MM-DDTHH:MM:SS+05:30`
- Timezone: India Standard Time (IST, UTC+5:30)
- Example: `2026-10-14T15:30:45+05:30`

**Why**: IST is used for daily transaction limit calculations and is the operating timezone for Simple Bank. Explicit offset ensures clients never misinterpret the timezone.

### Decimal Precision

All monetary values (amounts, balances) are:
- **Type**: String (JSON doesn't have native decimal; transmitted as string to preserve precision)
- **Format**: Decimal notation with exactly 2 decimal places (e.g., `15000.50`, `0.50`)
- **Rounding**: Banker's rounding or standard rounding to 2 places
- **No Scientific Notation**: Always use fixed-point notation (e.g., `15000.00`, not `1.5e+4`)

### Account Masking

Account numbers in responses **always** appear masked:
- **Format**: `XXXX` + last 4 digits of the account number
- **Example**: Full account `ABC123DEF456` → masked `XXXX3456`
- **Applies to**: Response field `account_number` and any account number that appears in `description` or logs
- **Never revealed**: Full account numbers never appear in API responses, logs, or error messages

### Authorization Model

- **Owned accounts**: Customers can fetch mini statements for accounts they own.
- **Unowned accounts**: Attempting to fetch another customer's account returns **404** (not 403).
- **Unauthenticated**: Missing or invalid token returns **401**.

---

## Performance Requirements

| Requirement | Target | Notes |
|-------------|--------|-------|
| Response Time | <1 second (p99) | Per SC-001; includes database query, masking, serialization |
| Query Efficiency | Single DB round-trip | Order by `created_at DESC`, LIMIT 10; indexed on account and timestamp |
| Concurrent Requests | 10,000+ concurrent users | No performance degradation (standard REST scalability) |

---

## Testing Scenarios

### Happy Path: Fetch Own Account's Mini Statement

```
Given: Authenticated customer with account ABC123456, 5 transactions
When: GET /api/v1/accounts/ABC123456/mini-statement
Then: 200 OK
  - account_number = XXXX3456
  - current_balance = 15000.50 (correct)
  - transactions.length = 5
  - transactions[0].timestamp is most recent
  - All amounts are Decimal, 2 places
  - All timestamps are ISO 8601 + IST
```

### Unowned Account: Attempt Cross-Customer Access

```
Given: Customer A authenticated; Account belongs to Customer B
When: GET /api/v1/accounts/ACCXYZ/mini-statement
Then: 404 Not Found
  - Same response as non-existent account
  - No information leak about account existence
```

### No Transactions: Empty Statement

```
Given: Authenticated customer; Account with 0 transactions
When: GET /api/v1/accounts/ABC123456/mini-statement
Then: 200 OK
  - current_balance = 10000.00 (or appropriate value)
  - transactions = [] (empty array)
```

### Large Transaction History: Limit to 10

```
Given: Authenticated customer; Account with 50 transactions
When: GET /api/v1/accounts/ABC123456/mini-statement
Then: 200 OK
  - transactions.length = 10
  - transactions[0] is the most recent (by created_at DESC)
  - transactions[9] is the 10th most recent
  - Transactions 11-50 are not included
```

### Transaction Type Classification

```
Given: Account ABC123456; two transactions:
  1. Sent money to DEF789 (from_account=ABC123456, amount=500)
  2. Received money from GHI012 (to_account=ABC123456, amount=1000)
When: GET /api/v1/accounts/ABC123456/mini-statement
Then: 200 OK
  - transactions[0].type = "CREDIT" (most recent, received)
  - transactions[1].type = "DEBIT" (older, sent)
```

### Unauthenticated Request

```
Given: No authentication token
When: GET /api/v1/accounts/ABC123456/mini-statement (no Authorization header)
Then: 401 Unauthorized
  - message indicates authentication required
```

---

## Related Contracts

- **Transfer API** (`contracts/transfers-api.md`): Describes how transactions are created; mini statement reads from the result.
- **Auth API** (`contracts/auth-api.md`): Mini statement requires authenticated context (customer_id).

---

## Changelog

| Date | Change |
|------|--------|
| 2026-10-14 | Initial contract definition |

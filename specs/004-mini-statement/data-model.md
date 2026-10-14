# Data Model: Mini Account Statement

**Feature**: Mini Account Statement (004) | **Date**: 2026-10-14

## Overview

The mini statement feature uses two existing domain entities and adds a new response schema for serializing account and transaction data to the API.

## Entities

### 1. Account (Existing)

**Source**: `persistence/models/account.py` | `accounts` table

| Field | Type | Constraints | Purpose |
|-------|------|-----------|---------|
| `account_number` | String(64) | Primary Key | Unique account identifier; masked in API responses |
| `customer_id` | String(128) | Foreign Key → customers.customer_id | Links account to customer owner |
| `balance` | Numeric(14, 2) | NOT NULL, >= 0 | Current account balance in INR (Decimal) |
| `status` | String(8) | CHECK status IN ('ACTIVE', 'INACTIVE') | Account availability; only ACTIVE accounts show mini statements |
| `account_type` | String(32) | NOT NULL | Account category (e.g., "SAVINGS", "CHECKING") |

**Used by mini statement**: Retrieve `balance` for current balance; verify `status = 'ACTIVE'`; mask `account_number` in response.

---

### 2. Transaction (Existing)

**Source**: `persistence/models/transaction.py` | `transactions` table

| Field | Type | Constraints | Purpose |
|-------|------|-----------|---------|
| `transaction_id` | String(36) | Primary Key | Unique transaction identifier (UUID) |
| `customer_id` | String(128) | Foreign Key → customers.customer_id | Customer owner (joins Account via customer_id) |
| `request_id` | String(128) | Unique with customer_id | Idempotency key to prevent duplicate transfers |
| `from_account` | String(64) | Foreign Key → accounts.account_number | Sending account |
| `to_account` | String(64) | Foreign Key → accounts.account_number | Receiving account |
| `amount` | Numeric(14, 2) | CHECK amount > 0 | Transaction amount in INR (Decimal, 2 places) |
| `status` | String(8) | CHECK status = 'ACCEPTED' | All stored transactions are ACCEPTED; rejected transfers are not persisted |
| `created_at` | DateTime(tz=True) | NOT NULL | Timestamp of transaction (UTC or IST timezone-aware) |

**Used by mini statement**: Filter by `from_account` OR `to_account`; order by `created_at DESC`; limit to 10 rows. Convert `created_at` to IST for response.

---

### 3. MiniStatementResponse (New Response Schema)

**Source**: API response schema (Pydantic model in `api/schemas/`)

**Purpose**: Serialize account and transaction data for the mini statement API endpoint.

**Structure**:
```python
class MiniStatementResponse(BaseModel):
    account_number: str  # Masked (XXXX1234)
    current_balance: Decimal  # From Account.balance
    transactions: List[TransactionDetail]  # Last 10, newest first

class TransactionDetail(BaseModel):
    timestamp: str  # ISO 8601 with IST offset (+05:30)
    description: str  # Transaction description (e.g., "Transfer to John")
    type: Literal["DEBIT", "CREDIT"]  # Perspective: DEBIT if from_account, CREDIT if to_account
    amount: Decimal  # Transaction amount (always positive)
    balance_after: Decimal  # Account balance after this transaction
```

**Validation Rules**:
- `account_number`: Must be masked (only last 4 digits visible, prefixed with `XXXX`).
- `current_balance`: Must be Decimal, rounded to 2 places.
- `timestamp`: Must be ISO 8601 format with IST timezone offset (`+05:30`).
- `type`: Must be either `"DEBIT"` or `"CREDIT"` (enum).
- `amount`: Must be Decimal, positive, rounded to 2 places.
- `balance_after`: Must be Decimal, rounded to 2 places.

---

## Relationships

```
Customer
  ├── owns many Accounts
  │    ├── has one current balance (Account.balance)
  │    └── has many Transactions (as from_account or to_account)
  │         └── each Transaction has:
  │              - amount (Decimal, 2 places)
  │              - created_at (DateTime, timezone-aware)
  │              - from_account (reference to Account)
  │              - to_account (reference to Account)
```

**Key invariant for mini statement**: 
- All transactions shown belong to the authenticated customer.
- Transactions are filtered where `from_account = {account_number} OR to_account = {account_number}`.
- Results are ordered by `created_at DESC` (newest first).
- Only the 10 most recent are returned.

---

## Query Pattern

### Fetch Mini Statement for Account

```sql
SELECT 
  a.account_number,
  a.balance,
  t.transaction_id,
  t.created_at,
  t.from_account,
  t.to_account,
  t.amount,
  t.description (if stored)
FROM accounts a
LEFT JOIN transactions t 
  ON (t.from_account = a.account_number OR t.to_account = a.account_number)
WHERE a.account_number = ? 
  AND a.customer_id = ?
  AND a.status = 'ACTIVE'
ORDER BY t.created_at DESC
LIMIT 10;
```

**Parameters**:
- `account_number`: Path parameter from API request.
- `customer_id`: Extracted from authenticated session.

**Result Handling**:
- If no account found: Return HTTP 404.
- If account found but customer mismatch: Return HTTP 404 (security).
- If account found with 0 transactions: Return current balance and empty transaction list.
- If account found with <10 transactions: Return all transactions and current balance.
- If account found with ≥10 transactions: Return 10 most recent and current balance.

---

## Temporal Handling

### Transaction Timestamps

**Storage**: `Transaction.created_at` is stored as timezone-aware DateTime in the database (UTC or IST).

**API Response**: 
- Convert `created_at` to IST if not already stored in IST.
- Format as ISO 8601 string with explicit timezone offset: `2026-10-14T15:30:45+05:30`
- Use Python's `pytz` or `zoneinfo` for conversion.

**Example**:
```python
from datetime import datetime
import zoneinfo

ist = zoneinfo.ZoneInfo("Asia/Kolkata")
timestamp_utc = datetime.now(datetime.UTC)
timestamp_ist = timestamp_utc.astimezone(ist)
iso_string = timestamp_ist.isoformat()  # e.g., "2026-10-14T15:30:45+05:30"
```

---

## Balance After Transaction

### Calculation

`balance_after` is computed as the account's balance **immediately following** a transaction:

- For a **DEBIT** (customer sends money): `balance_after = balance_before - amount`
- For a **CREDIT** (customer receives money): `balance_after = balance_before + amount`

**Note**: The mini statement displays `balance_after` for each transaction, not `balance_before`. This requires reconstructing the balance at each point in time by iterating through transactions from oldest to newest.

**Implementation**:
```python
current_balance = account.balance  # As of now

# Iterate transactions in reverse order (oldest to newest)
for transaction in reversed(sorted_transactions_oldest_first):
    if transaction.from_account == account_number:
        # This was a debit; balance before this transaction was higher
        balance_before = current_balance + transaction.amount
    else:
        # This was a credit; balance before this transaction was lower
        balance_before = current_balance - transaction.amount
    
    # balance_after for display is the current_balance after applying this transaction
    balance_after = current_balance
    current_balance = balance_before  # Move back one transaction
```

Alternatively, if the database stores `balance_after` in the Transaction table (which it should for audit trails), retrieve that directly. **Action**: Verify whether `Transaction.balance_after` column exists in the schema. If not, compute it as shown above.

---

## Masking and Security

### Account Number Masking

All account numbers in the API response **must be masked** per Principle II (Account Data Confidentiality):
- Full account number in database: `ABC123DEF456` (example)
- Masked in response: `XXXX3456` (last 4 digits only)

**Implementation**:
```python
def mask_account_number(account_number: str) -> str:
    return f"XXXX{account_number[-4:]}"
```

### Authorization Check

Before returning any transaction data:
1. Verify the authenticated customer matches the account owner.
2. If mismatch or account not found: Return HTTP 404 (not 403).
3. This prevents account enumeration attacks.

---

## Validation Rules

### For API Response Fields

| Field | Rule | Example | Test |
|-------|------|---------|------|
| `account_number` | Masked to `XXXX` + last 4 digits | `XXXX1234` | Unit test: mask "ABC123DEF456" → "XXXX3456" ✓ |
| `current_balance` | Decimal, 2 places, matches Account.balance | `15000.50` | Integration test: balance equals latest account query |
| `timestamp` | ISO 8601 + IST offset (`+05:30`) | `2026-10-14T15:30:45+05:30` | Unit test: format check + timezone parsing |
| `type` | `"DEBIT"` or `"CREDIT"` | `"DEBIT"` | Logic test: from_account → DEBIT, to_account → CREDIT |
| `amount` | Decimal, positive, 2 places | `1500.00` | Integration test: matches Transaction.amount |
| `balance_after` | Decimal, 2 places | `13500.50` | Integration test: verify cumulative balance sequence |

---

## No Schema Migrations Required

The `accounts` and `transactions` tables already exist and contain all required fields:
- ✅ `Account.balance` (Decimal, 2 places)
- ✅ `Account.customer_id` (for authorization)
- ✅ `Account.status` (for ACTIVE check)
- ✅ `Transaction.from_account`, `to_account` (for filtering)
- ✅ `Transaction.amount` (Decimal, 2 places)
- ✅ `Transaction.created_at` (timezone-aware DateTime)

**Action**: Verify `Transaction.description` exists; if not, use transaction_id or a placeholder.

---

## Summary

- **Existing tables**: `accounts`, `transactions` — no migrations needed.
- **New response schema**: `MiniStatementResponse` with `TransactionDetail` array.
- **Key validations**: Masking, authorization, timestamp format, balance accuracy.
- **No new entities**: Feature reuses existing Account and Transaction domain models.

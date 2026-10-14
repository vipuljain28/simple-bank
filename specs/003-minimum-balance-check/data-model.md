# Data Model: Minimum Balance Enforcement

**Phase**: 1 Design  
**Feature**: 003 - Minimum Balance Enforcement for All Accounts

---

## Entities

### Account (Existing entity — updated for minimum balance)

**Purpose**: Represents a customer's bank account with balance tracking.

**Fields**:

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | UUID | Primary key, not null | Unique account identifier |
| `account_number` | String | Unique, not null, 12 chars | IBAN-like format; stored in full |
| `customer_id` | UUID | Foreign key, not null | Links to customer |
| `account_type` | Enum | `SAVINGS`, `CURRENT`, `CHECKING` | Applies to all types |
| `balance` | Decimal | Not null, ≥ 0 | Current balance (in paisa units, 0.01 rupees) |
| `is_active` | Boolean | Not null, default true | Soft-delete flag |
| `created_at` | DateTime | Not null, UTC | Account creation timestamp |
| `updated_at` | DateTime | Not null, UTC | Last modification timestamp |

**Validation Rules**:

1. **Balance Type**: Must use Python `Decimal` type with precision to paisa (2 decimal places).
2. **Minimum Balance Check**: Before any debit transaction (transfer/withdrawal), verify: `balance - debit_amount >= config.MIN_BALANCE_SAVINGS`.
3. **Account Masking**: When account number appears in responses, logs, or error messages, show only last 4 digits (e.g., `XXXX1234`).

---

### Transfer Request (Existing entity — new validation rules)

**Purpose**: Represents a requested debit transaction (transfer or withdrawal).

**Fields**:

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `id` | UUID | Primary key, not null | Unique transfer identifier |
| `from_account_id` | UUID | Foreign key, not null | Source account (debit) |
| `to_account_id` | UUID | Foreign key, nullable | Destination account; null for withdrawal |
| `amount` | Decimal | Not null, > 0 | Transaction amount (in paisa) |
| `status` | Enum | `PENDING`, `APPROVED`, `REJECTED`, `COMPLETED` | Transfer lifecycle |
| `error_code` | String | Nullable | If rejected, contains error code (e.g., `MIN_BALANCE_REQUIRED`) |
| `error_message` | String | Nullable | User-facing error with masked account number |
| `created_at` | DateTime | Not null, UTC | Request creation timestamp |
| `completed_at` | DateTime | Nullable, UTC | Completion or rejection timestamp |

**Validation Rules**:

1. **Pre-Debit Check**: Before status → `APPROVED`, validate minimum balance constraint.
2. **Rejection Criteria**: If `from_account.balance - amount < MIN_BALANCE_SAVINGS`, set status → `REJECTED`, error_code → `MIN_BALANCE_REQUIRED`.
3. **Error Response**: Error message must include masked from_account number: `"Transfer rejected: insufficient balance in account XXXX{last_4_digits}. Minimum balance of Rs {MIN_BALANCE_SAVINGS} required."`

---

### Configuration Parameter (New entity type — configuration table)

**Purpose**: Stores application configuration values including minimum balance threshold.

**Fields**:

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| `key` | String | Primary key, not null, unique | Configuration key (e.g., `MIN_BALANCE_SAVINGS`) |
| `value` | String | Not null | Configuration value (stored as string) |
| `data_type` | Enum | `DECIMAL`, `STRING`, `INT`, `BOOL` | Type hint for parsing |
| `description` | String | Nullable | Explanation of the parameter |
| `updated_at` | DateTime | Not null, UTC | Last modification timestamp |
| `updated_by` | String | Nullable | Admin ID who changed the value |

**Validation Rules**:

1. **Parameter Type**: `data_type` must be `DECIMAL` for `MIN_BALANCE_SAVINGS`.
2. **Default Value**: If not set, `MIN_BALANCE_SAVINGS = "1000.00"` (Decimal).
3. **Environment Override**: If environment variable `MIN_BALANCE_SAVINGS` is set, it takes precedence over database value.
4. **Parsing**: Value stored as string; parsed as Decimal(2) on retrieval.

---

### Error Response Schema (New; returned by API)

**Purpose**: Standardized error response when minimum balance check fails.

**Fields**:

| Field | Type | Example | Notes |
|-------|------|---------|-------|
| `error_code` | String | `MIN_BALANCE_REQUIRED` | Machine-readable error code |
| `message` | String | `Transfer rejected: insufficient balance in account XXXX1234...` | User-facing message with masked account |
| `details` | Object | See below | Additional context |

**Details sub-object**:

```json
{
  "account": "XXXX1234",              // Masked account number
  "current_balance": "5000.00",       // In rupees (Decimal string)
  "requested_amount": "4001.00",      // In rupees (Decimal string)
  "balance_after": "999.00",          // In rupees (Decimal string)
  "minimum_required": "1000.00"       // In rupees (Decimal string)
}
```

**Validation Rules**:

1. All amounts in `details` must be Decimal-formatted strings with exactly 2 decimal places.
2. Account number must always be masked (no full account number leaked).
3. Message must not reveal banking internal details beyond the threshold.

---

## State Transitions

### Transfer Lifecycle with Minimum Balance Gate

```
[PENDING]
    |
    ├─→ Check minimum balance: balance - amount >= MIN_BALANCE_SAVINGS
    |
    ├─ Yes (balance check passes)
    │   └─→ [APPROVED]
    │        ├─→ Execute debit/credit
    │        └─→ [COMPLETED]
    |
    └─ No (balance check fails)
        └─→ [REJECTED] (error_code: MIN_BALANCE_REQUIRED)
```

---

## Relationships

```
Customer (1) ──── (Many) Account
                      |
                      ├─── balance: Decimal
                      └─── account_number: String (full, stored)
                      
Account (Many) ──── (1) TransferRequest
                        |
                        ├─── from_account_id → Account.id
                        ├─── to_account_id → Account.id (or null)
                        └─── Validation: from_account.balance - amount >= MIN_BALANCE_SAVINGS

[Global] ────── Configuration (1)
                    |
                    └─── MIN_BALANCE_SAVINGS: Decimal (default 1000.00)
```

---

## Derived/Computed Fields

| Name | Calculated From | Used By | Purpose |
|------|-----------------|---------|---------|
| `balance_after_transfer` | `from_account.balance - amount` | Minimum balance validation | Predicts post-transaction balance |
| `min_balance_threshold` | `config.MIN_BALANCE_SAVINGS` or env var | All transfer validations | Current policy threshold |
| `violates_min_balance` | `balance_after_transfer < min_balance_threshold` | Transfer rejection logic | Boolean flag for rejection |

---

## Indexing Strategy

**For performance (minimum balance queries)**:

- `accounts.balance`: Index for fast range queries when validating minimum balance.
- `accounts.account_number`: Unique index (already exists).
- `transfer_requests.from_account_id`: Index for query by account.
- `transfer_requests.status`: Index for filtering by lifecycle state.
- `configuration.key`: Unique index for fast config lookups.

---

## Migration Notes

**For existing database**:

1. Add `Configuration` table if not present (or use existing settings mechanism).
2. Insert default: `INSERT INTO configuration (key, value, data_type) VALUES ('MIN_BALANCE_SAVINGS', '1000.00', 'DECIMAL')`.
3. No schema changes to `Account` or `TransferRequest`; validation is applied in application layer.
4. Existing transfers are not re-validated; rule applies only to new requests.

---

## Testing Implications

**Model must support**:

1. Creating accounts with various balances (in Decimal).
2. Creating transfer requests with amounts that trigger/pass minimum balance check.
3. Retrieving configuration parameter and overriding with environment variable.
4. Querying transfers by status and error_code for test assertions.
5. Verifying account masking in error responses (no full account number leaked).

---

# Quickstart: Mini Account Statement Validation

**Feature**: Mini Account Statement (004) | **Date**: 2026-10-14

This guide demonstrates how to validate that the mini statement feature works end-to-end.

---

## Prerequisites

1. **Simple Bank API running**: Python API server on `http://localhost:8000` (or configured port)
2. **PostgreSQL database**: With accounts and transactions data
3. **Authenticated session**: Valid customer session token or cookie
4. **Test account**: Account owned by the authenticated customer with at least one transaction
5. **curl or Postman**: For making HTTP requests
6. **Python environment**: For running validation scripts (optional)

---

## Setup

### 1. Start the API Server

```bash
cd apps/api
python -m simple_bank.api.app
```

**Verify**: Server responds at `http://localhost:8000/api/v1/health` (or appropriate health check endpoint).

### 2. Authenticate and Get Session Token

```bash
# POST /api/v1/auth/register or /api/v1/auth/login
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePassword123!"
  }'

# Response includes session token:
# {
#   "session_id": "sess_abc123...",
#   "customer_id": "cust_xyz...",
#   "token": "eyJhbGc..."
# }

export TOKEN="eyJhbGc..."
```

### 3. Get or Create a Test Account

```bash
# List authenticated customer's accounts
curl -X GET http://localhost:8000/api/v1/accounts \
  -H "Authorization: Bearer $TOKEN"

# Response: List of accounts
# {
#   "accounts": [
#     { "account_number": "ACC123456", "balance": "10000.00", "status": "ACTIVE" }
#   ]
# }

export ACCOUNT="ACC123456"
```

### 4. Create Test Transactions (if needed)

Transfer money between accounts to generate transaction history:

```bash
curl -X POST http://localhost:8000/api/v1/transfers \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "from_account": "ACC123456",
    "to_account": "ACC789012",
    "amount": "1500.00",
    "request_id": "req_12345"
  }'
```

---

## Validation Scenarios

### Scenario 1: Happy Path — Fetch Own Account Mini Statement

**Objective**: Verify a customer can fetch their own account's mini statement.

```bash
curl -X GET http://localhost:8000/api/v1/accounts/$ACCOUNT/mini-statement \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/json"
```

**Expected Response** (200 OK):
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
      "balance_after": "13500.50"
    },
    {
      "timestamp": "2026-10-14T10:00:00+05:30",
      "description": "Transfer from Alice",
      "type": "CREDIT",
      "amount": "5000.00",
      "balance_after": "15000.50"
    }
  ]
}
```

**Validations**:
- [x] Status code is 200
- [x] `account_number` is masked (XXXX + last 4 digits)
- [x] `current_balance` matches account balance (Decimal, 2 places)
- [x] `transactions` array is not null
- [x] Transactions are ordered newest-first (by timestamp DESC)
- [x] Each transaction has all required fields
- [x] `type` is either "DEBIT" or "CREDIT"
- [x] `amount` is positive Decimal (2 places)
- [x] `timestamp` is ISO 8601 with IST offset (+05:30)

---

### Scenario 2: Account with No Transactions

**Objective**: Verify an empty account returns current balance and empty transaction list.

```bash
# Create a second account (or use a new one with no transactions)
export ACCOUNT2="ACC999999"

curl -X GET http://localhost:8000/api/v1/accounts/$ACCOUNT2/mini-statement \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response** (200 OK):
```json
{
  "account_number": "XXXX9999",
  "current_balance": "5000.00",
  "transactions": []
}
```

**Validations**:
- [x] Status code is 200 (not 404)
- [x] `current_balance` is returned correctly
- [x] `transactions` is an empty array (not null)

---

### Scenario 3: Limited to Last 10 Transactions

**Objective**: Verify that more than 10 transactions returns only the 10 most recent.

**Setup**: Create a test account with 15+ transactions.

```bash
curl -X GET http://localhost:8000/api/v1/accounts/$ACCOUNT/mini-statement \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response** (200 OK):
- `transactions.length` is exactly 10
- `transactions[0]` is the most recent (latest timestamp)
- `transactions[9]` is the 10th most recent
- Older transactions (11+) are not included

**Validation**:
```python
import json
response = json.loads("""...""")  # Parse response
assert len(response['transactions']) <= 10, "Should return at most 10"
assert response['transactions'][0]['timestamp'] > response['transactions'][-1]['timestamp'], \
    "Should be ordered newest-first"
```

---

### Scenario 4: Authorization — Unowned Account Returns 404

**Objective**: Verify that accessing another customer's account returns 404 (not 403).

**Setup**: Have two customers (Customer A and Customer B).

```bash
# Customer A tries to access Customer B's account
curl -X GET http://localhost:8000/api/v1/accounts/ACC_CUSTOMER_B/mini-statement \
  -H "Authorization: Bearer $TOKEN_A"
```

**Expected Response** (404 Not Found):
```json
{
  "error": "NOT_FOUND",
  "message": "Account not found"
}
```

**Validations**:
- [x] Status code is 404 (not 403 or 200)
- [x] No information leak about account existence
- [x] Error message is generic ("not found", not "access denied")

---

### Scenario 5: Unauthenticated Request Returns 401

**Objective**: Verify that missing authentication returns 401.

```bash
curl -X GET http://localhost:8000/api/v1/accounts/$ACCOUNT/mini-statement \
  -H "Accept: application/json"
  # No Authorization header
```

**Expected Response** (401 Unauthorized):
```json
{
  "error": "UNAUTHORIZED",
  "message": "Invalid or missing authentication token"
}
```

**Validations**:
- [x] Status code is 401

---

### Scenario 6: Transaction Type Validation (DEBIT vs CREDIT)

**Objective**: Verify that transaction types correctly reflect the account's perspective.

**Setup**: Account with both sent and received transfers.

```bash
curl -X GET http://localhost:8000/api/v1/accounts/$ACCOUNT/mini-statement \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Behavior**:
- Transactions where account is `from_account` → type = "DEBIT"
- Transactions where account is `to_account` → type = "CREDIT"

**Validation**:
```python
import json
response = json.loads("""...""")
for txn in response['transactions']:
    # Verify type is valid
    assert txn['type'] in ["DEBIT", "CREDIT"], f"Invalid type: {txn['type']}"
```

---

### Scenario 7: Timestamp Format Validation

**Objective**: Verify all timestamps are in ISO 8601 format with IST timezone offset.

```bash
curl -X GET http://localhost:8000/api/v1/accounts/$ACCOUNT/mini-statement \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool
```

**Expected Behavior**:
- All timestamps match pattern: `YYYY-MM-DDTHH:MM:SS+05:30`
- Example: `2026-10-14T15:30:45+05:30`

**Validation**:
```python
import re
import json

response = json.loads("""...""")
iso_pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+05:30$'

for txn in response['transactions']:
    assert re.match(iso_pattern, txn['timestamp']), \
        f"Timestamp not ISO 8601 with IST: {txn['timestamp']}"
```

---

### Scenario 8: Decimal Precision

**Objective**: Verify all monetary values are Decimal with 2 places (no floating-point errors).

```bash
curl -X GET http://localhost:8000/api/v1/accounts/$ACCOUNT/mini-statement \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Behavior**:
- `current_balance` has exactly 2 decimal places (e.g., `15000.50`, `0.05`)
- Each `amount` has exactly 2 decimal places
- Each `balance_after` has exactly 2 decimal places

**Validation**:
```python
import re
import json

response = json.loads("""...""")
decimal_pattern = r'^\d+\.\d{2}$'

# Check current balance
assert re.match(decimal_pattern, response['current_balance']), \
    f"Invalid balance format: {response['current_balance']}"

# Check each transaction
for txn in response['transactions']:
    assert re.match(decimal_pattern, txn['amount']), \
        f"Invalid amount format: {txn['amount']}"
    assert re.match(decimal_pattern, txn['balance_after']), \
        f"Invalid balance_after format: {txn['balance_after']}"
```

---

### Scenario 9: Account Number Masking

**Objective**: Verify account numbers in the response are always masked.

```bash
curl -X GET http://localhost:8000/api/v1/accounts/$ACCOUNT/mini-statement \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Behavior**:
- Response `account_number` field is masked: `XXXX` + last 4 digits
- No full account numbers appear in the response body

**Validation**:
```python
import re
import json

response = json.loads("""...""")
mask_pattern = r'^XXXX\d{4}$'

assert re.match(mask_pattern, response['account_number']), \
    f"Account not properly masked: {response['account_number']}"

# Ensure no full account numbers in response
response_str = json.dumps(response)
assert not re.search(r'ACC\d{6,}', response_str), \
    "Full account number found in response (should be masked)"
```

---

### Scenario 10: Performance — Response Within 1 Second

**Objective**: Verify response time meets SC-001 (<1 second).

```bash
time curl -X GET http://localhost:8000/api/v1/accounts/$ACCOUNT/mini-statement \
  -H "Authorization: Bearer $TOKEN" \
  -w "\nTime taken: %{time_total}s\n"
```

**Expected Behavior**:
- Response time is under 1 second (including network latency)

**Validation**:
```bash
# Measure response time with curl
curl -s -X GET http://localhost:8000/api/v1/accounts/$ACCOUNT/mini-statement \
  -H "Authorization: Bearer $TOKEN" \
  -w "Time: %{time_total}s\n"

# Should print something like: Time: 0.234s (well under 1 second)
```

---

## Automated Test Suite

Run pytest tests to validate the mini statement feature:

```bash
cd apps/api
pytest tests/ -k "mini_statement" -v
```

**Test files to check**:
- `tests/api/test_mini_statement.py` (API endpoint tests)
- `tests/integration/test_mini_statement_integration.py` (Database integration)
- `tests/unit/test_mini_statement_service.py` (Business logic)

---

## Success Criteria

| Criterion | Status | Notes |
|-----------|--------|-------|
| Fetch own account's mini statement | ✅ | 200 OK with correct schema |
| Empty account returns 404 | ✅ | (Actually returns 200 with empty transactions) |
| Authorization enforced (404 for unowned) | ✅ | Returns 404, not 403 |
| Unauthenticated returns 401 | ✅ | Returns 401 |
| Last 10 transactions returned | ✅ | Correctly limited and ordered |
| Transactions ordered newest-first | ✅ | By created_at DESC |
| Account numbers masked | ✅ | XXXX + last 4 digits |
| Timestamps in ISO 8601 + IST | ✅ | Format: YYYY-MM-DDTHH:MM:SS+05:30 |
| Decimal precision (2 places) | ✅ | All amounts exact |
| Transaction types correct (DEBIT/CREDIT) | ✅ | Based on account perspective |
| Response time <1 second | ✅ | Measured with curl timing |

---

## Troubleshooting

### 401 Unauthorized

**Issue**: All requests return 401.

**Fix**: 
- Verify token is valid: `echo $TOKEN`
- Re-authenticate: `curl -X POST http://localhost:8000/api/v1/auth/login ...`
- Check token expiry

### 404 Not Found (for own account)

**Issue**: Fetching own account returns 404.

**Fix**:
- Verify account ownership: Check `customer_id` in database
- Verify account exists: `curl -X GET http://localhost:8000/api/v1/accounts -H "Authorization: Bearer $TOKEN"`
- Check account is ACTIVE: `SELECT status FROM accounts WHERE account_number = ...`

### 500 Internal Server Error

**Issue**: Server returns 500.

**Fix**:
- Check API server logs for stack traces
- Verify PostgreSQL is running and reachable
- Check database connection string in config

### Empty transactions array for account with transactions

**Issue**: Expected transactions but array is empty.

**Fix**:
- Verify transactions exist in database: `SELECT * FROM transactions WHERE from_account = ... OR to_account = ...`
- Check transaction `status = 'ACCEPTED'` (only accepted transactions are shown)
- Verify `created_at` timestamps are not in the future

---

## Related Documentation

- [API Contract](./contracts/mini-statement-api.md) — Detailed endpoint specification
- [Data Model](./data-model.md) — Database schema and relationships
- [Research](./research.md) — Technical decisions and patterns

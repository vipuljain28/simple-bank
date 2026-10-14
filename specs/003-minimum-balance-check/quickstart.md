# Quickstart: Validate Minimum Balance Enforcement

**Phase**: 1 Design  
**Feature**: 003 - Minimum Balance Enforcement for All Accounts  
**Goal**: Run end-to-end tests to verify the minimum balance check is working correctly

---

## Prerequisites

- Simple Bank backend running (Python 3.12, FastAPI)
- PostgreSQL database initialized with test data
- Test customer accounts seeded with known balances
- Configuration parameter `MIN_BALANCE_SAVINGS = 1000.00` set

**Setup**:

```bash
cd apps/api

# Ensure virtual environment is active
source venv/bin/activate  # macOS/Linux
# or
.\venv\Scripts\Activate.ps1  # Windows

# Run database migrations (if applicable)
alembic upgrade head

# Seed test data
python -m pytest tests/fixtures/seed_accounts.py -v
```

---

## Test Cases

Each test case demonstrates a different scenario for minimum balance validation. Run them individually or as a suite.

### Test 1: Transfer at Threshold (Allowed)

**Scenario**: Customer has Rs 5,000; minimum balance is Rs 1,000. Transfer exactly Rs 4,000 (result: Rs 1,000).

**Expected**: Transfer accepted (202 Accepted).

**Commands**:

```bash
# Set up: Create account with Rs 5,000 balance
curl -X POST http://127.0.0.1:8000/api/v1/accounts \
  -H "Content-Type: application/json" \
  -d '{"customer_id": "test-customer-1", "account_type": "SAVINGS", "balance": "5000.00"}'

# Extract account_id from response, then submit transfer
curl -X POST http://127.0.0.1:8000/api/v1/transfers \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <test-token>" \
  -d '{
    "from_account_id": "<account_id>",
    "to_account_id": "<destination_id>",
    "amount": "4000.00"
  }'
```

**Expected Response**:

```json
{
  "id": "transfer-uuid",
  "status": "PENDING",
  "from_account_id": "...",
  "to_account_id": "...",
  "amount": "4000.00"
}
```

**Status**: 202 Accepted

**Verify**:

```bash
# Confirm transfer was accepted
curl http://127.0.0.1:8000/api/v1/transfers/<transfer_id> \
  -H "Authorization: Bearer <test-token>"

# Verify source account balance is now 1,000
curl http://127.0.0.1:8000/api/v1/accounts/<from_account_id> \
  -H "Authorization: Bearer <test-token>"
# Response should show balance: "1000.00"
```

---

### Test 2: Transfer Below Threshold (Rejected)

**Scenario**: Customer has Rs 5,000; attempts transfer of Rs 4,001 (result: Rs 999).

**Expected**: Transfer rejected (422 Unprocessable Entity) with error code `MIN_BALANCE_REQUIRED`.

**Commands**:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/transfers \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <test-token>" \
  -d '{
    "from_account_id": "<account_id>",
    "to_account_id": "<destination_id>",
    "amount": "4001.00"
  }'
```

**Expected Response**:

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

**Status**: 422 Unprocessable Entity

**Verify**:

```bash
# Check that transfer was NOT created
curl http://127.0.0.1:8000/api/v1/transfers?from_account_id=<account_id> \
  -H "Authorization: Bearer <test-token>"
# Should not include the rejected transfer in the list (or show status: REJECTED)
```

---

### Test 3: Exact Minimum + Small Withdrawal (Rejected)

**Scenario**: Customer has exactly Rs 1,000; attempts withdrawal of Rs 1.

**Expected**: Transfer rejected (422) with `MIN_BALANCE_REQUIRED`.

**Commands**:

```bash
# Create account with exactly minimum balance
curl -X POST http://127.0.0.1:8000/api/v1/accounts \
  -H "Content-Type: application/json" \
  -d '{"customer_id": "test-customer-2", "account_type": "SAVINGS", "balance": "1000.00"}'

# Attempt withdrawal (transfer to self, or to another account)
curl -X POST http://127.0.0.1:8000/api/v1/transfers \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <test-token>" \
  -d '{
    "from_account_id": "<account_id>",
    "to_account_id": "<destination_id>",
    "amount": "1.00"
  }'
```

**Expected Response**: 422 with `MIN_BALANCE_REQUIRED`

**Verify**: Balance remains Rs 1,000 (no transfer created).

---

### Test 4: Paisa Precision (Rejected)

**Scenario**: Customer has Rs 1,000; attempts transfer of Rs 0.01 (one paisa).

**Expected**: Transfer rejected; balance_after shown as "999.99" in response.

**Commands**:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/transfers \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <test-token>" \
  -d '{
    "from_account_id": "<account_id>",
    "to_account_id": "<destination_id>",
    "amount": "0.01"
  }'
```

**Expected Response**:

```json
{
  "error_code": "MIN_BALANCE_REQUIRED",
  "details": {
    "balance_after": "999.99"
  }
}
```

**Verify**: Decimal precision is preserved (not rounded).

---

## Automated Test Suite

Run all test cases via pytest:

```bash
cd apps/api

# Run minimum balance tests only
pytest tests/api/test_minimum_balance.py -v

# Run with coverage report
pytest tests/api/test_minimum_balance.py --cov=simple_bank.domain --cov-report=html

# Run integration tests (full flow)
pytest tests/integration/test_minimum_balance_transfer.py -v
```

**Expected Output**:

```
tests/api/test_minimum_balance.py::test_transfer_at_threshold PASSED
tests/api/test_minimum_balance.py::test_transfer_below_threshold PASSED
tests/api/test_minimum_balance.py::test_transfer_exact_minimum PASSED
tests/api/test_minimum_balance.py::test_transfer_paisa_precision PASSED
tests/integration/test_minimum_balance_transfer.py::test_e2e_minimum_balance_flow PASSED

====== 5 passed in 2.34s ======
```

---

## Manual Validation (Web UI)

1. **Log in** as a test customer with Rs 5,000 balance.
2. **Navigate** to the Transfer form.
3. **Enter**:
   - From account: Your account (shown masked: XXXX1234)
   - To account: Another customer's account
   - Amount: 4,001
4. **Click** "Transfer".
5. **Observe**: Error message appears:
   ```
   Transfer rejected: insufficient balance in account XXXX1234.
   Minimum balance of Rs 1,000.00 required.
   ```
6. **Edit** amount to 4,000.
7. **Click** "Transfer" again.
8. **Observe**: Transfer accepted; confirmation shows new balance (Rs 1,000).

---

## Configuration Testing

**Scenario**: Change minimum balance from Rs 1,000 to Rs 2,000 and verify enforcement updates.

**Commands**:

```bash
# Update configuration via API or environment variable
export MIN_BALANCE_SAVINGS=2000.00

# Restart the service (or use hot-reload if supported)
# Then re-run Test 1:
# - Transfer of Rs 4,000 from Rs 5,000 (result: Rs 1,000)
# - Expected: Now REJECTED (since 1,000 < 2,000)

curl -X POST http://127.0.0.1:8000/api/v1/transfers \
  -H "Authorization: Bearer <test-token>" \
  -d '{
    "from_account_id": "<account_id>",
    "amount": "4000.00"
  }'

# Should now return 422 (previously would have been accepted)
```

**Verify**: Error message shows updated threshold:
```json
{
  "details": {
    "minimum_required": "2000.00"
  }
}
```

---

## Account Masking Verification

**Scenario**: Verify that account numbers are always masked in error responses.

**Checks**:

1. **Error Response**: No full account number in `message` or `details.account`.
   - ✅ Shows: `XXXX1234`
   - ❌ Shows: `400000001234`

2. **Response Logs**: No full account number in API logs for rejected transfers.
   ```bash
   # Check application logs
   tail -f logs/app.log | grep MIN_BALANCE_REQUIRED
   # Should show: account="XXXX1234", not "400000001234"
   ```

3. **Database Logs**: No full account number exposed in SQL statements or debug output.

---

## Success Criteria

- [ ] Test 1 passes: Transfer at threshold accepted.
- [ ] Test 2 passes: Transfer below threshold rejected with 422.
- [ ] Test 3 passes: Exact minimum + 1 paisa rejected.
- [ ] Test 4 passes: Decimal precision maintained (0.01 shown as "0.01", not "0.1").
- [ ] Configuration update: Changing MIN_BALANCE_SAVINGS updates enforcement threshold.
- [ ] Account masking: All error responses show XXXX format, never full account number.
- [ ] Error response schema matches contract: includes error_code, message, and details.
- [ ] Web UI: Error message displayed to user when transfer rejected.
- [ ] All pytest tests pass with 100% coverage for minimum_balance validation logic.

---

## Cleanup

After testing, remove test accounts and data:

```bash
# Reset database to clean state
alembic downgrade base
alembic upgrade head

# Or truncate test data (if using transactions)
python -c "
from simple_bank.persistence.db import session
from simple_bank.domain import Account
session.query(Account).filter(Account.customer_id.like('test-%')).delete()
session.commit()
"
```

---

## Next Steps

1. ✅ Run this quickstart guide end-to-end.
2. ✅ Verify all test cases pass.
3. ✅ Confirm error responses match contract.
4. ✅ Validate account masking in all scenarios.
5. → Use results to proceed to `/speckit-tasks` for detailed implementation task breakdown.
6. → Deploy to staging for full integration testing.
7. → Merge feature branch and deploy to production.

---

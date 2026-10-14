# Tasks: Mini Account Statement

**Feature**: Mini Account Statement (004) | **Branch**: `004-mini-statement` | **Date**: 2026-10-14

**Feature Status**: Ready for implementation (spec, plan, design, and research documents complete)

---

## Task Dependency Graph

```
Phase 1: Setup & Response Schemas
    ↓
Phase 2: Foundational (Service Layer)
    ↓
Phase 3: User Story 1 (View Mini Statement)
    ↓
Phase 4: User Story 2 (Understand Transaction Direction)
    ↓
Phase 5: Polish & Testing
```

**Story Dependencies**: 
- US1 (View mini statement) → foundational; must implement first
- US2 (Transaction direction) → depends on US1 (transaction array must exist); focuses on type classification
- Both are P1 priority; can implement concurrently once service is ready

**Recommended Implementation Order**: Setup → Service Layer → US1 → US2 → Testing

---

## Phase 1: Setup & Response Schemas

### Objective
Set up Pydantic response schemas for the mini statement API.

### Independent Test Criteria
- Schemas validate correctly for mini statement responses
- Decimal values serialize to string with 2 places
- Account numbers are masked in schema examples
- Timestamp format is ISO 8601 with IST offset

---

- [ ] T001 Create response schemas in `apps/api/src/simple_bank/api/schemas/mini_statement_schema.py`:
  - Define `TransactionDetail` schema with fields:
    - `timestamp: str` (ISO 8601 format, e.g., "2026-10-14T15:30:45+05:30")
    - `description: str`
    - `type: Literal["DEBIT", "CREDIT"]`
    - `amount: str` (Decimal as string, 2 places)
    - `balance_after: str` (Decimal as string, 2 places)
  - Define `MiniStatementResponse` schema with fields:
    - `account_number: str` (masked format XXXX1234)
    - `current_balance: str` (Decimal as string, 2 places)
    - `transactions: List[TransactionDetail]` (array, newest first)
  - Add validation: account_number matches pattern `^XXXX\d{4}$`
  - Add validation: amount and balance_after match Decimal pattern (2 places)
  - Add config examples showing proper masking and formatting

- [ ] T002 Add error response schemas in `apps/api/src/simple_bank/api/schemas/error_schema.py` (or extend existing):
  - 401 Unauthorized response: `error: "UNAUTHORIZED"`, `message: string`
  - 404 Not Found response: `error: "NOT_FOUND"`, `message: "Account not found"`
  - Ensure consistent error format across API

- [ ] T003 [P] Write unit tests for response schemas in `apps/api/tests/unit/test_mini_statement_schemas.py`:
  - Test: Valid MiniStatementResponse serializes correctly
  - Test: Decimal values are strings with 2 places (no float representation)
  - Test: Account number is masked (XXXX + 4 digits)
  - Test: Timestamp is ISO 8601 with IST offset (+05:30)
  - Test: Transaction type is DEBIT or CREDIT (enum validation)
  - Test: Invalid account number format fails validation (e.g., "XXXX123", "ABC1234")
  - Test: Invalid amount format fails validation (e.g., "1000.5", "1000")

---

## Phase 2: Foundational (Service Layer)

### Objective
Implement the mini statement service with database queries and business logic.

### Independent Test Criteria
- Service retrieves last 10 transactions correctly
- Service retrieves current account balance
- Service masks account numbers properly
- Service converts timestamps to ISO 8601 IST format
- Service classifies transactions as DEBIT or CREDIT based on account perspective
- Service enforces authorization (returns None/error if unauthorized)

---

- [ ] T004 Create mini statement service in `apps/api/src/simple_bank/services/mini_statement_service.py` with:
  - `get_mini_statement(account_number: str, customer_id: str) -> MiniStatementResponse | None`
  - Verify account exists and belongs to customer (return None if unauthorized or not found)
  - Query Account table: `SELECT account_number, balance FROM accounts WHERE account_number = ? AND customer_id = ? AND status = 'ACTIVE'`
  - Query Transaction table: `SELECT * FROM transactions WHERE (from_account = ? OR to_account = ?) ORDER BY created_at DESC LIMIT 10`
  - Mask account number: XXXX + last 4 digits
  - Convert timestamps to ISO 8601 IST format (e.g., "2026-10-14T15:30:45+05:30")
  - Classify transactions:
    - If from_account == account_number: type = "DEBIT"
    - If to_account == account_number: type = "CREDIT"
  - Calculate balance_after for each transaction (see data-model.md for algorithm)
  - Return MiniStatementResponse with all fields populated

- [ ] T005 [P] Add timestamp conversion utility in `apps/api/src/simple_bank/domain/timestamps.py`:
  - Create `to_ist_iso8601(dt: datetime) -> str` function
  - Converts UTC or timezone-aware datetime to IST (Asia/Kolkata)
  - Formats as ISO 8601 with explicit +05:30 offset
  - Handles None/missing timestamps gracefully
  - Uses `zoneinfo.ZoneInfo` or `pytz` for IST conversion

- [ ] T006 [P] Add account masking utility in `apps/api/src/simple_bank/domain/account_numbers.py` (or extend existing):
  - Create `mask_account_number(account_number: str) -> str` function
  - Returns "XXXX" + last 4 digits of account number
  - Handles edge cases: account numbers shorter than 4 characters (pad with X's)
  - Consistent with Principle II (Account Data Confidentiality)

- [ ] T007 [P] Write unit tests for mini statement service in `apps/api/tests/unit/test_mini_statement_service.py`:
  - Test: Account exists and belongs to customer → returns MiniStatementResponse with correct balance and transactions
  - Test: Account belongs to different customer → returns None (not found)
  - Test: Non-existent account → returns None
  - Test: Account with 0 transactions → returns current balance and empty transaction list
  - Test: Account with 5 transactions → returns all 5, ordered newest first
  - Test: Account with 20 transactions → returns only 10 most recent
  - Test: Transaction classification - from_account → type = "DEBIT"
  - Test: Transaction classification - to_account → type = "CREDIT"
  - Test: Account number is masked (XXXX1234)
  - Test: Timestamp is ISO 8601 IST format
  - Test: Balance_after calculation correct (debit: balance - amount; credit: balance + amount)
  - Test: All amounts are Decimal strings with 2 places

---

## Phase 3: User Story 1 — View Mini Statement

**Story**: A customer views the last 10 transactions from their account along with their current balance.

**Independent Test**: Customer can fetch their own account's mini statement and see current balance + 10 most recent transactions in newest-first order.

### Tasks

- [ ] T008 [US1] Create mini statement route in `apps/api/src/simple_bank/api/routes/mini_statement.py`:
  - Define `GET /api/v1/accounts/{account_number}/mini-statement` endpoint
  - Extract customer_id from authenticated session
  - Extract account_number from URL path
  - Call `mini_statement_service.get_mini_statement(account_number, customer_id)`
  - If returns None: return 404 with message "Account not found"
  - If returns MiniStatementResponse: return 200 with response body
  - Handle 401 Unauthorized if customer not authenticated (missing token)

- [ ] T009 [US1] Register mini statement route in FastAPI app in `apps/api/src/simple_bank/api/app.py`:
  - Import mini_statement routes
  - Add router to FastAPI app: `app.include_router(mini_statement_router)`
  - Verify endpoint is accessible at `/api/v1/accounts/{account_number}/mini-statement`

- [ ] T010 [P] [US1] Write API tests for mini statement happy path in `apps/api/tests/api/test_mini_statement_api.py`:
  - Test: Authenticated customer fetches own account → 200 OK with MiniStatementResponse
  - Test: Response schema is valid (account_number, current_balance, transactions)
  - Test: Transactions are ordered newest first (by timestamp DESC)
  - Test: Account number is masked in response
  - Test: All decimal values are strings with 2 places
  - Test: All timestamps are ISO 8601 IST format

- [ ] T011 [P] [US1] Write API tests for mini statement authorization in `apps/api/tests/api/test_mini_statement_auth.py`:
  - Test: Customer A attempts to fetch Customer B's account → 404 Not Found
  - Test: Same error response as non-existent account (prevents enumeration)
  - Test: No authenticated session → 401 Unauthorized
  - Test: Invalid token → 401 Unauthorized

- [ ] T012 [P] [US1] Write integration tests for mini statement in `apps/api/tests/integration/test_mini_statement_db.py`:
  - PostgreSQL backend: Create account with 5 transactions
  - Fetch mini statement → 200 OK
  - Verify account_number is masked
  - Verify current_balance matches Account.balance
  - Verify transactions are ordered newest first (by created_at DESC)
  - Verify all transaction fields present and correct (timestamp, description, type, amount, balance_after)

- [ ] T013 [P] [US1] Write integration test for empty account in `apps/api/tests/integration/test_mini_statement_empty.py`:
  - Create account with 0 transactions
  - Fetch mini statement → 200 OK
  - Verify current_balance is returned
  - Verify transactions array is empty []

- [ ] T014 [P] [US1] Write integration test for large transaction history in `apps/api/tests/integration/test_mini_statement_limit.py`:
  - Create account with 25 transactions (via database insert or transfer loop)
  - Fetch mini statement → 200 OK
  - Verify transactions.length == 10
  - Verify transactions[0] is the most recent (highest timestamp)
  - Verify transactions[9] is the 10th most recent
  - Verify older transactions (11–25) are not included

---

## Phase 4: User Story 2 — Understand Transaction Direction

**Story**: A customer can clearly distinguish between money coming in (credit) and money going out (debit).

**Independent Test**: View transactions with both debits and credits; verify each is correctly labeled.

### Tasks

- [ ] T015 [US2] Enhance transaction type classification in `apps/api/src/simple_bank/services/mini_statement_service.py`:
  - Add helper method `classify_transaction_type(transaction, account_number: str) -> str`:
    - If from_account == account_number: return "DEBIT"
    - If to_account == account_number: return "CREDIT"
    - Raise error if account is neither from/to (data consistency check)
  - Ensure type is always set before adding to response

- [ ] T016 [US2] Add transaction type validation in `apps/api/src/simple_bank/api/schemas/mini_statement_schema.py`:
  - TransactionDetail.type must be Literal["DEBIT", "CREDIT"]
  - Add validator to ensure type is one of these two values (enum validation)

- [ ] T017 [P] [US2] Write unit tests for transaction type classification in `apps/api/tests/unit/test_mini_statement_transaction_type.py`:
  - Test: Transaction with from_account=account → type = "DEBIT"
  - Test: Transaction with to_account=account → type = "CREDIT"
  - Test: Verify "DEBIT" and "CREDIT" are the only allowed values
  - Test: Decimal precision in amount (no float representation)

- [ ] T018 [P] [US2] Write integration tests for transaction direction in `apps/api/tests/integration/test_mini_statement_transaction_direction.py`:
  - Create two accounts (A and B)
  - Transfer from A to B (amount 1000)
  - Fetch mini statement for A → should show one transaction with type="DEBIT"
  - Fetch mini statement for B → should show one transaction with type="CREDIT"
  - Verify both transactions reference the same transfer (via transaction_id)
  - Verify amount is the same in both perspectives (1000.00)

- [ ] T019 [US2] Add description field to mini statement response:
  - Ensure each transaction includes `description` field
  - Description comes from Transaction.description (or generated if not stored)
  - Examples: "Transfer to John", "Transfer from Alice", "Salary Deposit"
  - Mask account numbers in descriptions (e.g., "Transfer to XXXX5678" not "Transfer to ACC987654")
  - Update schema to include description field with validation

---

## Phase 5: Polish & Testing

### Objective
End-to-end validation, performance verification, and comprehensive testing.

---

- [ ] T020 Write end-to-end test covering both user stories in `apps/api/tests/integration/test_mini_statement_e2e.py`:
  - Create account A with Rs 10,000
  - Create account B with Rs 5,000
  - Transfer Rs 2,000 from A to B
  - Transfer Rs 1,500 from B to A
  - Fetch mini statement for A → Should show 2 transactions:
    - Most recent: CREDIT from B (1500)
    - Older: DEBIT to B (2000)
  - Fetch mini statement for B → Should show 2 transactions:
    - Most recent: DEBIT to A (1500)
    - Older: CREDIT from A (2000)
  - Verify all details: timestamps, amounts, balances, types, masked accounts

- [ ] T021 [P] Write performance test in `apps/api/tests/integration/test_mini_statement_performance.py`:
  - Fetch mini statement for account with 20 transactions
  - Measure response time
  - Target: <1 second (per SC-001)
  - Verify no N+1 query issues (should be 2 DB queries: account + transactions)

- [ ] T022 [P] Write documentation in `specs/004-mini-statement/` (reference existing):
  - Link to API contract: `contracts/mini-statement-api.md`
  - Link to data model: `data-model.md`
  - Link to quickstart: `quickstart.md`
  - Create IMPLEMENTATION_NOTES.md:
    - How to run mini statement tests: `pytest apps/api/tests/ -k "mini_statement" -v`
    - How to test via curl: Example curl commands
    - Common issues and troubleshooting

- [ ] T023 Update React/Vite UI in `apps/web/src/features/mini_statement/` (or appropriate component):
  - Create MiniStatementView component to display mini statement
  - Fetch mini statement via `/api/v1/accounts/{account_number}/mini-statement`
  - Display current balance prominently
  - Display transactions in table:
    - Columns: Date, Description, Type (DEBIT/CREDIT), Amount, Balance After
    - Row colors: DEBIT = red/negative, CREDIT = green/positive (or indicators)
  - Handle loading state, error state (401, 404), and empty state
  - Responsive design for mobile
  - Link from account detail view to mini statement

- [ ] T024 [P] Run full test suite:
  - `pytest apps/api/tests/ -v` (all tests pass)
  - Verify existing tests still pass (backward compatibility)
  - Check for no regressions in auth, masking, or transfer features

- [ ] T025 [P] Verify Constitution compliance in `apps/api/tests/integration/test_constitution_mini_statement.py`:
  - Principle I (Exact Monetary Arithmetic): All amounts use Decimal, 2 places ✓
  - Principle II (Account Data Confidentiality): No full account numbers in response ✓
  - Principle III (Every Rule Has a Test): All FR's have acceptance tests ✓
  - Principle IV (Versioned API Contract): Endpoint uses `/api/v1` ✓
  - Principle V (React Web Client Uses API): UI calls `/api/v1` endpoint ✓

- [ ] T026 [P] Write browser/manual testing guide in `specs/004-mini-statement/BROWSER_TESTING.md`:
  - Prerequisites: API running, at least one account with transactions
  - Test steps: Navigate to mini statement view, verify balance and transactions display
  - Test: Click on transaction → verify details (if detail view available)
  - Test: Check that account numbers are masked in UI
  - Test: Verify timestamps are readable (ISO 8601 IST)
  - Test: Verify DEBIT/CREDIT labels are clear
  - Test: Mobile responsiveness (if applicable)

- [ ] T027 Update project FEATURE-STATUS.md to mark mini statement as complete

---

## Implementation Strategy

### MVP Scope (Phases 1–3 Only)
Start with User Story 1 (View Mini Statement):
1. T001-T003: Response schemas
2. T004-T007: Service layer with tests
3. T008-T014: Route handler and API/integration tests

**Result**: Customers can view their mini statement with last 10 transactions and current balance.

### Full Scope (All Phases)
After MVP, add:
4. T015-T019: Transaction direction classification
5. T020-T027: Polish, documentation, UI, and verification

---

## Parallel Execution Examples

### Day 1: Schemas & Service Layer (Can run in parallel)
```
Developer A: T001, T002, T003 (Response schemas + tests)
Developer B: T004, T005, T006 (Service + utility functions)
Developer C: T007 (Service unit tests)
→ Merge when all complete
```

### Day 2: Route & API Tests (Can run in parallel after Day 1)
```
Developer A: T008, T009 (Route handler + app registration)
Developer B: T010, T011, T012, T013, T014 (API + integration tests for US1)
→ Verify together; all tests should pass
```

### Day 3: Transaction Direction & Polish (Can run in parallel)
```
Developer A: T015, T016, T017, T018, T019 (Transaction type classification)
Developer B: T020, T021, T022 (E2E test, performance, docs)
Developer C: T023, T024 (React UI, full test suite)
Developer D: T025, T026, T027 (Constitution compliance, browser testing, status update)
```

---

## Task Format Validation

✅ All tasks follow checklist format: `- [ ] [Task ID] [Parallelizable?] [Story?] Description with file path`

✅ Task IDs sequential (T001–T027)

✅ Story labels present for US1, US2 tasks ([US1], [US2])

✅ Parallelizable tasks marked with [P]

✅ All file paths are explicit and absolute

---

## Summary

- **Total Tasks**: 27
- **MVP Tasks**: 14 (T001–T014)
- **Full Scope Tasks**: 27 (T001–T027)
- **Estimated Duration**: 4–5 days (2–3 developers)
- **Test Coverage**: Unit, integration, API, E2E, performance, and constitution compliance tests
- **Ready to Implement**: Yes; all dependencies mapped, parallelization identified, file paths concrete

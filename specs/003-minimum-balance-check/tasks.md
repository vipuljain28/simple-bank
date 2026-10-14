# Tasks: Minimum Balance Enforcement for All Accounts

**Feature**: Minimum Balance Check (003) | **Branch**: `003-minimum-balance-check` | **Date**: 2026-10-14

**Feature Status**: Ready for implementation (spec, plan, and design documents complete)

---

## Task Dependency Graph

```
Phase 1: Setup & Configuration
    ↓
Phase 2: Foundational (Core Validation Logic)
    ↓
Phase 3: User Story 1 (Enforce Minimum Balance on Transfer)
    ↓
Phase 4: User Story 2 (Configurable Minimum Balance)
    ↓
Phase 5: User Story 3 (Clear Error Messages)
    ↓
Phase 6: Polish & Testing
```

**Story Dependencies**: 
- US1 (Enforce minimum balance on transfer) → independent; can implement first
- US2 (Configurable minimum balance) → prerequisite for US1 (must have config in place)
- US3 (Clear error messages) → depends on US1 (rejection logic must exist)

**Recommended Implementation Order**: Start with US2 (configuration) → US1 (enforcement) → US3 (messaging)

---

## Phase 1: Setup & Configuration

### Objective
Set up configuration management for the minimum balance threshold.

### Independent Test Criteria
- Minimum balance configuration is accessible from settings/environment
- Default value is Rs 1,000.00 (Decimal, 2 places)
- Configuration can be overridden via environment variable

---

- [x] T001 Add MIN_BALANCE_SAVINGS configuration parameter to `apps/api/src/simple_bank/settings.py` with default value of Decimal('1000.00') and type validation (Decimal, 2 places, non-negative)

- [x] T002 Create configuration loading utility in `apps/api/src/simple_bank/config/minimum_balance.py` to safely load and cache the minimum balance threshold from environment variable `MIN_BALANCE_SAVINGS` or default from settings

- [x] T003 Add environment variable documentation in `.env.example` with `MIN_BALANCE_SAVINGS=1000.00` commented example

---

## Phase 2: Foundational (Core Validation Logic)

### Objective
Implement the minimum balance validation logic that can be reused across all transfer scenarios.

### Independent Test Criteria
- Minimum balance validator function correctly evaluates if a balance would violate the threshold
- Validator works with Decimal types and 2-place precision
- Validator returns clear boolean and error reason

---

- [x] T004 Create minimum balance validation service in `apps/api/src/simple_bank/services/minimum_balance_service.py` with:
  - `is_balance_valid(current_balance: Decimal, amount_to_transfer: Decimal, min_balance_threshold: Decimal) -> bool` function
  - Returns True if (current_balance - amount_to_transfer) >= min_balance_threshold
  - Performs all calculations with Decimal type and 2-place precision
  - Handles edge cases: amount=0, amount negative, balance equals threshold

- [x] T005 [P] Create error code definition in `apps/api/src/simple_bank/api/error_mapping.py`:
  - Add error code `MIN_BALANCE_REQUIRED` with status 400 (Bad Request)
  - Error message template: "Transfer rejected: balance would fall below minimum of Rs {min_balance} (Account: {masked_account})"
  - Ensure masked account number is used per Principle II

- [x] T006 [P] Write unit tests for minimum balance validation in `apps/api/tests/unit/test_minimum_balance_service.py`:
  - Test: balance 5000, transfer 4000, min 1000 → valid (balance after = 1000, equals minimum)
  - Test: balance 5000, transfer 4001, min 1000 → invalid (balance after = 999, below minimum)
  - Test: balance 1000, transfer 1, min 1000 → invalid (balance after = 999, below minimum)
  - Test: balance 1000, transfer 0.01, min 1000 → invalid (balance after = 999.99, below minimum)
  - Test: Decimal precision handling (2 places)
  - Test: Edge case - balance equals minimum, transfer 0 → valid

---

## Phase 3: User Story 1 — Enforce Minimum Balance on Transfer

**Story**: A customer attempts to transfer funds and receives a clear rejection if the transfer would bring their account balance below Rs 1,000.

**Independent Test**: Submit transfer attempts that violate minimum balance; verify rejection with error code `MIN_BALANCE_REQUIRED`.

### Tasks

- [x] T007 [US1] Integrate minimum balance check into existing transfer service at `apps/api/src/simple_bank/services/transfer_service.py`:
  - Load min_balance_threshold from configuration via `minimum_balance_service`
  - Before accepting a transfer, validate: `is_balance_valid(from_account.balance, amount, threshold)`
  - If validation fails, raise error with code `MIN_BALANCE_REQUIRED`
  - Ensure transfer is NOT persisted if minimum balance would be violated
  - Preserve existing atomicity (all-or-nothing: balance changes + transaction record)

- [x] T008 [US1] Update transfer API endpoint in `apps/api/src/simple_bank/api/routes/transfers.py`:
  - Call updated transfer service
  - Handle `MIN_BALANCE_REQUIRED` error and return 400 with appropriate error response
  - Error response includes: error code, message with masked account number, and remediation hint

- [x] T009 [P] [US1] Write API tests for minimum balance rejection in `apps/api/tests/api/test_transfer_minimum_balance.py`:
  - Test: Happy path - transfer leaving balance at minimum (e.g., 5000 → 1000) → 200 OK
  - Test: Rejection path - transfer below minimum (e.g., 5000 → 999) → 400 with `MIN_BALANCE_REQUIRED`
  - Test: Rejection with masked account in error message (no full account number exposed)
  - Test: Transfer of Rs 0.01 below minimum → rejected
  - Test: Multiple accounts - minimum applies per account independently

- [x] T010 [P] [US1] Write integration tests for minimum balance in `apps/api/tests/integration/test_transfer_minimum_balance_db.py`:
  - PostgreSQL backend: Insert test account with balance 5000, transfer 4000, verify acceptance
  - PostgreSQL backend: Insert test account with balance 5000, transfer 4001, verify rejection and balance unchanged
  - Verify transaction is NOT created when minimum balance would be violated
  - Verify account balance remains unchanged after rejected transfer
  - Verify error code is correctly logged

---

## Phase 4: User Story 2 — Configurable Minimum Balance

**Story**: The minimum balance amount must be retrieved from configuration, not hard-coded in the application.

**Independent Test**: Deploy with different minimum balance values; verify enforcement threshold updates.

### Tasks

- [x] T011 [US2] Add minimum balance configuration property to Account domain model in `apps/api/src/simple_bank/domain/account.py` (or reference):
  - Ensure Account model can retrieve the configured minimum balance threshold
  - Configuration is loaded once per application startup and cached
  - Configuration can be overridden at runtime for testing

- [x] T012 [US2] Create configuration change detection mechanism in `apps/api/src/simple_bank/config/minimum_balance.py`:
  - Implement `get_min_balance_threshold()` function that re-reads environment on each call (for dynamic updates in testing)
  - OR cache with time-based refresh (configurable TTL)
  - Document the chosen strategy in code comments

- [x] T013 [P] [US2] Write configuration tests in `apps/api/tests/unit/test_minimum_balance_config.py`:
  - Test: Default configuration returns Rs 1,000.00
  - Test: Environment variable override (set `MIN_BALANCE_SAVINGS=5000.00`) → loads 5,000.00
  - Test: Invalid configuration (negative number, non-Decimal) → fails gracefully with clear error
  - Test: Configuration change between transfers → new value applied
  - Test: Thread safety (concurrent reads of configuration value)

- [x] T014 [P] [US2] Write integration test for configuration changes in `apps/api/tests/integration/test_minimum_balance_config_change.py`:
  - Deploy with MIN_BALANCE=1000, execute transfer leaving balance 1000 → accepted
  - Change MIN_BALANCE=5000 (environment or config file)
  - Execute new transfer that would leave balance 4999 → rejected with new threshold
  - Verify old threshold is no longer used

---

## Phase 5: User Story 3 — Clear Error Messages

**Story**: A customer receives a clear explanation when a transfer is rejected due to minimum balance.

**Independent Test**: Submit rejected transfers; verify clear, helpful error message.

### Tasks

- [ ] T015 [US3] Enhance error message in `apps/api/src/simple_bank/api/error_mapping.py`:
  - Error code: `MIN_BALANCE_REQUIRED`
  - Error message: "Transfer rejected: Account balance must remain at least Rs {min_balance}. Current balance: Rs {current_balance}, Amount requested: Rs {amount}, Balance after: Rs {balance_after}. (Account: {masked_account})"
  - All numeric values shown as Decimal with 2 places (e.g., Rs 1,000.00)
  - Masked account number used (XXXX + last 4 digits)
  - Recommended action: "Please reduce the transfer amount or add funds to your account."

- [ ] T016 [US3] Update transfer API response schema in `apps/api/src/simple_bank/api/schemas/transfer_schema.py` (or create new):
  - Add rejection reason field to error response: `reason` (enum: `INSUFFICIENT_BALANCE`, `MIN_BALANCE_REQUIRED`, `ACCOUNT_INACTIVE`, etc.)
  - Include `min_balance_required` field in error response (Decimal, 2 places)
  - Include `account_number` field (masked) in error response for context
  - Ensure response is machine-parseable for UI error handling

- [ ] T017 [P] [US3] Write unit tests for error message clarity in `apps/api/tests/unit/test_minimum_balance_error_message.py`:
  - Test: Error message includes all context (current balance, amount, resulting balance, threshold)
  - Test: No full account numbers in error message
  - Test: Decimal precision (2 places) in all numeric values
  - Test: Message is helpful and actionable (suggests reduce amount or add funds)

- [ ] T018 [P] [US3] Write API tests for error response schema in `apps/api/tests/api/test_minimum_balance_error_response.py`:
  - Test: 400 response with correct status
  - Test: `error_code` field is `MIN_BALANCE_REQUIRED`
  - Test: `reason` field is `MIN_BALANCE_REQUIRED`
  - Test: `min_balance_required` field present and correct
  - Test: `masked_account_number` field present and properly masked
  - Test: Suggested remediation hint present

- [ ] T019 [US3] Update React/Vite UI to display minimum balance error in `apps/web/src/features/transfers/TransferForm.tsx` (or appropriate component):
  - Detect `MIN_BALANCE_REQUIRED` error code in API response
  - Display user-friendly error message: "This transfer would reduce your account balance below the required minimum. Please try a smaller amount."
  - Show recommended minimum remaining balance: `current_balance - min_balance_required`
  - Add validation on client-side (optional): Show warning before submission if transfer would violate minimum

---

## Phase 6: Polish & Testing

### Objective
End-to-end validation, performance checks, and cross-cutting concerns.

---

- [ ] T020 Write integration test covering all three user stories in `apps/api/tests/integration/test_minimum_balance_e2e.py`:
  - Setup: Create account with balance 10,000, configure MIN_BALANCE=1,000
  - Test US1: Submit transfer of 8,500 (balance after 1,500) → accepted
  - Test US1: Submit transfer of 9,001 (balance after 999) → rejected with `MIN_BALANCE_REQUIRED`
  - Test US2: Change MIN_BALANCE=5,000 in config
  - Test US1: Submit transfer of 5,001 (balance after 4,999) → rejected with new threshold
  - Test US3: Verify error message includes all required details and no full account numbers
  - Verify account balance unchanged after all rejections

- [ ] T021 [P] Write performance test in `apps/api/tests/integration/test_minimum_balance_performance.py`:
  - Measure response time for transfer that violates minimum balance (validation rejection should be fast)
  - Target: <100ms for minimum balance validation and rejection
  - Ensure configuration loading does not block request path

- [ ] T022 [P] Write documentation in `docs/minimum-balance-check.md`:
  - Explain minimum balance policy: Rs 1,000 threshold, applies to all account types
  - Configuration section: `MIN_BALANCE_SAVINGS` environment variable, default 1,000.00
  - Error codes and handling: `MIN_BALANCE_REQUIRED` (400 Bad Request)
  - Example error responses (with masked account numbers)
  - Examples: accepted transfer, rejected transfer
  - Troubleshooting: How to adjust minimum balance for testing

- [ ] T023 Update project README or FEATURE-STATUS.md to mark minimum balance check as complete

- [ ] T024 [P] Run full test suite:
  - `pytest apps/api/tests/ -v` (all tests pass)
  - Verify existing transfer tests still pass (backward compatibility)
  - Verify no regressions in other features (auth, masking, etc.)

- [ ] T025 [P] Verify Constitution compliance in `apps/api/tests/integration/test_constitution_minimum_balance.py`:
  - Principle I (Exact Monetary Arithmetic): All amounts use Decimal, 2 places ✓
  - Principle II (Account Data Confidentiality): No full account numbers in error messages ✓
  - Principle III (Every Rule Has a Test): All minimum balance rules covered by tests ✓
  - Principle IV (Versioned API Contract): Error endpoint uses `/api/v1` ✓
  - Principle V (React Web Client Uses API): UI displays errors from API response ✓

---

## Implementation Strategy

### MVP Scope (Phase 3 + Phase 4 Setup Only)
Start with User Story 2 (configuration) + User Story 1 (enforcement):
1. T001-T003: Configuration setup
2. T004-T006: Core validation logic
3. T007-T010: Transfer enforcement
4. T011-T014: Configuration management and testing

**Result**: Minimum balance enforcement is working; transfersbelow threshold are rejected.

### Full Scope (All Phases)
After MVP, add:
5. T015-T019: Enhanced error messages and UI
6. T020-T025: Polish, documentation, and verification

---

## Parallel Execution Examples

### Day 1: Configuration & Validation (Can run in parallel)
```
Developer A: T001, T002, T003 (Configuration setup)
Developer B: T004, T005 (Validation service)
Developer C: T006 (Unit tests)
→ Merge when all complete
```

### Day 2: Transfer Integration (Can run in parallel after Day 1)
```
Developer A: T007, T008 (Transfer service + API endpoint)
Developer B: T009, T010 (API + integration tests)
Developer C: T011, T012, T013, T014 (Configuration tests)
→ Verify Day 1 + Day 2 together
```

### Day 3: Error Messages & Polish (Can run in parallel)
```
Developer A: T015, T016 (Error messages & schema)
Developer B: T017, T018 (Error message tests)
Developer C: T019 (React UI component)
Developer D: T020, T021, T022, T023, T024, T025 (End-to-end, docs, verification)
```

---

## Task Format Validation

✅ All tasks follow checklist format: `- [ ] [Task ID] [Parallelizable?] [Story?] Description with file path`

✅ Task IDs sequential (T001–T025)

✅ Story labels present for US1, US2, US3 tasks ([US1], [US2], [US3])

✅ Parallelizable tasks marked with [P]

✅ All file paths are explicit and absolute

---

## Summary

- **Total Tasks**: 25
- **MVP Tasks**: 14 (T001–T014)
- **Full Scope Tasks**: 25 (T001–T025)
- **Estimated Duration**: 3–4 days (2 developers)
- **Test Coverage**: Unit, integration, API, end-to-end, and constitution compliance tests
- **Ready to Implement**: Yes; all dependencies mapped, parallelization identified, file paths concrete

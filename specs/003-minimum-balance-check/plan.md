# Implementation Plan: Minimum Balance Enforcement for All Accounts

**Branch**: `003-minimum-balance-check` | **Date**: 2026-10-14 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/003-minimum-balance-check/spec.md`

## Summary

All accounts in Simple Bank must maintain a minimum balance of Rs 1,000. Before accepting any debit transaction (transfer or withdrawal), the system validates that the resulting balance would not fall below the configured minimum. Rejected transfers return error code `MIN_BALANCE_REQUIRED` with the masked account number per Constitutional requirements. The minimum balance threshold is configurable via `MIN_BALANCE_SAVINGS` parameter to support future policy changes.

**Technical approach**: Add validation layer to transfer service that checks `balance - amount >= MIN_BALANCE_SAVINGS` before accepting transactions. Configuration-driven threshold allows runtime policy updates. Decimal arithmetic ensures monetary precision. Error responses include masked account number consistent with existing transfer error patterns.

## Technical Context

**Language/Version**: Python 3.12 (verified in existing codebase)

**Primary Dependencies**: FastAPI, SQLAlchemy, Pydantic (existing; no new dependencies)

**Storage**: PostgreSQL with SQLite fallback for development (existing)

**Testing**: pytest with pytest-cov (existing)

**Target Platform**: Linux server with Docker deployment (existing)

**Project Type**: Web service (FastAPI backend + React frontend)

**Performance Goals**: Minimum balance validation adds <10 ms latency to transaction processing

**Constraints**: 
- Decimal precision to paisa (0.01 rupee)
- Account number masking in all error responses (XXXX1234 format)
- Configuration-driven, not hard-coded thresholds

**Scale/Scope**: Applies to all accounts; no account-type filtering. Single validation layer reused by all debit transactions.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

✅ **Principle I (Exact Monetary Arithmetic)**: Decimal type required; validation on Decimal amounts. ✅ PASS

✅ **Principle II (Account Data Confidentiality)**: Error responses include masked account (XXXX1234). ✅ PASS

✅ **Principle III (Every Rule Has a Test)**: Spec includes 6 acceptance scenarios + edge cases. ✅ PASS

✅ **Principle IV (Versioned API Contract)**: Error code `MIN_BALANCE_REQUIRED` part of `/api/v1` contract. ✅ PASS

✅ **Principle V (React Web Client Uses the API)**: Error responses flow through API; client consumes via standard error handling. ✅ PASS

**Gate Status**: ✅ **CLEAR** — All constitutional principles satisfied.

## Project Structure

### Documentation (this feature)

```text
specs/003-minimum-balance-check/
├── spec.md                  # Feature specification ✅
├── plan.md                  # This file (implementation plan) ✅
├── research.md              # Phase 0: Research & unknowns ✅
├── data-model.md            # Phase 1: Entity model ✅
├── quickstart.md            # Phase 1: Validation guide ✅
├── contracts/
│   └── transfer-errors.md   # Phase 1: Error response contract ✅
├── CLARIFY-SUMMARY.md       # Clarifications from /speckit-clarify ✅
└── checklists/
    └── requirements.md      # Quality checklist ✅
```

### Source Code (repository root) — Option 2: Web application

```text
apps/api/
├── src/simple_bank/
│   ├── api/
│   │   ├── routes/
│   │   │   └── transfers.py           # Existing; add minimum balance validation
│   │   ├── schemas/
│   │   │   └── transfers.py           # Existing transfer schemas; error types
│   │   └── error_mapping.py           # Existing; map MIN_BALANCE_REQUIRED
│   ├── domain/
│   │   ├── transfers.py               # Existing; add minimum balance rule
│   │   ├── errors.py                  # Existing; add MinimumBalanceViolation
│   │   └── account_numbers.py         # Existing; masking logic
│   ├── services/
│   │   └── transfer_service.py        # Existing; add minimum balance check
│   ├── persistence/
│   │   └── database.py                # Existing config loading
│   └── settings.py                    # Existing; add MIN_BALANCE_SAVINGS config
└── tests/
    ├── api/
    │   └── test_minimum_balance.py     # NEW: API integration tests
    ├── unit/
    │   └── test_minimum_balance_validation.py  # NEW: Unit tests
    └── integration/
        └── test_minimum_balance_transfer.py    # NEW: End-to-end tests

apps/web/
└── src/features/transfers/
    └── TransferForm.tsx               # Existing; display MIN_BALANCE_REQUIRED errors
```

## Design Artifacts

### Phase 0: Research (Completed)

**Deliverable**: `research.md`

**Contents**:
- Resolution of all technical ambiguities (account type scope, configuration parameter, account masking)
- Dependency analysis (all existing; no new dependencies)
- Integration points (transfer service, configuration loading, error response schema)
- Technology recommendations (Decimal arithmetic, configuration strategy, error format)
- Testing strategy (unit, integration, API contract, manual)
- Risk mitigation plan

**Status**: ✅ **COMPLETE**

---

### Phase 1: Design (Completed)

#### Artifact 1: Data Model (`data-model.md`)

**Entities Defined**:
- **Account** (existing; updated with minimum balance validation rules)
- **Transfer Request** (existing; new validation rules added)
- **Configuration Parameter** (new; stores MIN_BALANCE_SAVINGS)
- **Error Response Schema** (new; returned on validation failure)

**State Transitions**:
- Transfer lifecycle with minimum balance gate (PENDING → APPROVED or REJECTED)

**Validation Rules**:
- Decimal precision to paisa (2 decimal places)
- Account masking format (XXXX1234)
- Configuration parameter loading (env var or database)

**Relationships**:
- Account ↔ TransferRequest (1:Many)
- Global Configuration ↔ MIN_BALANCE_SAVINGS (1:1)

**Indexing Strategy**: Balance queries, account lookups, transfer status filtering

**Status**: ✅ **COMPLETE** (7.9 KB)

---

#### Artifact 2: API Contract (`contracts/transfer-errors.md`)

**Endpoint**: POST /api/v1/transfers (existing endpoint; new validation)

**Error Response (422 Unprocessable Entity)**:

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

**Field Specifications**:
- All monetary amounts as Decimal-formatted strings (2 places)
- Account always masked (XXXX format)
- Status code: 422 (not 400, not 403)

**Test Scenarios**:
- Transfer at threshold (allowed): 5,000 → 4,000 = 1,000 ✅
- Transfer below threshold (rejected): 5,000 → 4,001 = 999 ❌
- Exact minimum + 1: 1,000 → 1 = 999 ❌
- Paisa precision: 1,000 → 0.01 = 999.99 ❌

**Status**: ✅ **COMPLETE** (6.8 KB)

---

#### Artifact 3: Quickstart Validation Guide (`quickstart.md`)

**Purpose**: Runnable end-to-end validation scenarios

**Test Cases**:
1. Transfer at threshold (allowed)
2. Transfer below threshold (rejected)
3. Exact minimum + small withdrawal (rejected)
4. Paisa precision (rejected)
5. Configuration parameter testing (override MIN_BALANCE_SAVINGS)
6. Account masking verification

**Validation Method**:
- Manual curl commands for each scenario
- Automated pytest test suite
- Web UI manual validation
- Coverage and success criteria

**Status**: ✅ **COMPLETE** (9.6 KB)

---

## Post-Phase 1 Constitution Check

*GATE: Must pass before proceeding to Phase 2 (Task generation).*

✅ **Principle I (Exact Monetary Arithmetic)**: 
- Data model uses Decimal type throughout
- Contract specifies Decimal-formatted strings for all amounts
- Quickstart tests verify paisa precision (0.01)
- ✅ PASS

✅ **Principle II (Account Data Confidentiality)**:
- Data model documents account masking rules
- Contract specifies XXXX1234 format in error responses
- Quickstart includes account masking verification test
- ✅ PASS

✅ **Principle III (Every Rule Has a Test)**:
- Spec includes 6 acceptance scenarios
- Data model lists 4 edge cases
- Quickstart includes 4 automated test cases + 6 verification checks
- ✅ PASS

✅ **Principle IV (Versioned API Contract)**:
- Contract defined for /api/v1/transfers endpoint
- Error code MIN_BALANCE_REQUIRED is standardized
- Response schema is versioned
- ✅ PASS

✅ **Principle V (React Web Client Uses the API)**:
- Web UI integration mentioned in project structure
- Error message format is user-friendly (not machine-readable error code)
- Quickstart includes Web UI manual validation scenario
- ✅ PASS

**Gate Status**: ✅ **CLEAR** — Design passes all constitutional principles. Ready for Phase 2.

---

## Design Decisions Summary

| Decision | Choice | Rationale | Alternatives Rejected |
|----------|--------|-----------|----------------------|
| Minimum balance scope | Apply to ALL account types | Clarity from /speckit-clarify; simpler implementation | Account-type-specific thresholds |
| Configuration location | Env var → Database → Default (1000.00) | Flexibility (env override) + persistence (DB) + fallback | Hard-coded constant; single source only |
| Data type for amounts | Python Decimal | Constitution Principle I; exact arithmetic; project standard | Float (loses precision); int (no fractional rupees) |
| Error HTTP status | 422 Unprocessable Entity | Semantic correctness (rule violation, not bad input) | 400 Bad Request; 403 Forbidden |
| Account masking format | XXXX{last_4_digits} | Industry standard (credit cards); Constitution Principle II | Full account number; just UUID |
| Configuration parameter name | MIN_BALANCE_SAVINGS | Explicit; domain-clear; allows future MIN_BALANCE_CHECKING | MIN_BAL; MINIMUM_BALANCE; MIN_BALANCE_ALL |

---

## Next Steps

### Immediate (End of Phase 1)

- ✅ Design artifacts completed (data-model.md, contracts/, quickstart.md, research.md)
- ✅ Constitution check passed
- → **Proceed to Phase 2**: Run `/speckit-tasks` to generate implementation task breakdown

### Phase 2 (Task Generation)

**Command**: `/speckit-tasks spec 003`

**Output**: `tasks.md` with dependency-ordered implementation tasks

**Typical tasks** (generated by /speckit-tasks):
1. Add MIN_BALANCE_SAVINGS to settings.py
2. Create MinimumBalanceViolation error class
3. Implement validation logic in transfer service
4. Add 422 error response handler in API routes
5. Write unit tests for validation
6. Write integration tests for error responses
7. Write E2E tests via web UI
8. Update API documentation

### Phase 3 (Implementation)

**Command**: `/speckit-implement tasks 003`

**Input**: tasks.md from Phase 2

**Output**: Fully implemented feature with tests passing

---

## Success Criteria

Feature implementation is complete when:

- [ ] All tests pass: `pytest apps/api/tests/ -v`
- [ ] Code coverage: ≥90% for minimum balance validation logic
- [ ] Contract verified: 422 response format matches `contracts/transfer-errors.md`
- [ ] Quickstart guide runs successfully end-to-end
- [ ] Account masking verified: No full account number in responses/logs
- [ ] Configuration tested: MIN_BALANCE_SAVINGS can be overridden
- [ ] Web UI updated: Error message displays to user
- [ ] PR created and passes CI/CD checks
- [ ] Human approval obtained before merge

---

## Files Generated in Phase 1

| File | Size | Purpose |
|------|------|---------|
| `research.md` | 11.1 KB | Technical validation; dependency analysis |
| `data-model.md` | 8.1 KB | Entity definitions; validation rules; relationships |
| `contracts/transfer-errors.md` | 6.8 KB | API error response specification |
| `quickstart.md` | 9.6 KB | End-to-end validation scenarios |
| `plan.md` | This file | Implementation roadmap |

**Total Documentation**: ~43.5 KB

---

## Appendix: Git Branch & CI/CD

**Branch Name**: `003-minimum-balance-check`

**Branch Workflow**:

```bash
# Start from main
git checkout main
git pull origin main

# Create feature branch
git checkout -b 003-minimum-balance-check

# After tasks generated:
# - Make commits following task breakdown
# - Push to origin
# - Open PR (CI/CD runs automatically)
# - Request review (human review before merge)
# - Merge to main only after approval
```

**CI/CD Pipeline** (automatic on PR):

1. Lint: `black --check apps/api/` (Python formatting)
2. Type check: `mypy apps/api/src/` (static type analysis)
3. Unit tests: `pytest apps/api/tests/unit/ -v` (validation logic)
4. Integration tests: `pytest apps/api/tests/integration/ -v` (with database)
5. Coverage: `pytest apps/api/tests/ --cov=simple_bank --cov-report=term-missing` (≥90%)

**Branch Protection**: Main branch requires ≥1 approval + all checks passing before merge.

---

```

**Structure Decision**: [Document the selected structure and reference the real
directories captured above]

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |

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
├── plan.md                  # This file (implementation plan)
├── research.md              # Phase 0: Research & unknowns (to be generated)
├── data-model.md            # Phase 1: Entity model (to be generated)
├── quickstart.md            # Phase 1: Validation guide (to be generated)
├── contracts/
│   └── transfer-errors.md   # Phase 1: Error response contract (to be generated)
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
```

**Structure Decision**: [Document the selected structure and reference the real
directories captured above]

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |

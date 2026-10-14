# Implementation Plan: Fund Transfer

**Branch**: `main` | **Date**: 2026-10-14 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-fund-transfer/spec.md`

## Summary

Update the existing `POST /api/v1/transfers` flow so its daily cap is selected from the sending account's age: Rs 50,000 before 30×24 hours since opening, and Rs 1,00,000 at or after that instant. Aggregate accepted transfer amounts per sending account and India Standard Time day. Keep rule evaluation in the existing `TransferService` and atomically persist accepted transfers with both balance changes. Add and backfill an account-opening timestamp without changing existing customers' effective cap; preserve the current React/Vite `/api/v1` boundary.

## Technical Context

**Language/Version**: Python 3.12 for the API; TypeScript for the constitution-required React/Vite client

**Primary Dependencies**: uv, FastAPI, Pydantic, SQLAlchemy 2, psycopg 3, pytest; React and Vite for the web client

**Storage**: Existing PostgreSQL account and transaction tables; additive migration adds a time-zone-aware account opening timestamp. Existing accounts are backfilled as at least 30×24 hours old and therefore retain the Rs 1,00,000 cap. New accounts record their opening instant. Transaction rows already identify the sending account and store exact numeric amounts.

**Testing**: pytest unit tests for `TransferService`; PostgreSQL-backed API and integration tests; browser-level validation for the React client

**Target Platform**: Python 3.12 server and modern web browsers

**Project Type**: Web application with a Python API and React/Vite client

**Performance Goals**: Customer-visible accepted or rejected outcome within one second, including additional verification, per FR-008

**Constraints**: Monetary arithmetic uses `Decimal` and two decimal places; age is elapsed time from a time-zone-aware opening timestamp, with the standard limit applying at exactly 30×24 hours; daily totals reset at midnight India Standard Time and are separate per sending account; transfer record and both balance changes are all-or-nothing; API routes use `/api/v1`; the web client communicates only through that API; full account numbers must not appear in logs or displayed output; accepted retries must not apply a transfer twice.

**Scale/Scope**: Initial fund-transfer workflow only. Throughput, account volume, availability, and recovery objectives are not specified; correctness must hold for concurrent requests.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Plan response |
|-----------|------|---------------|
| Exact monetary arithmetic | Use exact decimal values rounded to two places; test representation and rounding. | Pass: parse decimal strings as `Decimal`, persist exact numeric values, and test two-place validation. |
| Account data confidentiality | Never log full account numbers; display only `XXXX` plus the last four digits. | Pass: mask account numbers in API responses and UI; exclude full values from logs and operational output. |
| Every rule has a test | Each constitutional and product rule has automated coverage. | Pass: test both caps, exact age boundary, per-sender-account daily totals, IST reset, and legacy-account migration behavior through unit and PostgreSQL integration tests. |
| Versioned API contract | All application routes begin with `/api/v1`. | Pass: transfer endpoint is `POST /api/v1/transfers`. |
| React web client uses the API | React/Vite client communicates only through `/api/v1`. | Pass: all transfer requests use the API; browser code has no direct persistence or backend access. |

No constitutional violations identified. This is an additive change to the existing account and transfer implementation; no new application or service is required.

## Project Structure

### Documentation (this feature)

```text
specs/001-fund-transfer/
├── plan.md
├── research.md
├── data-model.md
├── contracts/
│   └── transfers-api.md
├── quickstart.md
└── tasks.md              # Created by /speckit-tasks, not this plan
```

### Existing Source Code Structure

```text
apps/
├── api/
│   ├── pyproject.toml
│   ├── uv.lock
│   ├── src/simple_bank/
│   │   ├── api/routes/transfers.py
│   │   ├── services/transfer_service.py
│   │   ├── domain/transfers.py
│   │   ├── domain/transfer_repository.py
│   │   ├── persistence/models/account.py
│   │   ├── persistence/transfer_repository.py
│   │   └── migrations/versions/
│   └── tests/
│       ├── unit/test_transfer_rejections.py
│       ├── api/test_transfer_errors.py
│       └── integration/
└── web/
    └── src/
        ├── features/transfers/TransferForm.tsx
        └── lib/api/transfers.ts
```

**Structure Decision**: Extend `Account` with its opening timestamp and the existing transfer repository interface to expose the sender account's opening time and per-sender daily accepted total. Keep cap selection in `TransferService`, based on its injected clock, so unit tests can exercise the exact elapsed-time boundary. The PostgreSQL repository continues to lock account rows in deterministic order and commit the transaction and both balance changes atomically. Add migration `004_account_opening_time.sql` to add the timestamp, backfill existing accounts as at least 30×24 hours old, and ensure new accounts record their actual opening instant. Update transfer-form guidance so it describes both possible caps and states that the limit applies per sending account; do not let the client choose or submit the cap.

**Post-Design Constitution Re-check**: PASS. The plan retains exact monetary arithmetic, account masking, the `/api/v1` boundary, and atomic accepted-transfer updates. It adds automated coverage for both caps, the exact 30×24-hour transition, per-sending-account aggregation, the IST-day reset, and legacy-account backfill. The React/Vite client continues to use only the API.

## Complexity Tracking

No constitution violations or additional architectural projects require justification.

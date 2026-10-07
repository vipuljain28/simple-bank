# Implementation Plan: Fund Transfer

**Branch**: `001-fund-transfer` | **Date**: 2026-10-07 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-fund-transfer/spec.md`

## Summary

Implement `POST /api/v1/transfers` with FastAPI and PostgreSQL, managed with uv and Python 3.12. Keep the transfer rules and orchestration in a distinct, dependency-injected `TransferService` so its behavior can be unit tested without FastAPI or a live database. Persist an accepted transfer, its idempotency request ID, and both balance changes in one database transaction. The constitution also requires a React/Vite web client that accesses the API only through `/api/v1`.

## Technical Context

**Language/Version**: Python 3.12 for the API; TypeScript for the constitution-required React/Vite client

**Primary Dependencies**: uv, FastAPI, Pydantic, SQLAlchemy 2, psycopg 3, pytest; React and Vite for the web client

**Storage**: PostgreSQL with exact numeric monetary columns and transactional updates

**Testing**: pytest unit tests for `TransferService`; PostgreSQL-backed API and integration tests; browser-level validation for the React client

**Target Platform**: Python 3.12 server and modern web browsers

**Project Type**: Web application with a Python API and React/Vite client

**Performance Goals**: Customer-visible accepted or rejected outcome within one second, including additional verification, per FR-008

**Constraints**: Monetary arithmetic uses `Decimal` and two decimal places; transfer record and both balance changes are all-or-nothing; API routes use `/api/v1`; the web client communicates only through that API; full account numbers must not appear in logs or displayed output; accepted retries must not apply a transfer twice.

**Scale/Scope**: Initial fund-transfer workflow only. Throughput, account volume, availability, and recovery objectives are not specified; correctness must hold for concurrent requests.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Plan response |
|-----------|------|---------------|
| Exact monetary arithmetic | Use exact decimal values rounded to two places; test representation and rounding. | Pass: parse decimal strings as `Decimal`, persist exact numeric values, and test two-place validation. |
| Account data confidentiality | Never log full account numbers; display only `XXXX` plus the last four digits. | Pass: mask account numbers in API responses and UI; exclude full values from logs and operational output. |
| Every rule has a test | Each constitutional and product rule has automated coverage. | Pass: test each rule through `TransferService` and verify transactional behavior against PostgreSQL. |
| Versioned API contract | All application routes begin with `/api/v1`. | Pass: transfer endpoint is `POST /api/v1/transfers`. |
| React web client uses the API | React/Vite client communicates only through `/api/v1`. | Pass: all transfer requests use the API; browser code has no direct persistence or backend access. |

No constitutional violations identified. The workspace has no application source, so the structure below is a proposed greenfield layout.

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

### Proposed Source Code Structure

```text
apps/
├── api/
│   ├── pyproject.toml
│   ├── uv.lock
│   ├── src/simple_bank/
│   │   ├── api/routes/transfers.py
│   │   ├── services/transfer_service.py
│   │   ├── domain/transfers.py
│   │   └── persistence/
│   └── tests/
│       ├── unit/test_transfer_service.py
│       ├── api/
│       └── integration/
└── web/
    └── src/
        ├── features/transfers/
        └── lib/api/
```

**Structure Decision**: Keep the FastAPI transport layer thin and put all transfer rules in `TransferService`, with persistence and verification dependencies injected through interfaces. This gives unit tests a direct service boundary while keeping the React/Vite client on the required `/api/v1` contract. No application directories currently exist.

**Post-Design Constitution Re-check**: PASS. The design uses Python `Decimal` and PostgreSQL exact numeric values, keeps all API routes under `/api/v1`, preserves account masking, performs accepted transfer changes atomically, and provides a unit-testable service plus tests for every rule. The React/Vite client has no direct backend or database access.

## Complexity Tracking

No constitution violations or additional architectural projects require justification.

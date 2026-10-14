# Implementation Plan: Mini Account Statement

**Branch**: `004-mini-statement` | **Date**: 2026-10-14 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/004-mini-statement/spec.md`

## Summary

Add a mini statement endpoint (`GET /api/v1/accounts/{account_number}/mini-statement`) that returns a customer's last 10 transactions and current balance. Transactions are ordered newest-first, account numbers are masked, and all timestamps are ISO 8601 formatted with India Standard Time (IST) timezone. The feature reuses existing Account and Transaction models; no database migrations are required.

## Technical Context

**Language/Version**: Python 3.12 for the API; TypeScript for the React/Vite client

**Primary Dependencies**: FastAPI, Pydantic, SQLAlchemy 2, psycopg 3, pytest

**Storage**: Existing PostgreSQL `accounts` and `transactions` tables. No migrations required; all needed fields already exist.

**Testing**: pytest unit tests for service logic; PostgreSQL-backed API and integration tests; browser-level validation for the React client

**Target Platform**: Python 3.12 server and modern web browsers

**Project Type**: Web application with a Python API and React/Vite client

**Performance Goals**: Customer-visible response within one second (SC-001), including authentication and database queries

**Constraints**: 
- Monetary arithmetic uses `Decimal` with 2 decimal places
- All timestamps in ISO 8601 format with IST timezone offset (+05:30)
- Account numbers always masked in responses (XXXX + last 4 digits)
- Access to unowned accounts returns 404 (prevents enumeration attacks)
- Transactions limited to 10 most recent, ordered newest-first
- API endpoint follows `/api/v1` prefix (Principle IV)
- Web client communicates only through `/api/v1` (Principle V)

**Scale/Scope**: Single endpoint; leverages existing transaction data. Scalability inherits from existing query patterns.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Plan response |
|-----------|------|---------------|
| Exact monetary arithmetic | Use exact decimal values rounded to two places; test representation and rounding. | Pass: `Decimal` type for amounts and balances; Pydantic serialization with 2-place precision; integration tests verify decimal handling. |
| Account data confidentiality | Never log full account numbers; display only `XXXX` plus the last four digits. | Pass: Mask account numbers in all API responses; add masking tests; excluded from logs. |
| Every rule has a test | Each constitutional and product rule has automated coverage. | Pass: Unit tests for masking, authorization, timestamp format, decimal precision, and transaction ordering. Integration tests verify end-to-end behavior. |
| Versioned API contract | All application routes begin with `/api/v1`. | Pass: Endpoint is `GET /api/v1/accounts/{account_number}/mini-statement`. |
| React web client uses the API | React/Vite client communicates only through `/api/v1`. | Pass: Web UI calls `/api/v1` endpoint; no direct database access from frontend. |

**No constitutional violations identified.** This is an additive endpoint on existing infrastructure.

## Project Structure

### Documentation (this feature)

```text
specs/004-mini-statement/
├── spec.md                          # Feature specification
├── plan.md                          # This file (implementation plan)
├── research.md                      # Phase 0 output: Technical decisions
├── data-model.md                    # Phase 1 output: Data entities and schemas
├── contracts/
│   └── mini-statement-api.md       # Phase 1 output: API contract
├── quickstart.md                    # Phase 1 output: Validation guide
├── checklists/
│   └── requirements.md              # Quality checklist (maintained by skills)
└── tasks.md                         # Phase 2 output (/speckit-tasks, NOT created by this plan)
```

### Existing Source Code Structure

```text
apps/
├── api/
│   ├── pyproject.toml
│   ├── uv.lock
│   ├── src/simple_bank/
│   │   ├── api/
│   │   │   ├── app.py               # Main FastAPI app
│   │   │   ├── routes/              # Route modules
│   │   │   │   ├── transfers.py     # (Existing) Transfer endpoint
│   │   │   │   ├── auth.py          # (Existing) Auth endpoint
│   │   │   │   └── [mini_statement.py]  # NEW: Mini statement routes
│   │   │   └── schemas/             # Pydantic request/response schemas
│   │   │       ├── transfer_schema.py
│   │   │       └── [mini_statement_schema.py]  # NEW: Response schemas
│   │   ├── services/                # Business logic
│   │   │   ├── transfer_service.py  # (Existing)
│   │   │   └── [mini_statement_service.py]  # NEW: Mini statement logic
│   │   ├── domain/                  # Domain models
│   │   │   ├── transfers.py
│   │   │   ├── account_numbers.py   # (Existing) Masking utilities
│   │   │   └── [mini_statement.py]  # NEW (optional): Domain logic
│   │   ├── persistence/
│   │   │   └── models/
│   │   │       ├── account.py       # (Existing) Account model
│   │   │       └── transaction.py   # (Existing) Transaction model
│   │   ├── security/                # (Existing) Auth/session handling
│   │   └── error_mapping.py         # (Existing) Error handling
│   └── tests/
│       ├── api/
│       │   └── [test_mini_statement_api.py]  # NEW: API endpoint tests
│       ├── integration/
│       │   └── [test_mini_statement_integration.py]  # NEW: DB integration tests
│       └── unit/
│           └── [test_mini_statement_service.py]  # NEW: Service unit tests
└── web/
    └── src/
        └── features/
            └── [mini_statement/]    # NEW (optional): React components for mini statement UI
```

**Structure Decision**: Add mini statement as a new route module (`routes/mini_statement.py`), paired with a service module (`services/mini_statement_service.py`) and response schemas (`schemas/mini_statement_schema.py`). This mirrors existing patterns (transfers) and keeps concerns separated.

## Complexity Tracking

No constitutional violations or complexity tradeoffs needed. Feature design aligns cleanly with existing project structure and constraints.

| Area | Decision | Rationale |
|------|----------|-----------|
| Route location | `/api/v1/accounts/{account_number}/mini-statement` | Follows RESTful resource naming; `/accounts/{id}/mini-statement` is a sub-resource |
| Query strategy | ORDER BY `created_at DESC LIMIT 10` | Simple, efficient; leverages existing indexed column |
| Balance source | Query `Account.balance` directly, not derived | Source of truth; more reliable than deriving from transactions |
| Authorization | Return 404 for both not-found and unauthorized | Security: prevents account enumeration |
| Timestamp format | ISO 8601 with IST offset | Industry standard; explicit timezone prevents confusion |

---

## Phase 0: Research

**Status**: ✅ COMPLETE | **Output**: [research.md](research.md)

**Decisions resolved**:
1. Transaction query strategy (direct SQL with LIMIT 10)
2. Current balance calculation (query Account.balance)
3. Response format and schema (JSON with masking, timestamps, balances)
4. Transaction type determination (DEBIT/CREDIT based on account perspective)
5. Time zone handling (ISO 8601 with IST +05:30 offset)
6. Authorization and error handling (404 for enumeration prevention)

**Dependencies**: Existing FastAPI, SQLAlchemy, authentication layer — all present.

---

## Phase 1: Design & Contracts

**Status**: ✅ COMPLETE | **Outputs**:
- [data-model.md](data-model.md) — Entity structure and relationships
- [contracts/mini-statement-api.md](contracts/mini-statement-api.md) — Full endpoint specification
- [quickstart.md](quickstart.md) — Validation scenarios and test guide

**Design Summary**:

### Entities Used
- **Account** (existing): Identified by `account_number`; owned by `customer_id`; has `balance` and `status`
- **Transaction** (existing): Tracks `from_account`, `to_account`, `amount`, `created_at`; reuses existing schema
- **MiniStatementResponse** (new schema): Groups current balance and transaction array for serialization

### API Endpoint
```
GET /api/v1/accounts/{account_number}/mini-statement
Authorization: Bearer {token}
Response: 200 OK, 401 Unauthorized, 404 Not Found
```

### Response Schema
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
    }
  ]
}
```

### Data Query Pattern
```sql
SELECT 
  account_number, balance
FROM accounts 
WHERE account_number = ? AND customer_id = ? AND status = 'ACTIVE';

SELECT 
  transaction_id, created_at, from_account, to_account, amount, description
FROM transactions 
WHERE (from_account = ? OR to_account = ?) AND customer_id = ?
ORDER BY created_at DESC
LIMIT 10;
```

### Security Model
- **Authentication**: Verify customer session before proceeding
- **Authorization**: Check account ownership; return 404 if unauthorized or not found
- **Masking**: Apply to all account numbers in response
- **Timestamps**: Convert to IST before serialization

### Testing Strategy
- **Unit tests**: Masking, authorization logic, schema validation, timestamp formatting
- **Integration tests**: Database queries, transaction ordering, balance accuracy, empty accounts
- **API tests**: Happy path (200), unowned account (404), unauthenticated (401), response schema

---

## Next Phase: Task Generation

**Next command**: `/speckit-tasks`

This will generate `tasks.md` with a dependency-ordered list of implementation tasks:
1. Create response schemas (Pydantic models)
2. Implement service layer (business logic)
3. Add route handler (FastAPI endpoint)
4. Write unit tests
5. Write integration tests
6. Add API tests
7. Validation and performance testing

---

## Constitution Compliance: Phase 1 Re-check

All principles verified post-design:

✅ **Exact Monetary Arithmetic**: Decimal serialization with 2-place precision
✅ **Account Data Confidentiality**: Masking applied to account_number field
✅ **Every Rule Has a Test**: Each FR maps to testable acceptance scenario
✅ **Versioned API Contract**: `/api/v1` prefix maintained
✅ **React Web Client Uses API**: Mini statement queried via `/api/v1` only

---

## Artifacts Generated

| File | Purpose | Status |
|------|---------|--------|
| [research.md](research.md) | Technical decisions and patterns | ✅ Complete |
| [data-model.md](data-model.md) | Entity structure and queries | ✅ Complete |
| [contracts/mini-statement-api.md](contracts/mini-statement-api.md) | API contract and responses | ✅ Complete |
| [quickstart.md](quickstart.md) | Validation guide and test scenarios | ✅ Complete |
| tasks.md | Implementation tasks (generated by /speckit-tasks) | ⏳ Pending |

---

## Summary

The mini account statement feature is fully designed and ready for implementation. All technical decisions are documented in research.md, data model and API contract are defined, and validation scenarios are specified in quickstart.md. No database migrations are needed; the feature leverages existing Account and Transaction tables.

**Proceed to**: `/speckit-tasks` to generate the task breakdown for implementation.

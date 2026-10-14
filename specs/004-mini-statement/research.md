# Research: Mini Account Statement

**Feature**: Mini Account Statement (004) | **Branch**: `004-mini-statement` | **Date**: 2026-10-14

## Scope

This research document resolves technical decisions and validates patterns for implementing the mini statement endpoint (`GET /api/v1/accounts/{account_number}/mini-statement`).

## Decisions

### Decision 1: Transaction Query Strategy

**Question**: How should the last 10 transactions be efficiently retrieved from the database?

**Decision**: Query the `transactions` table with ordering by `created_at DESC` and `LIMIT 10`, filtered by the sending account (from_account) to match the account context.

**Rationale**: 
- The existing `Transaction` model stores `created_at` as a timezone-aware DateTime, which is the correct field for ordering by recency.
- A simple `ORDER BY created_at DESC LIMIT 10` is efficient and standard SQL.
- This aligns with existing query patterns in the codebase.

**Alternatives considered**:
- Materialized views or cached transaction lists: Rejected because the transaction volume for this feature is not large enough to justify caching complexity, and the 1-second performance target is easily met with direct queries.
- Pagination with offset: Rejected because the requirement is specifically "last 10" (fixed limit), not paginated browsing.

**Implementation note**: The query must filter transactions where the authenticated customer owns the `from_account`.

### Decision 2: Current Balance Calculation

**Question**: Should the current balance be queried separately or derived from transaction balances?

**Decision**: Query the `Account.balance` column directly; do not derive it from "balance after transaction" fields.

**Rationale**:
- The `Account.balance` is the source of truth and is updated atomically with each transfer.
- Deriving current balance from the most recent transaction's balance-after could fail if transactions are out of order or if there are pending/rejected transactions in the full history.
- Querying `Account.balance` is a single row lookup, which is more efficient and reliable.

**Alternatives considered**:
- Storing balance-after in each Transaction row and using the most recent as current: Rejected because it creates data inconsistency if Account.balance is updated without a corresponding transaction.
- Computing balance by summing all transactions: Rejected because it's computationally expensive and less reliable than the canonical Account.balance.

**Implementation note**: Current balance must be accurate as of the mini statement request time.

### Decision 3: Response Format and Schema

**Question**: What should the JSON response schema look like?

**Decision**: Return a response object with:
- `account_number` (masked, e.g., `XXXX1234`)
- `current_balance` (Decimal, 2 places)
- `transactions` (array of transaction objects, newest first)

Each transaction object includes:
- `timestamp` (ISO 8601 with IST offset, e.g., `2026-10-14T15:30:45+05:30`)
- `description` (string)
- `type` (enum: `DEBIT` or `CREDIT`)
- `amount` (Decimal, 2 places)
- `balance_after` (Decimal, 2 places)

**Rationale**:
- ISO 8601 with timezone offset is industry standard for APIs and unambiguous.
- Masking account numbers at the API boundary enforces Principle II (Account Data Confidentiality).
- Grouping transactions in an array and current balance at the top level is conventional REST design.
- Using `DEBIT`/`CREDIT` enum is clear and testable.

**Alternatives considered**:
- Unix timestamps: Rejected because ISO 8601 is more human-readable and suitable for this use case.
- Sending full account numbers: Rejected because it violates the constitution.
- Nested balance object: Rejected because the flat structure is simpler and adequate.

**Implementation note**: Response schema must be documented in `contracts/mini-statement-api.md` and validated by tests.

### Decision 4: Transaction Type Determination

**Question**: How should transaction type (DEBIT vs CREDIT) be determined from the existing Transaction model?

**Decision**: 
- A transaction is a **DEBIT** if the authenticated customer owns the `from_account`.
- A transaction is a **CREDIT** if the authenticated customer owns the `to_account`.

**Rationale**:
- The existing `Transaction` model tracks `from_account` and `to_account`.
- The mini statement is always viewed from the perspective of one account.
- This logic directly follows the customer's perspective: money leaving is a debit, money arriving is a credit.
- This is consistent with banking terminology and user expectations.

**Alternatives considered**:
- Storing a `type` column in Transaction: Rejected because it would require schema changes and is redundant with from/to account logic.
- Showing both perspectives: Rejected because the spec requires a single account's mini statement, not a transaction ledger view.

**Implementation note**: The query must retrieve all transactions where the account is either `from_account` OR `to_account`, then classify each based on the perspective.

### Decision 5: Time Zone Handling

**Question**: How should transaction timestamps be converted to IST for the API response?

**Decision**: 
- Store all timestamps in the database as UTC or IST (timezone-aware).
- At API serialization time, ensure all DateTime values are converted to IST timezone before JSON serialization.
- Use Python's `pytz` or `zoneinfo` to handle IST conversions.
- Format as ISO 8601 with the `+05:30` offset.

**Rationale**:
- The constitution requires IST timezone for daily limit calculations (reset at midnight IST).
- Serializing with explicit timezone offset (`+05:30`) ensures clients always have unambiguous timestamps.
- Python's datetime handling is mature and well-tested.

**Alternatives considered**:
- Storing everything in UTC and letting clients convert: Rejected because the API contract should be explicit about timezone.
- Using Unix timestamps: Rejected because ISO 8601 is more useful for this API.

**Implementation note**: The serialization layer (Pydantic schema) must handle the conversion.

### Decision 6: Authorization and Error Handling

**Question**: How should authorization be enforced? What HTTP status codes should be returned?

**Decision**:
- **HTTP 404** ("Not Found"): Return for both non-existent accounts and accounts owned by other customers. This prevents account enumeration attacks (security).
- **HTTP 401** ("Unauthorized"): Return if the customer is not authenticated.
- **HTTP 200** ("OK"): Return successful mini statement responses, including those with zero transactions.

**Rationale**:
- HTTP 404 for both cases prevents attackers from discovering which accounts exist in the system.
- This aligns with the clarification from `/speckit-clarify` (Question 1, Answer A).
- Consistent with REST conventions for resource not found.

**Alternatives considered**:
- HTTP 403 for access denied: Rejected because it leaks information about account existence.
- HTTP 400 for invalid input: Not applicable; account number is a path parameter.

**Implementation note**: The route handler must check account ownership before querying transactions. If not owned, return 404.

## Dependencies & Integration Points

### Existing Systems Used
1. **Authentication** (Feature 002): Verify customer session/token; extract `customer_id` from authenticated context.
2. **Transaction Persistence** (Feature 001): Read from `transactions` and `accounts` tables.
3. **Account Masking** (Principle II): Use existing masking utilities to mask account numbers in responses.
4. **API Layer** (Principle IV): Add route to existing FastAPI app; follow `/api/v1` prefix.

### No New External Dependencies
- No new services, databases, or third-party APIs required.
- Existing Python stack (FastAPI, SQLAlchemy, Pydantic, pytest) is sufficient.

## Testing Strategy

### Unit Tests
- **Transaction query logic**: Mock database; verify LIMIT 10, ORDER BY DESC, filtering by account.
- **Current balance retrieval**: Mock Account model; verify correct balance returned.
- **Type classification (DEBIT/CREDIT)**: Test with from_account and to_account scenarios.
- **Account masking**: Verify `XXXX` + last 4 digits.
- **Timestamp formatting**: Verify ISO 8601 with IST offset.

### Integration Tests
- **PostgreSQL backend**: Insert accounts and transactions; fetch mini statement; validate ordering, masking, balance.
- **Authorization**: Attempt to fetch another customer's account; verify 404.
- **Empty transaction case**: Account with no transactions; verify empty array and current balance.
- **Less than 10 transactions**: Verify all returned; ordering correct.
- **More than 10 transactions**: Insert 20+ transactions; verify only 10 returned, newest first.

### API Tests
- **Happy path**: Authenticated customer fetches their own account; 200 response with correct schema.
- **Unauthorized access**: Attempt to fetch another customer's account; 404 response.
- **Unauthenticated**: No session token; 401 response.
- **Response schema validation**: Verify all fields present and correct types (Decimal amounts, ISO 8601 timestamps).
- **Performance**: Measure query time; verify <1 second per SC-001.

## Implementation Notes

- **No database migrations required**: The `transactions` and `accounts` tables already exist and contain the necessary fields.
- **Reuse existing patterns**: Follow the structure of existing routes in `apps/api/src/simple_bank/api/routes/`.
- **Pydantic schemas**: Create response schema(s) for the mini statement response.
- **Error mapping**: Use the existing error handling patterns in `error_mapping.py`.

## Summary

All technical decisions for the mini statement feature are clear and well-supported by the existing codebase. No blockers or ambiguities remain. Proceed to Phase 1: Design & Contracts.

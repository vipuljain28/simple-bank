# Research: Fund Transfer

**Date**: 2026-10-07

## Repository Findings

- The workspace contains requirements and Spec Kit artifacts, but no application source, dependency manifests, database configuration, or test suite to extend.
- The user selected Python 3.12, uv, FastAPI, PostgreSQL, and a separate service class for transfer rules.
- The constitution additionally requires a React/Vite client, `/api/v1` routes, exact monetary arithmetic, account-number masking, and automated tests for every rule.
- The active spec requires accepted-transfer idempotency, per-transfer additional verification, and atomic persistence of the accepted transaction and both balance updates.

## Decisions

### API and Web Client

**Decision**: Use a Python 3.12 FastAPI application managed by uv, with a separate React/Vite customer client. Keep the client dependent on the versioned REST API only.

**Rationale**: This follows the user's selected backend stack and the constitution's client/API boundary. FastAPI exposes the required REST contract and generates an OpenAPI description for contract validation.

**Alternatives considered**: A Node.js API or a client that accesses persistence directly. The former conflicts with the explicit stack request; the latter violates the constitution.

### Transfer Rule Service

**Decision**: Implement a distinct `TransferService` class. Keep HTTP parsing and response mapping in the FastAPI route; inject repository/session and additional-verification dependencies into the service. Put the rule evaluation and transfer orchestration behind the service's public operation so it can be unit tested without FastAPI or PostgreSQL.

**Rationale**: The user explicitly requires a separate, easy-to-unit-test service class. Dependency injection allows deterministic tests for every business rule, duplicate request, and verification result.

**Alternatives considered**: Inline validation in FastAPI endpoint functions or SQLAlchemy model hooks. Those approaches couple business rules to transport or persistence and make focused unit tests harder.

### PostgreSQL and Monetary Values

**Decision**: Use PostgreSQL, SQLAlchemy 2, psycopg 3, Python `Decimal`, and exact numeric columns. Accept amounts as decimal strings with exactly two fractional digits as required by the API contract; do not use binary floating-point.

**Rationale**: PostgreSQL transactions and row locks support atomic balance changes, transaction persistence, request-ID uniqueness, and daily-cap enforcement. Exact numeric arithmetic satisfies the constitution.

**Alternatives considered**: In-memory storage or non-transactional writes. These cannot reliably preserve the required all-or-nothing behavior across concurrent requests.

### Processing and Idempotency

**Decision**: In `TransferService`, check an existing accepted request ID for the authenticated customer before verification. If the transfer details match, return its stored response without requiring another proof or applying changes. If the ID belongs to different transfer details, return `REQUEST_ID_CONFLICT`. For a new request, verify the proof, then validate rules and write the request association, transaction, sender debit, and recipient credit in one PostgreSQL transaction. Lock the customer row for daily-limit serialization and lock account rows in a consistent order.

**Rationale**: The order supports the spec's lost-response retry flow without reusing a one-time verification proof. Row locking and unique constraints prevent concurrent requests from bypassing the cap, overspending, or creating duplicate transfers.

**Alternatives considered**: Checking idempotency after verification can reject a valid retry when the proof is one-time. Separate balance and transaction writes can leave partial results. Both conflict with the spec.

### Additional Verification

**Decision**: Depend on an injected `TransferVerifier` interface that verifies proof for the authenticated customer and exact transfer details. Use a deterministic fake verifier in unit and integration tests; connect a real identity provider through the interface when the host integration is selected.

**Rationale**: The spec requires an additional verification step for each new transfer but does not name a provider or proof protocol. An interface permits a testable service without inventing a provider-specific contract.

**Alternatives considered**: Trusting a request boolean or caller-supplied customer ID would not constitute trusted verification. Hard-coding an unspecified provider would exceed the available requirements.

### Error Mapping

**Decision**: Keep the spec's business error codes. Map malformed request/amount to HTTP 400, verification failure to 403, a request-ID conflict to 409, and other well-formed business-rule rejections to 422. Never include full account numbers in response messages or logs.

**Rationale**: This gives clients stable, distinct outcomes while preserving the specified error codes and confidentiality rule.

**Alternatives considered**: Returning HTTP 200 for all failures or exposing database exceptions. Both obscure outcome semantics and can leak internals.

## Resolved Planning Unknowns

- The backend language, version, package manager, framework, and database are explicitly selected by the user.
- The repository has no application layout; the proposed `apps/api` and `apps/web` structure is greenfield.
- No production verification provider or proof format is specified. The plan defines an adapter boundary and synthetic test verifier; production use requires a trusted host identity integration.
- Throughput, availability, recovery, and retention targets remain outside the feature scope; the plan retains the specified one-second response goal and tests concurrent financial invariants.
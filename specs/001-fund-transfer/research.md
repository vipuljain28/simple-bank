# Research: Account-Age Daily Transfer Limits

**Date**: 2026-10-14
**Feature**: [spec.md](spec.md)

## Repository Findings

- The repository already contains the FastAPI transfer route, a dependency-injected `TransferService`, SQLAlchemy persistence, PostgreSQL migrations, React/Vite UI, and unit/API/integration tests.
- The current service enforces one Rs 1,00,000 daily cap per customer. The transfer repository sums transactions by `customer_id`; the account model has no opening timestamp.
- Accepted transactions already record both `customer_id` and `from_account`, so a per-sending-account daily aggregate needs no transaction schema change.
- Account records are stored in PostgreSQL and may predate this policy. Their original opening time is not present in the current schema.
- The updated specification resolves the policy: an account younger than 30×24 hours has a Rs 50,000 cap; at or after 30×24 hours it has a Rs 1,00,000 cap. Age uses elapsed time; totals are separate per sending account and reset at IST midnight.
- The product owner selected that existing accounts should be treated as at least 30 days old, retaining the Rs 1,00,000 cap.

## Decisions

### Age Threshold

**Decision**: Compare the transfer evaluation instant with the account's time-zone-aware opening instant. Use Rs 50,000 if elapsed age is less than 30×24 hours; otherwise use Rs 1,00,000.

**Rationale**: This is the explicit product clarification and handles the exact boundary without calendar-day ambiguity.

**Alternatives considered**: Calendar-date counting was explicitly not selected.

### Daily Aggregation Scope

**Decision**: Sum accepted transfer amounts where the transaction's sending account is the account under evaluation and the transaction timestamp falls within the current IST calendar day. Apply the limit belonging to that sender account.

**Rationale**: The product owner selected separate per-sending-account limits, so another account owned by the same customer cannot consume this account's allowance.

**Alternatives considered**: One customer-wide daily aggregate was explicitly not selected.

### Existing Account Backfill

**Decision**: Add a non-null, time-zone-aware opening timestamp to accounts. Backfill existing rows to a timestamp at least 30×24 hours before the migration instant so the standard Rs 1,00,000 cap applies. New accounts receive their actual opening instant.

**Rationale**: Existing account opening dates are unavailable, and the product owner directed that legacy accounts retain the standard cap. The migration makes that explicit rather than assigning an unverifiable historical date.

**Alternatives considered**: Treating existing accounts as newly opened and restricting them to Rs 50,000 was not selected.

### Rule Ownership and Persistence

**Decision**: Keep age-based cap selection in `TransferService`. Extend the account snapshot/repository contract to provide opening time and a per-account daily total. Update the SQLAlchemy account model and add an additive migration; preserve existing transactional account locks and atomic balance/transaction writes.

**Rationale**: This reuses the established service and repository boundaries, enabling deterministic unit tests for threshold instants and PostgreSQL integration tests for transaction aggregation and concurrency.

**Alternatives considered**: Embedding the policy in HTTP handlers or aggregating client-side would split financial rule ownership and cannot safely enforce concurrent requests.

### Client Contract

**Decision**: Keep the transfer request/response shape unchanged. Replace the current fixed Rs 1,00,000 UI claim with concise guidance that explains the Rs 50,000 cap for accounts under 30×24 hours, the Rs 1,00,000 cap from that age onward, and per-sending-account aggregation. The backend remains authoritative for deciding the limit and returning rejections.

**Rationale**: The current form accepts account numbers directly and has no trusted account-age lookup. The spec does not require adding account metadata to transfer requests or introducing a lookup endpoint. Guidance can explain both cases without trusting client-provided account age.

**Alternatives considered**: Allowing the client to submit account age or a selected cap would make a financial limit caller-controlled. Adding a new account-lookup API is unnecessary to satisfy the specified transfer behavior.

## Resolved Planning Unknowns

- Backend, persistence, and client stack are established by the repository.
- Age definition, exact boundary, per-sending-account aggregation, and legacy-account treatment are clarified in the spec and product-owner decisions.
- No new external provider or API field is required.
- The existing one-second response target and atomicity/idempotency requirements remain in effect.

# Quickstart: Fund Transfer Validation

This guide describes local validation for the fund-transfer service and React client.

## Prerequisites

- Python 3.12 and uv.
- Node.js and npm for the React/Vite client.
- PostgreSQL for integration tests.
- Synthetic customer and account fixtures only; never use real customer or financial data.
- PostgreSQL migration setup must include the additive account-opening timestamp migration. Existing accounts are backfilled as at least 30×24 hours old, preserving their Rs 1,00,000 daily cap.
- Trusted host authentication and a per-transfer verification adapter must be injected into the FastAPI app. No production identity or verification provider is selected in this feature; the default app fails closed.
- Integration tests require an empty local PostgreSQL database named `simple_bank_test` and a `TEST_DATABASE_URL` environment variable. They create and drop their test tables, reject non-local hosts and other database names, and skip when the variable is unset.

## Automated Checks

From the repository root, run:

```sh
uv sync --project apps/api
uv run --project apps/api -- pytest apps/api/tests/unit apps/api/tests/api
uv run --project apps/api -- pytest apps/api/tests/integration
npm --prefix apps/web ci
npm --prefix apps/web run test
npm --prefix apps/web run build
npm --prefix apps/web run dev
```

Unit tests exercise `TransferService` with an in-memory repository and synthetic verifier; they do not need FastAPI or PostgreSQL. The PostgreSQL integration tests use synthetic accounts and fail closed unless pointed at the specifically named local test database. Do not put secrets or connection strings in tracked files.

## End-to-End Validation

1. Create synthetic fixtures for an active savings sender with sufficient balance and a different active recipient.
2. With the host authentication and verification adapters wired, submit a positive amount through the web app or `POST /api/v1/transfers` using a synthetic verification proof and a unique request ID.
3. Verify the response is visible within one second, contains a unique transaction ID, masks both account numbers, and reports `ACCEPTED`.
4. Verify the sender debit, recipient credit, and saved transaction all occur together for the same amount.
5. Repeat with one isolated failing condition for each documented code: `INVALID_AMOUNT`, `INSUFFICIENT_BALANCE`, `DAILY_LIMIT_EXCEEDED`, `SAME_ACCOUNT`, and `ACCOUNT_INACTIVE`.
6. Verify each rejection creates no transaction, returns no transaction ID, and changes neither balance.
7. Run concurrent synthetic transfers against the same customer and verify the balance and daily cap cannot be exceeded.
8. Retry an accepted request with the same request ID and transfer details; verify the original outcome is returned without another verification or balance update. Reuse the ID with changed transfer details and verify `REQUEST_ID_CONFLICT`.
9. Submit a new request with missing or invalid verification proof and verify `VERIFICATION_REQUIRED` with no transaction or balance changes.
10. Set the injected clock to just before an account reaches 30×24 hours since opening; verify that its Rs 50,000 cap applies. Advance the clock to the exact opening instant plus 30×24 hours and verify the Rs 1,00,000 cap applies.
11. Seed accepted same-day transfers from two sending accounts belonging to the same customer. Verify each account's cap uses only its own transfers, while each account's daily total resets at IST midnight.
12. Run the schema migration against synthetic pre-existing accounts and verify each receives an opening timestamp that makes the Rs 1,00,000 cap apply. Verify newly registered synthetic accounts use their actual opening instant and start under the Rs 50,000 cap.

## Expected Outcomes

- All accepted transfers preserve exact two-decimal monetary values and commit the transaction plus both balance changes together.
- All documented rule violations produce their matching API error code.
- Account numbers are masked in displayed responses and absent in full form from logs.
- The React client interacts with application services only through `/api/v1`.
- Transfer rules are covered by unit tests against `TransferService`, independently of HTTP and persistence layers.
- The age-based cap changes at exactly 30×24 hours, is enforced separately per sending account, and preserves the standard cap for legacy accounts through the migration backfill.
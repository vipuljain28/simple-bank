# Quickstart: Customer Authentication and Account Onboarding

This guide defines the local validation path for the authentication feature. PostgreSQL is used for persistent development and integration tests. A disposable in-memory SQLite mode is also available for UI smoke tests. Contact delivery remains an injected interface; the optional local email mock uses a fixed code and cannot be enabled outside schema-creating SQLite mode.

## Prerequisites

- Python 3.12 and uv.
- Node.js and npm for the React/Vite client.
- A local PostgreSQL database configured with a synthetic development URL in the local environment; do not add credentials to tracked files.
- `AUTH_CODE_PEPPER` supplied through a local secret manager or process environment; do not commit the value.
- The feature migrations applied in order: `apps/api/migrations/versions/001_transfer_schema.sql`, `apps/api/migrations/versions/002_customer_auth.sql`, then `apps/api/migrations/versions/003_auth_sessions.sql`.
- For manual email/SMS verification, configured trusted delivery providers. No production provider is selected by this feature. Tests use recording fake providers and synthetic codes.
- For disposable UI smoke tests only, set `DATABASE_URL=sqlite://`, `SQLITE_CREATE_SCHEMA=true`, and `MOCK_CONTACT_VERIFICATION=true`. The email mock accepts `1234` without sending email; it is rejected unless schema-creating SQLite mode is active. Mobile verification and password-reset delivery still require a provider.
- Replace every value in `.env.example` with reviewed synthetic placeholders before using it as local configuration; do not load it while it contains credential-like values.
- Synthetic identities and account data only. New accounts open at `Rs 0.00`; use a separately seeded synthetic funded sender when testing a successful transfer.

## Apply the Schema

In PowerShell, after setting `DATABASE_URL` to a local synthetic development database:

```powershell
psql $env:DATABASE_URL -f apps/api/migrations/versions/001_transfer_schema.sql
psql $env:DATABASE_URL -f apps/api/migrations/versions/002_customer_auth.sql
psql $env:DATABASE_URL -f apps/api/migrations/versions/003_auth_sessions.sql
```

Apply the migrations once and in order. Do not use these commands against production or an unknown database.

## Install and Validate

From the repository root:

```powershell
uv sync --project apps/api
uv run --project apps/api -- pytest apps/api/tests/unit apps/api/tests/api
$env:TEST_DATABASE_URL = "postgresql+psycopg://local-test-user:local-test-password@127.0.0.1:5432/simple_bank_test"
uv run --project apps/api -- pytest apps/api/tests/integration
npm --prefix apps/web ci
npm --prefix apps/web run test
npm --prefix apps/web run build
```

Integration tests are permitted only against an empty localhost database named `simple_bank_test`; the fixtures create/drop their own tables and use synthetic records. Do not point this variable at another database.

## Run the Local Application

In separate terminals:

```powershell
$env:DATABASE_URL = "sqlite://"
$env:SQLITE_CREATE_SCHEMA = "true"
$env:MOCK_CONTACT_VERIFICATION = "true"
$env:AUTH_CODE_PEPPER = "synthetic-local-only-pepper"
uv run --project apps/api -- uvicorn simple_bank.api.app:app --host 127.0.0.1 --port 8000
npm --prefix apps/web run dev -- --host 127.0.0.1
```

The Vite development proxy sends `/api` to the local FastAPI server. With the local mock enabled, email verification displays that code `1234` should be entered; no email is sent. SQLite is in-memory and all data is lost when the API stops. New accounts have a zero balance, and transfers remain unavailable until a trusted verification adapter is configured. Do not enable this mock outside local synthetic testing.

## End-to-End Scenarios

1. Register synthetic customer `customer-demo`, email `customer@example.test`, mobile `+919876543210`, and suffix `0000123456`. Verify one customer/profile/account is created atomically; the account number is exactly `19910000123456` and only `XXXX3456` is displayed.
2. Try a suffix with 9 digits, a non-digit, an existing account number, duplicate username, and duplicate normalized email. Verify each rejection creates no partial records; a mobile number shared with another profile is allowed.
3. Open the initial application screen while signed out and verify a clearly labeled Sign In action is visible. Verify `GET /api/v1/auth/session` returns HTTP 200 with `authenticated: false` when no session exists. Sign in with the valid synthetic username and password; verify the API sets an HttpOnly session cookie, returns a CSRF token, and exposes the authenticated transfer screen. Incorrect credentials return the same generic failure for unknown and known usernames.
4. Verify that five consecutive failed sign-ins trigger a generic 15-minute pause, after which valid credentials can succeed without support intervention.
5. Request and confirm one email or mobile challenge. In persistent mode, verify a six-digit code expires after 10 minutes, allows at most five attempts, is accepted once, and that a successful verification of either contact enables transfer eligibility. In disposable SQLite mock mode, email verification accepts the fixed code `1234`; no email is sent.
6. Verify a session stops authorizing protected operations after five minutes idle or one hour absolute lifetime. Sign-out and password reset revoke sessions immediately.
7. Request password recovery through an already verified contact. Verify responses do not reveal whether an account exists; a valid reset code expires after 15 minutes, allows at most five attempts, changes the password, revokes sessions, and does not automatically sign the customer in.
8. Choose a protected transfer action while signed out and verify sign-in appears before any transfer submission. A direct `POST /api/v1/transfers` without a session returns HTTP 401. Sign in, then verify an unverified customer receives the contact-verification-required outcome; after verifying either contact, verify the request is evaluated under the session customer rather than a request-supplied customer ID.
9. With a synthetic active savings sender owned by that customer and a different active recipient present in PostgreSQL, submit a valid transfer. Confirm existing transfer rules still determine the result and that sender ownership, recipient existence/status, and all balance/transaction changes are checked through the existing transfer service and repository.
10. Confirm logs, responses, and the browser never expose a password, raw session/verification/reset token, or full account number. Confirm the web client calls only `/api/v1`.

## Expected Outcomes

- No protected action accepts an unauthenticated or request-supplied customer identity.
- A valid session resolves to the matching customer and expires on the specified idle/absolute limits.
- Registration creates the profile and initial zero-balance savings account together or creates neither.
- The account number remains a 14-digit text identifier, including the complete 10-digit suffix and any leading zeroes.
- Contact verification, password recovery, and login cooldowns are one-time/expiring or temporary as specified, with generic safe errors.
- Browser state-changing requests pass same-origin and CSRF checks; expected anonymous session discovery does not produce HTTP 401.
- Existing transfer rules and all-or-nothing financial updates remain owned by `TransferService` and its PostgreSQL repository.
- KYC/document verification and production regulatory compliance remain outside this feature until project owners define them.

## Verified in This Workspace

On 2026-10-13, the Python unit/API suites passed 68 tests, the frontend suite passed 13 tests, and the production frontend build succeeded. All 22 PostgreSQL integration tests collect successfully but were not executed because a sanitized, authenticated local `simple_bank_test` database is not available. Do not use an unknown or production database for these tests.

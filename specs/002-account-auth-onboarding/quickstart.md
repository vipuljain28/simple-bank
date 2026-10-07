# Quickstart: Customer Authentication and Account Onboarding

This guide defines the local validation path for the planned authentication feature. Registration, sign-in, and transfers require PostgreSQL. Contact delivery remains an injected interface; automated tests use synthetic fake providers.

## Prerequisites

- Python 3.12 and uv.
- Node.js and npm for the React/Vite client.
- A local PostgreSQL database configured with a synthetic development URL in the local environment; do not add credentials to tracked files.
- The feature migrations applied in order: `apps/api/migrations/versions/001_transfer_schema.sql`, then `apps/api/migrations/versions/002_customer_auth.sql`.
- For manual email/SMS verification, configured trusted delivery providers. No production provider is selected by this feature. Tests use recording fake providers and synthetic codes.
- Synthetic identities and account data only. New accounts open at `Rs 0.00`; use a separately seeded synthetic funded sender when testing a successful transfer.

## Apply the Schema

In PowerShell, after setting `DATABASE_URL` to a local synthetic development database:

```powershell
psql $env:DATABASE_URL -f apps/api/migrations/versions/001_transfer_schema.sql
psql $env:DATABASE_URL -f apps/api/migrations/versions/002_customer_auth.sql
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
uv run --project apps/api -- uvicorn simple_bank.api.app:app --host 127.0.0.1 --port 8000
npm --prefix apps/web run dev -- --host 127.0.0.1
```

The Vite development proxy sends `/api` to the local FastAPI server. Set the local database URL and delivery-provider adapters before expecting registration or sign-in to succeed. If required production configuration is absent, the API must fail closed rather than accept a client-supplied customer identity.

## End-to-End Scenarios

1. Register synthetic customer `customer-demo`, email `customer@example.test`, mobile `+919876543210`, and suffix `0000123456`. Verify one customer/profile/account is created atomically; the account number is exactly `19910000123456` and only `XXXX3456` is displayed.
2. Try a suffix with 9 digits, a non-digit, an existing account number, duplicate username, and duplicate normalized email. Verify each rejection creates no partial records; a mobile number shared with another profile is allowed.
3. Verify `GET /api/v1/auth/session` returns HTTP 200 with `authenticated: false` when no session exists. Sign in with the valid synthetic username and password; verify the API sets an HttpOnly session cookie and returns a CSRF token. Incorrect credentials return the same generic failure for unknown and known usernames.
4. Verify that five consecutive failed sign-ins trigger a generic 15-minute pause, after which valid credentials can succeed without support intervention.
5. Request and confirm one email or mobile challenge. Verify a six-digit code expires after 10 minutes, allows at most five attempts, is accepted once, and that a successful verification of either contact enables transfer eligibility.
6. Verify a session stops authorizing protected operations after five minutes idle or one hour absolute lifetime. Sign-out and password reset revoke sessions immediately.
7. Request password recovery through an already verified contact. Verify responses do not reveal whether an account exists; a valid reset code expires after 15 minutes, allows at most five attempts, changes the password, revokes sessions, and does not automatically sign the customer in.
8. Submit `POST /api/v1/transfers` without a session and verify HTTP 401. Sign in, then verify an unverified customer receives the contact-verification-required outcome; after verifying either contact, verify the request is evaluated under the session customer rather than a request-supplied customer ID.
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

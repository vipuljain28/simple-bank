# Simple Bank

Simple Bank is a fund-transfer application with a FastAPI service and a React/Vite
client. It transfers funds from a customer's savings account to another active
Simple Bank account.

Customer registration and username/password authentication are implemented under
`specs/002-account-auth-onboarding/`. Registration creates a new zero-balance
savings account; verifying either email or mobile is required before transfers.

## Fund Transfer Requirements

- The transfer amount must be greater than Rs 0.
- The sender must have enough balance to cover the transfer.
- A customer may transfer no more than Rs 1,00,000 per day.
- The sender and recipient accounts must be different.
- Both accounts must be active.
- Each transfer must be saved with a unique transaction ID.
- The customer should receive a quick response.

See [docs/requirement-fund-transfer.md](docs/requirement-fund-transfer.md) for the
source requirement.

## Development Checks

```sh
uv sync --project apps/api
uv run --project apps/api -- pytest apps/api/tests/unit apps/api/tests/api
npm --prefix apps/web ci
npm --prefix apps/web run test
npm --prefix apps/web run build
```

PostgreSQL integration tests run only against an empty localhost database named
`simple_bank_test`, configured with `TEST_DATABASE_URL`. See
[`specs/001-fund-transfer/quickstart.md`](specs/001-fund-transfer/quickstart.md)
for transfer integration scenarios and
[`specs/002-account-auth-onboarding/quickstart.md`](specs/002-account-auth-onboarding/quickstart.md)
for auth setup and scenarios.

When `DATABASE_URL` is configured, the API wires a database-backed customer
session provider and auth service. Without it, protected actions fail closed.
Set `AUTH_CODE_PEPPER` through a secret manager or local process environment;
never commit its value. Email/SMS delivery and the production transfer-verification
provider are not selected; contact verification and transfer acceptance fail
closed until trusted adapters are configured. The Vite client proxies `/api` to
`http://127.0.0.1:8000` during local development. Do not use `.env.example` as
configuration until all of its values have been reviewed and replaced with
synthetic placeholders.

## Development ECS Deployment

The API's dev-only ECS Fargate setup, including its in-memory SQLite limitations
and GitHub Actions OIDC configuration, is documented in
[`docs/aws-ecs-dev.md`](docs/aws-ecs-dev.md). It is not a production deployment.

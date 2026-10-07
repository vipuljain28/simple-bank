# Simple Bank

Simple Bank is a fund-transfer application with a FastAPI service and a React/Vite
client. It transfers funds from a customer's savings account to another active
Simple Bank account.

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
for integration scenarios and expected outcomes.

The default API app intentionally fails closed. A host must supply a trusted
`CustomerContextProvider`, a `TransferVerifier`, and a configured transfer
service; production identity and verification providers are not selected here.
The Vite client proxies `/api` to `http://127.0.0.1:8000` during local development.

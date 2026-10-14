# Implementation Plan: Customer Authentication and Account Onboarding

**Branch**: `002-account-auth-onboarding` | **Date**: 2026-10-07 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/002-account-auth-onboarding/spec.md`

## Summary

Add registration, username/password sign-in, contact verification, recoverable sessions, password reset, and database-backed account validation. Implement authentication in a dependency-injected `CustomerAuthService`; resolve browser sessions through the existing `CustomerContextProvider` boundary. Keep transfer financial rules in the existing `TransferService`. The React/Vite client uses only `/api/v1`.

## Technical Context

**Language/Version**: Python 3.12 for the API; TypeScript for the React/Vite client

**Primary Dependencies**: uv, FastAPI, Pydantic, SQLAlchemy 2, psycopg 3, pytest, pytest-cov; React, Vite, Vitest, and `@vitest/coverage-v8`; add an Argon2id password-hashing library. Email/SMS delivery is behind injected provider interfaces; no production provider is selected.

**Storage**: PostgreSQL; additive migration for customer profiles, sessions, verification/reset challenges, and login throttling. Account identifiers remain text so leading zeroes are preserved.

**Testing**: pytest unit and API tests, PostgreSQL integration tests, and Vitest/Testing Library client tests. Authentication services use fake repositories and delivery providers for deterministic tests.

**Target Platform**: Python 3.12 API and modern browsers; same-origin browser requests through the `/api/v1` boundary

**Project Type**: Web application with Python API and React/Vite client

**Performance Goals**: No authentication-specific latency, throughput, or availability target is specified. The existing transfer outcome target remains one second under FR-008 of the fund-transfer spec.

**Constraints**: Account number is `1991` plus exactly 10 digits and is stored as text; email and username are unique while mobile may be shared; either verified contact enables transfers; sessions expire after 5 minutes idle or 1 hour absolute; five consecutive failed sign-ins trigger a 15-minute pause; passwords are non-reversible; account and customer creation is atomic; all routes use `/api/v1`; the web client uses only that API. Contact-delivery provider and production KYC policy are not specified and are not fabricated by this plan.

**Scale/Scope**: Initial Simple Bank registration and authentication flows only. Customer volume and deployment topology are unspecified. Registration opens one savings account with a zero balance; funding and regulatory onboarding are outside the defined feature scope.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Plan response |
|-----------|------|---------------|
| Exact monetary arithmetic | Monetary values use exact decimals with two places and have automated coverage. | Pass: initial account balance is exact `Decimal("0.00")` persisted as `NUMERIC(14, 2)`; account numbers are text, never numeric values. |
| Account data confidentiality | Full account numbers and credentials are absent from logs and unmasked customer output. | Pass: account identifiers are masked as `XXXX` plus the last four digits; passwords, session tokens, and verification/reset tokens are redacted and never returned. |
| Every rule has a test | Each constitutional and product rule has automated coverage. | Pass: each registration, authentication, session, verification, recovery, account-validation, and rejection rule receives unit/API/integration or client coverage. |
| Versioned API contract | All application routes begin with `/api/v1`. | Pass: auth routes use `/api/v1/auth/...`; transfers remain `/api/v1/transfers`. |
| React web client uses the API | Browser code communicates with application services only through the versioned API. | Pass: registration, sign-in, contact verification, recovery, session status, and transfers use the same-origin `/api/v1` client. |

**Gate Result**: PASS. Production use still requires approved email/SMS delivery and applicable KYC/compliance requirements; those are deployment prerequisites, not invented product rules.

**Post-Design Constitution Re-check**: PASS. The design keeps account numbers as text and balances exact-decimal, preserves account masking, uses `/api/v1` for all routes, keeps the React client behind the API, and provides automated coverage points for each rule. Authentication is resolved through trusted server-side sessions, not caller-supplied identity. No financial rules are weakened.

## Project Structure

### Documentation (this feature)

```text
specs/002-account-auth-onboarding/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── contracts/
│   └── auth-api.md      # Registration and authentication contract
├── quickstart.md        # Phase 1 output (/speckit-plan command)
└── tasks.md             # Generated later by /speckit-tasks
```

### Source Code (repository root)

```text
apps/
├── api/
│   ├── migrations/versions/001_transfer_schema.sql  # Existing base account/transfer schema
│   ├── migrations/versions/002_customer_auth.sql
│   ├── migrations/versions/003_auth_sessions.sql
│   ├── src/simple_bank/
│   │   ├── api/routes/auth.py
│   │   ├── api/routes/transfers.py                 # Existing route; add verification eligibility
│   │   ├── api/schemas/auth.py
│   │   ├── persistence/models/customer_profile.py
│   │   ├── persistence/models/auth_session.py
│   │   ├── persistence/models/auth_challenge.py
│   │   ├── persistence/models/login_throttle.py
│   │   ├── persistence/auth_repository.py
│   │   ├── security/context.py                     # Existing provider boundary; add DB session provider
│   │   ├── security/passwords.py
│   │   ├── security/contact_delivery.py
│   │   └── services/auth_service.py
│   └── tests/
│       ├── unit/test_auth_service.py
│       ├── api/test_auth_routes.py
│       └── integration/test_customer_registration.py
└── web/
  ├── src/App.tsx                                  # Public sign-in/registration entry and authenticated transfer view
  ├── src/features/auth/
  │   ├── RegistrationForm.tsx
  │   ├── SignInForm.tsx
  │   ├── ContactVerification.tsx
  │   └── PasswordResetForm.tsx
  ├── src/lib/api/auth.ts
  └── tests/auth/
```

**Structure Decision**: Extend the current `apps/api` and `apps/web` projects. Keep authentication orchestration in `CustomerAuthService`, credential/session/contact-delivery concerns behind injected interfaces, and transfer rules in `TransferService`. A database-backed `CustomerContextProvider` resolves the opaque session cookie to the trusted customer identity. Registration persists a `Customer`, `CustomerProfile`, and initial `Account` in one transaction. The browser never accesses PostgreSQL directly.

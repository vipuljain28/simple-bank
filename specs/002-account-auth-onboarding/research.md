# Research: Customer Authentication and Account Onboarding

**Date**: 2026-10-07

## Repository Findings

- The selected stack is Python 3.12, uv, FastAPI, PostgreSQL, SQLAlchemy 2, psycopg 3, and a React/Vite client.
- The current `create_app()` leaves both `transfer_service` and `customer_context_provider` unset. `get_authenticated_customer()` therefore returns HTTP 401 for every protected transfer request. This is the direct cause of the current unauthenticated behavior.
- The current `Customer` table contains only `customer_id`; account and transaction records already reference it. The existing `CustomerContextProvider` protocol is the seam for session-based identity.
- The transfer route is already thin and delegates financial rules to `TransferService`. That boundary will remain unchanged for balance, limit, and transfer-account rules.
- The current web app already calls `/api/v1/transfers` and uses a Vite same-origin `/api` proxy. Authentication UI and session-aware API calls are not yet present.

## Decisions

### Authentication Composition

**Decision**: Add `CustomerAuthService` and a PostgreSQL-backed `CustomerContextProvider`. Wire the provider into the FastAPI application during app composition from explicit dependencies and local settings; continue to fail closed when required configuration is absent.

**Rationale**: It fixes the actual 401 cause without weakening authorization or accepting a customer ID from the request. Existing transfer code continues to receive a trusted customer context through its current dependency boundary.

**Alternatives considered**: Trusting a body/header customer ID is forgeable. Leaving the provider unset preserves the current 401 for all protected requests. Moving financial rules into the auth route would violate the existing service boundary.

### Password Storage

**Decision**: Hash passwords with Argon2id through a maintained password-hashing library (`argon2-cffi`). Store only the password hash and parameters; verify through the library's constant-time verification API.

**Rationale**: A memory-hard password hash limits offline guessing if credential storage is exposed. It satisfies the spec's non-reversible storage requirement without custom cryptography.

**Alternatives considered**: Plaintext or reversible encryption is prohibited. Hand-built hashes and fast general-purpose hashes are not suitable for password storage.

**Input policy**: Accept passphrases from 12 through 128 characters without requiring a particular mix of character classes. Normalize usernames and email addresses for case-insensitive uniqueness; do not normalize passwords.

### Browser Sessions

**Decision**: Issue a cryptographically random opaque session token after successful sign-in. Store only its digest in PostgreSQL and put the raw token in an `HttpOnly`, `SameSite=Lax`, `Secure`-in-production cookie. Validate expiry and update last activity through the database-backed customer-context provider. Enforce the specified 5-minute idle timeout and 1-hour absolute lifetime. Revoke sessions on logout and password reset.

**Rationale**: Server-side state allows immediate revocation and enforces both idle and absolute expiry. An opaque cookie avoids exposing identity or relying on client-side token storage.

**Alternatives considered**: Browser local storage exposes bearer credentials to script injection. Self-contained tokens are harder to revoke immediately after logout or password reset. Permanent sessions conflict with the clarified expiry policy.

**CSRF protection**: Validate the request origin for browser state-changing requests. Issue a readable CSRF cookie/token pair from the session-status route, and require the matching token in a request header when a browser sends cookies. The client keeps the returned CSRF token in memory; the session credential remains in the HttpOnly cookie. Do not enable permissive cross-origin credentials.

### Contact Verification and Delivery

**Decision**: Let a customer select either email or mobile for ownership verification. Create a one-time, expiring challenge bound to that customer and channel; persist only a digest, consume it once, and mark the corresponding verification timestamp. Provide separate injected email and SMS delivery interfaces. Tests use recording fake providers.

**Rationale**: It implements the user's clarified either-contact rule, supports shared mobile numbers, prevents replay, and keeps the application independent of a vendor that was not selected.

**Alternatives considered**: Requiring both contacts contradicts the clarified rule. Trusting format validation alone does not prove control. Hard-coding a real messaging provider would invent a dependency and require credentials not specified in the project.

**Challenge defaults**: Use a six-digit numeric code, expire contact-verification codes after 10 minutes, and allow at most five confirmation attempts per challenge. Password-reset codes expire after 15 minutes, allow at most five attempts, and are single-use. Store only a digest of each code. Normalize mobile input to a validated E.164 text representation after parsing the supplied country code; do not treat a mobile number as an integer.

**Operational constraint**: Production registration, contact verification, and password recovery cannot complete until trusted email/SMS providers are configured. The application must fail closed when delivery is unavailable. A synthetic provider is test-only and must never expose verification codes in production responses or logs.

### Registration and Account Number

**Decision**: In one PostgreSQL transaction, create the customer identity, profile, and initial `SAVINGS` account with a zero exact-decimal balance. Build the account number as the fixed text prefix `1991` plus the submitted 10 ASCII digits. Enforce username, normalized email, and full account-number uniqueness in the database as well as application validation. Mobile numbers are not unique.

**Rationale**: A unique constraint is the final protection against concurrent duplicate selections; a transaction prevents partial customer/account creation. Text storage preserves a suffix's leading zeroes.

**Alternatives considered**: Converting account identifiers to integers loses leading zeroes. A pre-insert availability check without a database constraint is race-prone. Creating the account separately from the profile can leave partial records.

### Account and Transfer Authorization

**Decision**: Resolve sender and recipient through the existing account repository before financial mutation. Require the sender to be owned by the session customer, active, and savings; require a different active recipient. Require at least one verified contact before allowing a transfer. Return generic authorization/unavailable outcomes that do not expose account ownership or existence.

**Rationale**: Input shape is not proof of account existence. The current `TransferService` and PostgreSQL unit of work already own financial invariants and should remain the only path to balance updates.

**Alternatives considered**: Accepting arbitrary well-formed account numbers or returning different ownership/existence messages leaks information and violates the feature rules.

### Password Recovery and Failed Sign-In Attempts

**Decision**: Send a single-use, expiring reset challenge only to a contact already verified for that customer. A successful reset updates the password hash and revokes all sessions without automatically signing the customer in. Track consecutive failed attempts by normalized username; pause sign-in for 15 minutes after five failures, return generic failure text, and clear the throttle after cooldown or successful sign-in.

**Rationale**: These decisions implement FR-014 and FR-015, avoid unverified-channel recovery, and prevent a permanent customer lockout.

**Alternatives considered**: Resetting through an unverified address or silently creating a session after reset weakens account recovery. Permanent lockout permits an attacker to deny service to a known customer.

## Resolved Planning Unknowns

- Backend/client stack and the authentication method (username/password) are selected by the user.
- Session lifetime, failed-login cooldown, contact uniqueness, recovery channel policy, and either-contact verification rule are specified in the clarified feature spec.
- The specific production email/SMS provider, credentials, and delivery configuration are not selected; the design uses interfaces and synthetic test fakes. Production operation requires a trusted configured provider.
- The feature spec does not supply KYC, regulatory, availability, throughput, or authentication-latency requirements. This plan does not invent them; obtain applicable requirements before production deployment.

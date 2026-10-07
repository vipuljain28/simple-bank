# Data Model: Customer Authentication and Account Onboarding

## Customer

The existing bank customer identity remains the parent of profiles and financial accounts.

| Field | Type | Rules |
|---|---|---|
| `customer_id` | Opaque string identifier | Primary key; derived from trusted server state, never accepted as registration or transfer identity from the browser. |

Relationships:
- One customer has one profile for this login flow.
- One customer may own one or more accounts.
- One customer may have multiple active browser sessions.

## CustomerProfile

New one-to-one customer profile and credential record. It extends the logical Customer entity without changing the existing customer identifier used by transactions.

| Field | Type | Rules |
|---|---|---|
| `customer_id` | Opaque identifier | Primary key and foreign key to `customers.customer_id`. |
| `name` | Text | Required; display-safe customer name. |
| `email` | Text | Required; normalized for comparison and uniquely assigned to one customer. |
| `mobile_number` | Text | Required; store a validated E.164 representation; may be shared by multiple customers. |
| `username` | Text | Required; normalized for comparison and uniquely assigned to one customer. |
| `password_hash` | Encoded password-hash string | Required; non-reversible Argon2id hash for a 12-128 character passphrase; never return or log. |
| `email_verified_at` | Time-zone-aware timestamp, nullable | Set only after the customer proves control of the email contact. |
| `mobile_verified_at` | Time-zone-aware timestamp, nullable | Set only after the customer proves control of the mobile contact. |
| `created_at` | Time-zone-aware timestamp | Set by the service when registration commits. |

Invariants:
- Username and normalized email have unique database constraints; mobile number has no uniqueness constraint.
- Registration creates a customer, profile, and initial account atomically.
- A customer is transfer-eligible by contact policy when either verification timestamp is present.
- The customer ID remains the value used by account ownership and existing transaction records.

## Account

The existing account model is reused. Registration provisions one new savings account with zero balance.

| Field | Type | Rules |
|---|---|---|
| `account_number` | Text identifier | Primary key; new numbers are exactly `1991` plus the 10-digit suffix; unique; retain leading zeroes. |
| `customer_id` | Opaque identifier | Foreign key to the owning customer. |
| `balance` | Exact decimal | `NUMERIC(14, 2)`; new account opens at `Decimal("0.00")`; never use binary floating point. |
| `status` | Enum | New account is `ACTIVE`; transfer requirements still check both accounts' status. |
| `account_type` | Enum/text | New account is `SAVINGS`; sender eligibility continues to be enforced by `TransferService`. |

Invariants:
- Suffix validation accepts exactly 10 ASCII digits and preserves leading zeroes.
- Application availability checks improve feedback; the primary-key/unique constraint is authoritative during concurrent registration.
- Existing account numbers and account ownership are not rewritten or claimed by new registration.
- An existing account's full number is not returned to the browser; display uses `XXXX` plus the last four digits.

## AuthSession

Revocable server-side session for an authenticated customer.

| Field | Type | Rules |
|---|---|---|
| `session_id` | UUID/string | Primary key. |
| `customer_id` | Opaque identifier | Foreign key to the authenticated customer. |
| `token_digest` | Fixed-length digest | Unique; store only a digest of the random session token, never the raw cookie value. |
| `created_at` | Time-zone-aware timestamp | Establishes the absolute 1-hour session limit. |
| `last_activity_at` | Time-zone-aware timestamp | Establishes the 5-minute inactivity limit. |
| `revoked_at` | Time-zone-aware timestamp, nullable | Set on logout/password reset, or delete the row as the repository's revocation strategy. |

Invariants:
- Session is valid only when not revoked, `now - last_activity_at < 5 minutes`, and `now - created_at < 1 hour`.
- Logout and successful password reset invalidate all applicable sessions immediately.
- Cookie attributes are `HttpOnly`, `SameSite=Lax`, `Secure` in production, and scoped to the application path. State-changing requests also require a matching CSRF cookie/header pair and same-origin validation.
- The customer context provider resolves identity from the validated session; request-supplied customer IDs are ignored.

## ContactVerificationChallenge

One-time challenge proving control of either an email address or a mobile number.

| Field | Type | Rules |
|---|---|---|
| `challenge_id` | UUID/string | Primary key. |
| `customer_id` | Opaque identifier | Foreign key to the customer profile being verified. |
| `channel` | Enum | `EMAIL` or `MOBILE`; one verified channel is sufficient for transfer eligibility. |
| `token_digest` | Fixed-length digest | Store only the digest of the one-time challenge. |
| `created_at` / `expires_at` | Time-zone-aware timestamps | Expires 10 minutes after creation. |
| `attempt_count` | Integer | No more than five failed confirmations; consumed or expired challenge cannot be reused. |
| `consumed_at` | Time-zone-aware timestamp, nullable | Set once on successful verification. |

Invariants:
- Challenge is bound to one customer and one channel; a shared mobile number does not transfer ownership between customer profiles.
- Delivery is through injected email/SMS interfaces. Missing production delivery configuration fails closed.
- Verification sets the corresponding profile timestamp and never changes account balances.

## PasswordResetChallenge

One-time credential recovery challenge delivered only through a previously verified contact.

| Field | Type | Rules |
|---|---|---|
| `challenge_id` | UUID/string | Primary key. |
| `customer_id` | Opaque identifier | Foreign key to the customer whose password may be reset. |
| `channel` | Enum | Must refer to an already verified email or mobile contact. |
| `token_digest` | Fixed-length digest | Digest only; one-time use. |
| `created_at` / `expires_at` | Time-zone-aware timestamps | Expires 15 minutes after creation. |
| `attempt_count` | Integer | No more than five failed confirmations; consumed or expired challenge cannot be reused. |
| `consumed_at` | Time-zone-aware timestamp, nullable | Set on successful reset; prevents replay. |

Invariants:
- Unknown usernames and unavailable contacts receive a generic request response.
- A successful reset replaces the password hash, consumes the challenge, revokes existing sessions, and does not establish a new session.

## LoginThrottle

Temporary sign-in cooldown state.

| Field | Type | Rules |
|---|---|---|
| `normalized_username` | Text | Primary key for the failed-attempt counter; contains no password. |
| `consecutive_failures` | Integer | Incremented for failed attempts; cleared after successful sign-in or cooldown expiry. |
| `blocked_until` | Time-zone-aware timestamp, nullable | Set for 15 minutes after five consecutive failures; expires automatically. |
| `updated_at` | Time-zone-aware timestamp | Last counter update. |

Invariants:
- Responses do not reveal whether a username exists or whether a cooldown is active.
- The cooldown is temporary and cannot permanently lock a customer account.

## Relationships and Transaction Boundaries

- `Customer` 1:1 `CustomerProfile`; `Customer` 1:N `Account`, `AuthSession`, and auth challenges.
- Registration inserts the customer, profile, and initial account in one database transaction. Any uniqueness or persistence failure rolls back all three.
- Account-number lookup and ownership checks use the existing account repository before transfer mutation.
- Authentication/contact/password-reset operations never update balances or create financial transactions.
- The existing `TransferService` remains responsible for transfer rules; the session provider supplies only trusted identity and contact-verification eligibility.

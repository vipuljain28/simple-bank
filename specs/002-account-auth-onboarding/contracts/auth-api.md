# Customer Authentication and Onboarding API Contract

## General

All routes use the `/api/v1` prefix. Customer identity is derived from a validated server-side session; clients must not submit a `customer_id` to select an identity. Responses and logs never include a password, raw session token, verification code, reset token, or full account number.

Browser sessions use an opaque `HttpOnly`, `SameSite=Lax` cookie, marked `Secure` over HTTPS. `GET /api/v1/auth/session` sets a readable CSRF cookie and returns its token for both anonymous and authenticated states. Browser state-changing requests must pass same-origin validation; requests carrying a session cookie must also send the matching CSRF token in a request header. The React client calls the API through the same-origin `/api/v1` proxy and does not store session credentials in local storage.

## Register Customer

`POST /api/v1/auth/register`

Public route. Creates a customer profile and initial savings account atomically; registration does not automatically sign the customer in.

### Request

```json
{
  "name": "Synthetic Customer",
  "email": "customer@example.test",
  "mobile_number": "+919876543210",
  "username": "customer-demo",
  "password": "a-long-synthetic-passphrase",
  "account_number_suffix": "0000123456"
}
```

| Field | Type | Required | Validation |
|---|---|---|---|
| `name` | String | Yes | Non-empty display name. |
| `email` | String | Yes | Valid address; normalized for case-insensitive uniqueness. |
| `mobile_number` | String | Yes | Valid internationally qualified mobile number in E.164 form; never parse as an integer. |
| `username` | String | Yes | Non-empty; normalized for case-insensitive uniqueness. |
| `password` | String | Yes | 12-128 characters; passphrases are allowed without character-class rules; never returned. |
| `account_number_suffix` | String | Yes | Exactly 10 ASCII digits; preserve leading zeroes. |

### Created Response

HTTP `201 Created`

```json
{
  "customer_id": "cust_demo_001",
  "account_number": "XXXX3456",
  "account_type": "SAVINGS",
  "status": "ACTIVE",
  "transfer_eligible": false
}
```

The complete account number is `1991` plus the submitted suffix and is never returned unmasked. The new account balance is `0.00`. The customer must sign in separately. Either email or mobile ownership verification enables transfers.

If a unique username, email, or account number conflicts, return HTTP `409` with a safe field-level error that does not include the existing customer's profile or full account number. Failed registration creates no partial customer, profile, or account records.

## Sign In

`POST /api/v1/auth/login`

### Request

```json
{
  "username": "customer-demo",
  "password": "a-long-synthetic-passphrase"
}
```

Correct credentials return HTTP `200`, set the session cookie, and include the CSRF token for subsequent state-changing requests. Invalid or unknown credentials return the same generic HTTP `401` response. After five consecutive failed attempts for a username, further sign-in is paused for 15 minutes and returns a generic HTTP `429` response with `Retry-After`; the account is not permanently locked.

## Session Status

`GET /api/v1/auth/session`

This public discovery route returns HTTP `200` for both states so an anonymous browser can render sign-in without treating expected anonymity as a failed API call.

Anonymous response:

```json
{"authenticated": false, "csrf_token": "synthetic-csrf-token"}
```

Authenticated response includes `authenticated: true`, customer-safe profile fields, whether either contact has been verified, and the CSRF token. It does not include the password hash, full account number, or session cookie value.

## Sign Out

`POST /api/v1/auth/logout`

Requires a valid session and CSRF validation. Revokes the server-side session, clears the session cookie, and returns HTTP `204 No Content`. A repeated sign-out may return `204` after clearing any presented cookie.

## Request Contact Verification

`POST /api/v1/auth/contact-verification`

Requires a valid session and CSRF validation.

```json
{"channel": "email"}
```

`channel` is `email` or `mobile`. The server delivers a six-digit, one-time code to the corresponding contact associated with the signed-in customer and returns HTTP `202 Accepted` without disclosing the destination. The code expires after 10 minutes and allows at most five confirmation attempts. Delivery failure does not mark the contact verified.

## Confirm Contact Verification

`POST /api/v1/auth/contact-verification/confirm`

Requires a valid session and CSRF validation.

```json
{"channel": "mobile", "code": "synthetic-one-time-code"}
```

A valid, unexpired, unused six-digit challenge returns HTTP `200` and updated verification state. Successful verification of either channel makes the customer eligible to initiate transfers; verifying the other channel is optional. Invalid, expired, already-used, or over-attempted challenges are rejected without changing the verification state.

## Request Password Reset

`POST /api/v1/auth/password-reset/request`

Public route.

```json
{"username": "customer-demo", "channel": "email"}
```

If the profile exists and the selected contact has already been verified, the server sends a six-digit, one-time reset code that expires after 15 minutes. Regardless of account existence or delivery eligibility, return the same HTTP `202 Accepted` response so the endpoint cannot be used to enumerate customers.

## Confirm Password Reset

`POST /api/v1/auth/password-reset/confirm`

Public route.

```json
{
  "reset_code": "synthetic-reset-code",
  "new_password": "a-different-synthetic-passphrase"
}
```

A valid one-time challenge changes the password hash, consumes the challenge, revokes all sessions for the customer, clears any sign-in throttle, and returns HTTP `204 No Content`. The code expires after 15 minutes and accepts at most five attempts. It does not create a session. Invalid, expired, consumed, or over-attempted challenges do not change the password.

## Protected Transfer Integration

`POST /api/v1/transfers` remains the transfer operation. With no valid session it returns HTTP `401`; with a valid session but no verified email or mobile it returns a safe contact-verification-required response before financial mutation. A request containing a different customer ID cannot change the identity resolved from the session. The transfer service/repository still checks sender ownership, savings type, sender/recipient existence and status, and all existing financial rules. Missing/inactive account responses do not disclose account ownership or full account numbers.

## Error Response Shape

```json
{
  "error_code": "INVALID_CREDENTIALS",
  "message": "The sign-in details could not be verified."
}
```

Stable auth error codes include `INVALID_REQUEST`, `REGISTRATION_CONFLICT`, `INVALID_CREDENTIALS`, `LOGIN_TEMPORARILY_THROTTLED`, `UNAUTHENTICATED`, `CONTACT_VERIFICATION_REQUIRED`, and `INVALID_OR_EXPIRED_CHALLENGE`. Error messages never include passwords, tokens/codes, full account numbers, or another customer's profile.

# Feature Specification: Customer Authentication and Account Onboarding

**Feature Branch**: _not created_

**Created**: 2026-10-07

**Status**: Draft

**Input**: User description: "Validate account numbers against existing bank accounts; authenticate customers with username and password; provide new account creation with name, email, mobile number, and an account number formed from the fixed prefix 1991 plus a customer-selected 10-digit numeric suffix; address protected requests incorrectly returning 401 Unauthorized."

## Clarifications

### Session 2026-10-07

- Q: How should a new customer prove control of the email address and mobile number they register? → A: Verify either the email address or the mobile number; one verified contact is sufficient to enable transfers.
- Q: How long should a customer stay signed in without activity before needing to sign in again? → A: Expire sessions after 5 minutes of inactivity and after 1 hour total, whichever happens first.
- Q: If a customer forgets their password, how should they regain access to their account? → A: Allow self-service password reset through a contact method the customer has already verified.
- Q: Can the same email address or mobile number be registered on more than one customer profile? → A: Email addresses must be unique across customer profiles; mobile numbers may be shared.
- Q: What should happen after repeated failed username-and-password sign-in attempts? → A: After 5 failed attempts, pause sign-in attempts for 15 minutes and then allow retry without permanently locking the account.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Create a Customer and Savings Account (Priority: P1)

A new customer registers with their profile and login details, chooses a numeric account suffix, and receives a new savings account associated with their customer profile.

**Why this priority**: Customers need a trusted identity and an account before they can use transfers.

**Independent Test**: Submit valid synthetic registration details and verify that exactly one customer and one uniquely numbered savings account are created and can be used to sign in.

**Acceptance Scenarios**:

1. **Given** a visitor supplies valid name, email, mobile number, unique username, password, and a 10-digit suffix not already assigned, **When** they submit registration, **Then** the system creates one customer and one account whose 14-digit number begins with `1991`, associates the account with that customer, and displays only its masked form after creation.
2. **Given** a visitor supplies a suffix containing non-digits or other than 10 digits, **When** they submit registration, **Then** registration is rejected and no customer or account is partially created.
3. **Given** the selected account number, username, or email address is already assigned, **When** they submit registration, **Then** registration is rejected without creating partial records or exposing another customer's details. A mobile number already used by another customer does not by itself prevent registration.

---

### User Story 2 - Sign In and Use Protected Services (Priority: P1)

A registered customer signs in with a username and password and can use account and transfer actions as that authenticated customer.

**Why this priority**: A trusted identity must reach transfer rules; valid customers should not be rejected as anonymous.

**Independent Test**: Sign in with synthetic credentials, make a protected request, and verify it is evaluated for that customer; repeat without a valid session and verify access is denied.

**Acceptance Scenarios**:

1. **Given** a registered customer enters the correct username and password, **When** they sign in, **Then** the system establishes an authenticated session tied to that customer.
2. **Given** a customer has a valid session, **When** they use an account or transfer action, **Then** the action receives the session's trusted customer identity and is not rejected as unauthenticated.
3. **Given** a visitor has no valid session or enters incorrect credentials, **When** they sign in or call a protected action, **Then** access is denied with a safe message and no authenticated session is established.
4. **Given** a customer signs out, **When** they next request a protected action, **Then** they must authenticate again.
5. **Given** a customer cannot remember their password, **When** they prove control of a contact method already verified on their profile and set a replacement password, **Then** the password is reset, existing sessions are ended, and they must sign in with the replacement password.
6. **Given** five consecutive sign-in attempts fail for a username, **When** another sign-in is attempted during the next 15 minutes, **Then** sign-in is temporarily rate-limited with a generic response and the account is not permanently locked.

---

### User Story 3 - Use Only Existing, Authorized Accounts in a Transfer (Priority: P1)

A signed-in customer can transfer only from their own active savings account to a different active account that exists in Simple Bank.

**Why this priority**: Account-number formatting alone cannot prove that an account exists or belongs to the customer.

**Independent Test**: Submit synthetic transfer attempts using existing, missing, inactive, and differently owned account numbers; verify the service distinguishes valid requests from safe rejections and never changes state on rejection.

**Acceptance Scenarios**:

1. **Given** a signed-in customer supplies an existing active savings sender account they own and a different existing active recipient account, **When** they submit a transfer that satisfies the existing transfer rules, **Then** the request reaches transfer-rule evaluation under their authenticated identity rather than being rejected as unauthenticated.
2. **Given** a submitted sender or recipient number is malformed or does not identify a stored account, **When** the transfer is checked, **Then** it is rejected before any balance or transaction change.
3. **Given** a sender account exists but belongs to another customer or is not a savings account, **When** the signed-in customer submits a transfer from it, **Then** the request is rejected without revealing account ownership or changing account state.
4. **Given** the recipient account does not exist or is inactive, **When** a transfer is checked, **Then** the customer receives a safe account-unavailable outcome and no balance or transaction changes occur.

### Edge Cases

- The selected suffix begins with zero; it remains exactly 10 digits and is not shortened.
- The user types letters, signs, spaces, a prefix, or too few/many digits in the suffix field.
- Two registrations concurrently select the same account number; at most one succeeds.
- A username is already taken, or a password is incorrect; messages do not reveal whether unrelated customer records exist.
- Five consecutive password failures trigger a 15-minute sign-in pause; the pause ends automatically and does not require support intervention.
- An email address is already assigned to another customer; registration is rejected, but a mobile number shared with another customer is allowed.
- A customer requests password recovery using a contact method that has not been verified; the request does not change the password or establish a session.
- A valid session belongs to one customer while the submitted request attempts to name a different customer.
- A session expires after 5 minutes of inactivity or reaches its 1-hour maximum lifetime while the customer is using the application; protected actions then require sign-in again.
- A transfer references a syntactically valid but nonexistent recipient number.
- Registration fails while creating either the customer or account; neither record is left partially created.
- Existing accounts use an older number format; this feature does not silently rewrite them.

## Requirements *(mandatory)*

### Functional Requirements

1. **FR-001 - Registration details**: The system MUST provide a customer registration flow that collects name, email, mobile number, username, password, and a customer-selected account-number suffix.

   **Acceptance Criteria**: **Given** a visitor enters all required registration fields, **When** they submit registration, **Then** the system validates each field and either creates the customer and account together or returns a safe field-level rejection without partial creation.

2. **FR-002 - Customer identity uniqueness and credential privacy**: Each username and email address MUST identify no more than one customer. A mobile number MAY be associated with more than one customer. Passwords MUST be stored in a non-reversible form and MUST NOT be returned in responses or exposed in logs or operational output.

   **Acceptance Criteria**: **Given** a username or email address is already assigned, **When** another visitor attempts registration with that value, **Then** the new registration is rejected without disclosing the existing customer's profile. **Given** a mobile number is already associated with another customer, **When** a visitor registers using it and an otherwise unique username and email, **Then** mobile-number reuse alone does not reject registration. **Given** a customer registers or signs in, **When** the system handles the password, **Then** no response or log contains the password and no stored value can be used as the original password.

3. **FR-003 - Account-number format**: A newly created account number MUST consist of the fixed four-digit prefix `1991` followed by exactly 10 customer-selected digits. The complete identifier MUST contain digits only; the suffix MUST preserve all 10 digits, including leading zeroes.

   **Acceptance Criteria**: **Given** a visitor submits exactly 10 digits, **When** an account number is assigned, **Then** the full number is `1991` followed by those digits. **Given** the suffix has any other length or contains a non-digit, **When** registration is evaluated, **Then** it is rejected and no account is created.

4. **FR-004 - Account-number uniqueness**: A newly requested account number MUST be checked against existing account records and MUST NOT be assigned to more than one account.

   **Acceptance Criteria**: **Given** the complete requested number already belongs to an account, **When** registration is submitted, **Then** the number is rejected as unavailable and no second account is created. **Given** simultaneous registrations request the same number, **When** both are processed, **Then** at most one account is created with that number.

5. **FR-005 - Atomic registration**: Creating a customer and their initial account MUST succeed or fail together.

   **Acceptance Criteria**: **Given** either the customer or account cannot be created, **When** registration completes, **Then** neither record is left partially created and the visitor receives a failure outcome.

6. **FR-006 - Username and password sign-in**: The system MUST authenticate a customer using the registered username and password.

   **Acceptance Criteria**: **Given** the username and password match a registered customer, **When** the customer signs in, **Then** the system establishes an authenticated session for that customer. **Given** the credentials do not match, **When** sign-in is attempted, **Then** no session is established and a generic authentication failure is returned.

7. **FR-007 - Session lifecycle**: The customer MUST be able to end their authenticated session. A session MUST expire after 5 minutes of inactivity or 1 hour after it was established, whichever occurs first. Expired or ended sessions MUST NOT authorize protected actions.

   **Acceptance Criteria**: **Given** a customer has an active session, **When** they sign out, remain inactive for 5 minutes, or reach 1 hour since sign-in, **Then** subsequent protected actions are rejected until they sign in again.

8. **FR-008 - Trusted customer identity**: The identity used for account ownership and transfer rules MUST come from the authenticated session, not from a customer identifier supplied by the browser.

   **Acceptance Criteria**: **Given** a customer is signed in, **When** a request includes a different customer identifier, **Then** the system ignores that value and evaluates the request for the signed-in customer only.

9. **FR-009 - Database-backed account existence**: Before a transfer is evaluated, the system MUST verify that the submitted sender and recipient identifiers match existing account records; valid formatting alone MUST NOT establish account existence.

   **Acceptance Criteria**: **Given** a syntactically valid recipient identifier has no matching account record, **When** a transfer is checked, **Then** it is rejected before any transaction or balance change. **Given** both identifiers match account records, **When** the remaining transfer rules pass, **Then** account existence does not prevent the transfer.

10. **FR-010 - Sender authorization and account state**: The sender MUST belong to the authenticated customer, be an active savings account, and differ from the recipient. The recipient MUST be a different active account.

    **Acceptance Criteria**: **Given** the sender is not owned by the authenticated customer, is inactive, or is not a savings account, **When** a transfer is checked, **Then** it is rejected without disclosing another customer's data or changing balances. **Given** the recipient is missing, inactive, or the sender itself, **When** a transfer is checked, **Then** it is rejected without financial changes.

11. **FR-011 - Authenticated access to account and transfer actions**: A valid authenticated session MUST be recognized for every protected account and transfer action. Only requests without a valid session MUST receive an unauthorized outcome.

    **Acceptance Criteria**: **Given** a valid customer session, **When** that customer uses a protected account or transfer action, **Then** the request proceeds under the authenticated identity and is not rejected as unauthenticated. **Given** no valid session exists, **When** a protected action is requested, **Then** it is rejected as unauthorized before financial changes.

12. **FR-012 - Safe account-number presentation**: Full account numbers MUST NOT appear in ordinary account summaries, transfer outcomes, logs, or operational output; displayed account numbers MUST use the existing `XXXX` plus last-four-digits masking rule.

    **Acceptance Criteria**: **Given** an account number is included in a customer-facing outcome or operational output, **When** it is displayed or logged, **Then** only its masked form is present.

13. **FR-013 - Contact verification before transfer access**: A newly registered customer MUST verify ownership of either their email address or mobile number before becoming eligible to initiate transfers; verification of both is not required.

   **Acceptance Criteria**: **Given** a customer has registered but neither contact method is verified, **When** they attempt a transfer, **Then** the request is rejected safely without financial changes. **Given** the customer successfully verifies either contact method, **When** they initiate a transfer, **Then** contact verification no longer blocks the request, while all existing transfer rules still apply even if the other contact remains unverified.

14. **FR-014 - Forgotten password recovery**: A customer MUST be able to reset a forgotten password by proving control of an email address or mobile number already verified on their profile. A password reset MUST end the customer's existing sessions and MUST NOT sign them in automatically.

   **Acceptance Criteria**: **Given** a customer requests a password reset, **When** they prove control of a previously verified contact and set a replacement password, **Then** the replacement password becomes the credential, existing sessions are no longer valid, and the customer must sign in again. **Given** the customer cannot prove control of a previously verified contact, **When** they request a reset, **Then** the password remains unchanged and no session is established.

15. **FR-015 - Failed sign-in protection**: After five consecutive failed sign-in attempts for a username, the system MUST pause sign-in attempts for that username for 15 minutes. The failure response MUST remain generic, and the customer account MUST NOT be permanently locked by these failures.

   **Acceptance Criteria**: **Given** five consecutive sign-in attempts for a username have failed, **When** another attempt is made within 15 minutes, **Then** the system rejects it with a generic authentication response. **Given** the 15-minute pause has elapsed, **When** the customer submits valid credentials, **Then** sign-in can succeed without support intervention.

### Key Entities *(include if feature involves data)*

- **Customer**: A person with a unique username and email address, password credential, name, and mobile number; mobile numbers may be shared by multiple customers.
- **Account**: A Simple Bank account owned by one customer, with a unique account number, account type, status, and balance. Newly created account numbers use the `1991` prefix and a 10-digit suffix.
- **Authenticated session**: A time-limited authorization state that identifies one customer for protected account and transfer actions.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of tested account registrations with malformed suffixes or duplicate account numbers are rejected without partial customer or account records.
- **SC-002**: 100% of tested correct username/password sign-ins establish a session for the matching customer; incorrect credentials never establish a session.
- **SC-003**: 100% of tested transfer requests using a nonexistent, inactive, or unauthorized account are rejected without balance or transaction changes.
- **SC-004**: 100% of protected-action tests using a valid session reach the applicable account or transfer rules without an unauthenticated rejection; requests without valid sessions are denied.
- **SC-005**: At least 9 out of 10 representative test participants can complete registration and sign-in without assistance on their first attempt.
- **SC-006**: No tested response or operational log contains a full account number or password.
- **SC-007**: 100% of tested password resets require control of a previously verified contact, end existing sessions, and require a fresh sign-in.
- **SC-008**: 100% of tested sequences with five consecutive failed sign-in attempts pause further sign-in for 15 minutes without permanently locking the account.

## Assumptions

- Registration creates one new customer and one initial savings account; it cannot claim or take ownership of an account that already exists.
- The customer enters only the 10-digit suffix; `1991` is a fixed prefix and cannot be changed.
- The account-number format applies to newly created accounts. Existing account identifiers are checked against stored records and are not silently rewritten by this feature.
- A newly created account starts with a zero balance; funding or deposit workflows are outside this feature.
- Email and mobile values are format-validated; ownership verification of either one is sufficient before transfer access is enabled.
- Account numbers are identifiers, not monetary values; they are compared as complete digit sequences so leading zeroes are preserved.
- The existing fund-transfer limits, additional per-transfer verification, atomic balance updates, and error semantics remain governed by `specs/001-fund-transfer/spec.md`.

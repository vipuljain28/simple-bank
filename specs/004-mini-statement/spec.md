# Feature Specification: Mini Account Statement

**Feature Branch**: `004-mini-statement`

**Created**: 2026-10-14

**Status**: Draft

**Input**: User description: "Add new specification to show mini account statement"

## Clarifications

### Session 2026-10-14

- Q: When a customer attempts to view another customer's account mini statement, should the system return a "not found" error or an "access denied" error? → A: Return HTTP 404 "Not Found" for both non-existent and unauthorized accounts (prevents account enumeration attacks).
- Q: Should the mini statement response include the account's current balance in addition to the "balance after" each transaction? → A: Include current account balance in the response (separate from transaction list) for immediate visibility into financial position.
- Q: What date/time format and timezone should be used for transaction timestamps? → A: ISO 8601 format with IST timezone offset (e.g., `2026-10-14T15:30:45+05:30`) for industry-standard consistency.

## User Scenarios & Testing

### User Story 1 - View Mini Statement (Priority: P1)

A customer views the last 10 transactions from their account along with their current balance, showing transaction history in a clear, readable format with the most recent transactions first.

**Why this priority**: Viewing account transaction history and current balance is the core feature—it enables customers to monitor their account activity and understand their financial position at a glance.

**Independent Test**: A customer can fetch their account's mini statement and see the current balance and the 10 most recent transactions in newest-first order with all required details displayed.

**Acceptance Scenarios**:

1. **Given** a customer is authenticated and has an active account with transaction history, **When** they request the mini statement, **Then** they receive the current account balance and the last 10 transactions ordered newest first.
2. **Given** a customer views a mini statement, **When** they see an account number, **Then** the account number is masked (showing only the last 4 digits, e.g., `XXXX1234`).
3. **Given** a customer views their mini statement, **When** each transaction is displayed, **Then** each transaction shows the timestamp in ISO 8601 format with IST timezone (e.g., `2026-10-14T15:30:45+05:30`), description, debit/credit indicator, amount, and balance after the transaction.
4. **Given** a customer has fewer than 10 transactions, **When** they request the mini statement, **Then** all available transactions are returned along with the current balance.
5. **Given** a customer has more than 10 transactions, **When** they request the mini statement, **Then** only the 10 most recent transactions are returned along with the current balance.

### User Story 2 - Understand Transaction Direction (Priority: P1)

A customer can clearly distinguish between money coming in (credit) and money going out (debit) for each transaction.

**Why this priority**: Clear transaction direction is essential for customers to understand their account balance changes and money flow.

**Independent Test**: View transactions that include both deposits and withdrawals/transfers; verify each is clearly marked as debit or credit.

**Acceptance Scenarios**:

1. **Given** a transaction shows a debit (money going out), **When** the customer views it, **Then** it is clearly labeled as a debit.
2. **Given** a transaction shows a credit (money coming in), **When** the customer views it, **Then** it is clearly labeled as a credit.
3. **Given** a customer views a debit transaction, **When** they see the balance after, **Then** the balance is lower than before the transaction by the debit amount.
4. **Given** a customer views a credit transaction, **When** they see the balance after, **Then** the balance is higher than before the transaction by the credit amount.

### Edge Cases

- An account with no transactions returns the current balance and an empty transaction list (not an error).
- Attempting to access another customer's account returns HTTP 404 "Not Found" (security: prevents account enumeration attacks).
- Transactions are retrieved in newest-first order (most recent first); all transactions are limited to the last 10 only.
- The mini statement retrieves data for a single account; a customer cannot view mini statements across multiple accounts in one request.
- Account numbers in responses must always be masked, regardless of the customer's authentication level or account ownership.
- Transactions with zero amount are not expected (based on transfer rules), but if they exist, they are included in the statement.
- Transaction timestamps are formatted in ISO 8601 with IST timezone offset (e.g., `2026-10-14T15:30:45+05:30`) for consistency across the API.

## Requirements

### Functional Requirements

- **FR-001**: System MUST provide a mini statement endpoint at `/api/v1/accounts/{account_number}/mini-statement`.
- **FR-002**: System MUST return the last 10 transactions for the requested account, ordered newest first (most recent first), along with the current account balance.
- **FR-003**: Each transaction MUST include: ISO 8601 formatted timestamp with IST timezone (e.g., `2026-10-14T15:30:45+05:30`), description, debit/credit indicator, amount, and balance after the transaction.
- **FR-004**: The account number in the response MUST be masked, showing only the last 4 digits prefixed with `XXXX` (e.g., `XXXX1234`).
- **FR-005**: System MUST authenticate the customer before returning the mini statement.
- **FR-006**: System MUST only return mini statements for accounts owned by the authenticated customer; attempting to access another customer's account MUST return HTTP 404 "Not Found" to prevent account enumeration.
- **FR-007**: System MUST return the current balance and an empty transaction list if the account has fewer than 10 transactions (not an error).
- **FR-008**: Transaction amounts MUST use Decimal type and be rounded to two decimal places.
- **FR-009**: Transaction timestamps MUST be in ISO 8601 format with India Standard Time (IST/UTC+5:30) timezone offset.

### Key Entities

- **Account**: Identified by account number; has transaction history; owned by a customer.
- **Transaction**: A record of money movement (debit or credit); has date, description, amount, type (debit/credit), and resulting balance.
- **Customer**: Authenticated user who owns one or more accounts.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Customers can retrieve their mini statement in under 1 second from an authenticated session.
- **SC-002**: 100% of mini statements returned show account numbers masked (no full account numbers visible).
- **SC-003**: All transactions in the mini statement include complete information (ISO 8601 timestamp with IST timezone, description, debit/credit, amount, balance).
- **SC-004**: Mini statement endpoint correctly returns the last 10 transactions (or fewer if the account has fewer than 10 transactions) along with current balance.
- **SC-005**: A customer can only view mini statements for their own accounts; attempting to view another customer's mini statement returns HTTP 404 "Not Found".
- **SC-006**: 100% of transaction timestamps are in ISO 8601 format with IST timezone offset (+05:30).

## Assumptions

- The transaction history already exists in the database (populated by the Fund Transfer feature and other account operations).
- Authentication mechanism is already in place (built by Account Auth & Onboarding feature); the mini statement endpoint will use the existing session/token to identify the customer.
- "Last 10 transactions" means the 10 most recent transactions in descending order by timestamp (newest first).
- Debit transactions include transfers, withdrawals, and fees; credit transactions include deposits and transfers received.
- The minimum balance check feature (Feature 005) may affect future transaction filtering but is out of scope for this feature.
- Transaction descriptions are already stored in the database; this feature does not generate or modify transaction descriptions.
- Current balance is computed as the account's total balance as of the time of the mini statement request.
- All timestamps stored in the database use India Standard Time (IST/UTC+5:30) or will be converted to IST for API responses.
- Account enumeration attacks are a security concern; 404 responses will be used for both non-existent and unauthorized accounts.

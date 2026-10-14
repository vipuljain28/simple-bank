# Feature Specification: Fund Transfer

**Feature Branch**: _not created_

**Created**: 2026-10-06

**Status**: Draft

**Input**: User description: "Build the Fund Transfer feature described in docs/requirement-fund-transfer.md. Write user stories, a numbered list of requirements, and acceptance criteria in Given/When/Then format for every rule. If something is not clear, mark it [NEEDS CLARIFICATION]."

## Clarifications

### Session 2026-10-06

- Q: When a transfer is accepted, how should it affect the sender's and recipient's balances? → A: Debit the sender and credit the recipient together; if either update cannot complete, neither balance changes.
- Q: Should saving the accepted transfer and its unique ID succeed or fail together with both balance changes? → A: Save the record and ID with both balance changes; if any part cannot complete, none take effect.

### Session 2026-10-07

- Q: If a transfer is accepted but its response is lost, how should a repeated request avoid applying the transfer twice? → A: Require a unique request ID; a repeated ID with the same request returns the original outcome without applying the transfer again.
- Q: Must customers pass an additional verification step before each transfer, beyond being signed in? → A: Require an additional verification step for every transfer.

### Session 2026-10-14

- Q: How is the 30-day account-age boundary determined? → A: Use elapsed time from the account opening timestamp; an account receives the Rs 50,000 cap while it is less than 30×24 hours old and the Rs 1,00,000 cap at or after 30×24 hours.
- Q: How are daily limits applied when a customer has multiple accounts of different ages? → A: Apply and aggregate the daily limit per sending account; transfers from separate accounts have separate daily totals and limits.

## User Scenarios & Testing

### User Story 1 - Transfer Funds (Priority: P1)

A customer transfers money from their savings account to a different Simple Bank account and receives a confirmation when the transfer is accepted.

**Why this priority**: Initiating a valid transfer is the feature's primary customer value.

**Independent Test**: Submit one eligible transfer between two active accounts and verify that the customer receives a successful outcome and a transaction identifier.

**Acceptance Scenarios**:

1. **Given** a customer has an active savings account with sufficient funds and the recipient account is active and different, **When** the customer submits a positive amount within the daily limit, **Then** the transfer is accepted and the customer receives a confirmation.
2. **Given** a transfer has been accepted, **When** the customer views its outcome, **Then** it includes the unique transaction identifier assigned to the saved transfer.
3. **Given** the sending account was opened less than 30×24 hours ago and its accepted transfers for the current India Standard Time day total Rs 49,000, **When** the customer submits Rs 1,000, **Then** the transfer is accepted at the Rs 50,000 account-level daily cap.
4. **Given** the sending account was opened less than 30×24 hours ago and its accepted transfers for the current India Standard Time day total Rs 49,000, **When** the customer submits Rs 1,000.01, **Then** the transfer is rejected for exceeding the Rs 50,000 account-level daily cap.
5. **Given** the sending account is at least 30×24 hours old and its accepted transfers for the current India Standard Time day total Rs 99,000, **When** the customer submits Rs 1,000, **Then** the transfer is accepted at the Rs 1,00,000 account-level daily cap.
6. **Given** an account reaches 30×24 hours since opening, **When** a transfer is evaluated at or after that instant, **Then** its applicable account-level daily cap is Rs 1,00,000.

### User Story 2 - Understand a Rejected Transfer (Priority: P1)

A customer receives a clear rejection when a transfer does not satisfy a documented transfer rule.

**Why this priority**: A customer needs to understand when a transfer cannot proceed and must not mistake a rejection for a completed transfer.

**Independent Test**: Submit attempts that violate each transfer rule and verify that each attempt is rejected with an explanation of the unmet rule.

**Acceptance Scenarios**:

1. **Given** an attempted transfer violates one or more documented rules, **When** the customer submits it, **Then** the transfer is rejected and the customer is told why it cannot proceed.
2. **Given** a transfer attempt is rejected, **When** the customer receives its outcome, **Then** the outcome does not represent the attempt as a completed transfer.

### User Story 3 - Receive a Timely Outcome (Priority: P2)

A customer receives the outcome of a submitted transfer quickly enough to know whether it was accepted or rejected.

**Why this priority**: Timely feedback is explicitly required so the customer knows whether a transfer was accepted or rejected.

**Independent Test**: Measure elapsed time from submission until the customer can see an accepted or rejected outcome and compare it with the agreed target.

**Acceptance Scenarios**:

1. **Given** a customer submits a transfer, **When** an accepted or rejected outcome is available, **Then** the customer receives it within one second of submission.

### Edge Cases

- An amount of Rs 0 or less is rejected because the amount must be greater than Rs 0.
- An amount equal to the sender's available balance is permitted; an amount greater than that balance is rejected.
- For a sending account less than 30×24 hours old, a transfer that brings that account's current India Standard Time day total to exactly Rs 50,000 is permitted; one that would exceed it is rejected.
- For a sending account at least 30×24 hours old, a transfer that brings that account's current India Standard Time day total to exactly Rs 1,00,000 is permitted; one that would exceed it is rejected.
- Each sending account has its own daily total and applicable cap; transfers from other accounts owned by the same customer do not contribute to that account's daily total.
- The daily total for each account resets at midnight India Standard Time. The applicable cap changes at the exact instant the account reaches 30×24 hours since opening.
- A transfer to the sender's own account is rejected, even if that account is otherwise active.
- A transfer is rejected if either the sending or receiving account is inactive.
- If both balance changes cannot complete together, neither account balance changes and the transfer is not accepted.

## Requirements

### Functional Requirements

1. **FR-001 - Savings account transfer**: The web app MUST allow a customer to transfer money from their savings account to another Simple Bank account.

   **Acceptance Criteria**: **Given** a customer has a savings account and identifies another Simple Bank account as the recipient, **When** the customer submits a transfer, **Then** the web app evaluates the transfer under the requirements below and provides an outcome.

2. **FR-002 - Positive amount**: A transfer amount MUST be greater than Rs 0.

   **Acceptance Criteria**: **Given** a customer submits an amount of Rs 0 or less, **When** the transfer is evaluated, **Then** it is rejected because the amount is not greater than Rs 0.

3. **FR-003 - Sufficient sender balance**: The sender MUST have enough available balance to cover the transfer amount.

   **Acceptance Criteria**: **Given** the sender's available balance is less than the submitted amount, **When** the transfer is evaluated, **Then** it is rejected for insufficient balance. **Given** the sender's available balance equals or exceeds the amount, **When** the other transfer rules are satisfied, **Then** this balance rule does not prevent the transfer.

4. **FR-004 - Account-age daily limit**: A sending account opened less than 30×24 hours before transfer evaluation MUST NOT transfer more than Rs 50,000 in total during that India Standard Time day. A sending account opened at least 30×24 hours before evaluation MUST NOT transfer more than Rs 1,00,000 in total during that day. Daily totals MUST be aggregated separately for each sending account from midnight to midnight India Standard Time; transfers from other accounts owned by the customer MUST NOT count toward that account's total. The applicable limit is determined by the sending account's age when the transfer is evaluated.

   **Acceptance Criteria**:
   - **Given** the sending account is less than 30×24 hours old and its accepted transfers for the India Standard Time day plus the submitted amount total exactly Rs 50,000 or less, **When** the transfer is evaluated, **Then** this daily-limit rule does not prevent it.
   - **Given** the sending account is less than 30×24 hours old and its daily total plus the submitted amount would exceed Rs 50,000, **When** the transfer is evaluated, **Then** it is rejected for exceeding the daily limit.
   - **Given** the sending account is at least 30×24 hours old and its daily total plus the submitted amount totals exactly Rs 1,00,000 or less, **When** the transfer is evaluated, **Then** this daily-limit rule does not prevent it.
   - **Given** the sending account is at least 30×24 hours old and its daily total plus the submitted amount would exceed Rs 1,00,000, **When** the transfer is evaluated, **Then** it is rejected for exceeding the daily limit.
   - **Given** the sending account's age is exactly 30×24 hours, **When** the transfer is evaluated, **Then** the Rs 1,00,000 daily cap applies.
   - **Given** a customer has more than one sending account, **When** a daily total is calculated, **Then** only accepted transfers from the specific sending account are counted.
   - **Given** India Standard Time reaches midnight, **When** the next day begins, **Then** the daily total for each sending account is calculated for the new day.

5. **FR-005 - Different recipient account**: The recipient account MUST NOT be the same account as the sender account.

   **Acceptance Criteria**: **Given** the sender and recipient account are the same account, **When** the transfer is evaluated, **Then** it is rejected. **Given** they are different accounts, **When** the other transfer rules are satisfied, **Then** this rule does not prevent the transfer.

6. **FR-006 - Active accounts**: Both the sender and recipient accounts MUST be active for a transfer to be accepted.

   **Acceptance Criteria**: **Given** either the sender account or recipient account is inactive, **When** the transfer is evaluated, **Then** it is rejected. **Given** both accounts are active, **When** the other transfer rules are satisfied, **Then** this rule does not prevent the transfer.

7. **FR-007 - Saved transfer and unique identifier**: Every accepted transfer MUST be saved and MUST receive a transaction identifier unique among accepted transfers. Saving the transfer and its identifier MUST succeed or fail together with both account balance changes. Rejected submissions MUST NOT be saved as transfers and MUST NOT receive a transfer transaction identifier.

   **Acceptance Criteria**: **Given** a transfer is accepted, **When** its outcome is provided, **Then** the transfer has been saved with a transaction identifier that is not assigned to another accepted transfer and both account balance changes have completed. **Given** any part of saving the transfer, assigning its identifier, or updating either account balance cannot complete, **When** the transfer is processed, **Then** none of those changes take effect and the transfer is not accepted. **Given** a submission is rejected by another rule, **When** its outcome is provided, **Then** it is not saved as a transfer and does not receive a transfer transaction identifier.

8. **FR-008 - Timely response**: The customer MUST receive an accepted or rejected outcome within one second of submitting a transfer.

   **Acceptance Criteria**: **Given** a customer submits a transfer, **When** an accepted or rejected outcome is available, **Then** the customer receives the outcome within one second of submission.

9. **FR-009 - All-or-nothing balance update**: An accepted transfer MUST debit the sender's account and credit the recipient's account together. If both balance changes cannot complete, neither balance MUST change and the transfer MUST NOT be accepted.

   **Acceptance Criteria**: **Given** all transfer rules are satisfied and both balance changes can complete, **When** the transfer is accepted, **Then** the sender's balance is reduced by the transfer amount and the recipient's balance is increased by the same amount. **Given** either balance change cannot complete, **When** the transfer is processed, **Then** neither account balance changes and the transfer is not accepted.

10. **FR-010 - Duplicate request protection**: Every transfer request MUST include a request ID unique to the authenticated customer. Repeating an accepted request with the same ID and same sender account, recipient account, and amount MUST return the original outcome without applying the transfer again. Reusing an ID with different transfer details MUST be rejected.

   **Acceptance Criteria**: **Given** a transfer request has been accepted, **When** the customer retries it with the same request ID and same sender account, recipient account, and amount, **Then** the original outcome is returned without additional verification, balance changes, or transaction records. **Given** a request ID has already been used with a different sender account, recipient account, or amount, **When** it is submitted again, **Then** the request is rejected with `REQUEST_ID_CONFLICT` and no balance or transaction changes occur.

11. **FR-011 - Additional transfer verification**: The customer MUST complete an additional verification step for each new transfer before it can be accepted. The verification MUST apply to the authenticated customer and the exact transfer request. A request without successful verification MUST NOT change balances or create a transaction.

   **Acceptance Criteria**: **Given** a customer submits a new transfer without successful additional verification for that request, **When** the transfer is evaluated, **Then** it is rejected with `VERIFICATION_REQUIRED` and no balances or transaction records change. **Given** the customer completes successful additional verification for the exact request, **When** all transfer rules are satisfied, **Then** the transfer can be accepted.

### Key Entities

- **Customer**: The customer initiating a transfer and subject to the daily transfer limit.
- **Account**: A Simple Bank account with a balance and an active or inactive status; a transfer has one sending account and one different receiving account.
- **Transfer**: An accepted movement of a positive amount in Rs between accounts, saved with a unique transaction identifier. A rejected submission is not saved as a transfer.

## API

### Create a Transfer

**Endpoint**: `POST /api/v1/transfers`

#### Request Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `request_id` | String | Yes | Unique request identifier for this authenticated customer and transfer details; retries must reuse the same ID. |
| `verification_proof` | Opaque value | Yes | Evidence of successful additional verification, bound to the authenticated customer and exact transfer details. |
| `from_account` | String | Yes | Sender's savings account number. It MUST belong to the customer making the request. |
| `to_account` | String | Yes | Recipient's Simple Bank account number. |
| `amount` | Decimal string | Yes | Positive amount in Rs, represented to two decimal places. |

The customer's identity MUST come from the authenticated customer context and MUST NOT be supplied as a request field.

#### Successful Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `transaction_id` | String | Unique identifier for the accepted, saved transfer. |
| `from_account` | String | Sender account number, masked as `XXXX` plus its last four digits. |
| `to_account` | String | Recipient account number, masked as `XXXX` plus its last four digits. |
| `amount` | Decimal string | Accepted transfer amount in Rs, to two decimal places. |
| `status` | String | `ACCEPTED`. |
| `created_at` | String | Creation timestamp in ISO 8601 format with a time-zone offset. |
| `request_id` | String | Identifier from the request, used to recognize a retry. |

#### Error Response Fields and Codes

Rejected requests return an `error_code` and a human-readable `message`. Rejected submissions are not saved as transactions and do not receive a `transaction_id`.

| Error code | Meaning |
|------------|---------|
| `INSUFFICIENT_BALANCE` | The sender's available balance is less than the requested amount. |
| `DAILY_LIMIT_EXCEEDED` | The requested amount would bring the sending account's India Standard Time day total above Rs 50,000 if it is less than 30×24 hours old, or above Rs 1,00,000 otherwise. |
| `SAME_ACCOUNT` | The sender and recipient account numbers identify the same account. |
| `ACCOUNT_INACTIVE` | The sender or recipient account is inactive. |
| `INVALID_AMOUNT` | The amount is missing, not a valid monetary amount, or is not greater than Rs 0. |
| `REQUEST_ID_CONFLICT` | The request ID was previously used with different request fields. |
| `VERIFICATION_REQUIRED` | Successful additional verification for this transfer request is missing or invalid. |

Error messages MUST NOT include full account numbers.

For an already accepted `request_id`, the API returns the original successful response when the authenticated customer and transfer details match; it does not require a new verification proof or repeat the transfer. Reusing that ID with different transfer details returns `REQUEST_ID_CONFLICT`.

#### Successful Response Example

```json
{
   "transaction_id": "txn_demo_001",
   "request_id": "req_demo_001",
   "from_account": "XXXX1001",
   "to_account": "XXXX2002",
   "amount": "250.00",
   "status": "ACCEPTED",
   "created_at": "2026-10-06T10:00:00+05:30"
}
```

## Data

### Account

| Field | Description |
|-------|-------------|
| `account_number` | Unique account number. When displayed, it MUST be masked as `XXXX` plus its last four digits. |
| `customer_id` | Identifier of the customer who owns the account. |
| `balance` | Account balance in Rs, rounded to two decimal places. |
| `status` | Account state: `ACTIVE` or `INACTIVE`. |
| `opened_at` | Account opening timestamp, used to determine whether the Rs 50,000 or Rs 1,00,000 daily cap applies. |

### Transaction

| Field | Description |
|-------|-------------|
| `transaction_id` | Unique identifier assigned to an accepted transfer. |
| `request_id` | Request identifier, unique per authenticated customer, used to prevent duplicate accepted transfers. |
| `from_account` | Reference to the sender's `Account.account_number`. |
| `to_account` | Reference to the recipient's `Account.account_number`. |
| `amount` | Accepted transfer amount in Rs, rounded to two decimal places. |
| `status` | `ACCEPTED`; only accepted transfers are saved as transactions. |
| `created_at` | Creation date and time in ISO 8601 format with a time-zone offset. |

## Examples

The account references below are synthetic and masked. Each case assumes verification succeeds and the listed condition is the only rule it violates.

| # | From | To | Amount (Rs) | Relevant condition | Expected result |
|---|------|----|-------------|--------------------|-----------------|
| 1 | `XXXX1001` | `XXXX2002` | `0.00` | Both accounts active; sufficient balance; daily total remains within limit. | Rejected with `INVALID_AMOUNT`; no transaction is saved. |
| 2 | `XXXX1001` | `XXXX2002` | `250.00` | Sender balance is Rs 100.00; both accounts active; daily total remains within limit. | Rejected with `INSUFFICIENT_BALANCE`; no transaction is saved. |
| 3 | `XXXX1001` | `XXXX2002` | `200.00` | Sending account is 30 days old; its transfers already total Rs 99,900.00 for the IST day; both accounts active. | Rejected with `DAILY_LIMIT_EXCEEDED`; no transaction is saved. |
| 4 | `XXXX1001` | `XXXX1001` | `10.00` | Sender account active with sufficient balance; daily total remains within limit. | Rejected with `SAME_ACCOUNT`; no transaction is saved. |
| 5 | `XXXX1001` | `XXXX2002` | `10.00` | Recipient account is inactive; sender has sufficient balance; daily total remains within limit. | Rejected with `ACCOUNT_INACTIVE`; no transaction is saved. |
| 6 | `XXXX3001` | `XXXX2002` | `1,000.00` | Sending account was opened 29×24 hours ago; its IST-day total is Rs 49,000; sufficient balance. | Accepted; the account total becomes Rs 50,000. |
| 7 | `XXXX3001` | `XXXX2002` | `1,000.01` | Sending account was opened 29×24 hours ago; its IST-day total is Rs 49,000; sufficient balance. | Rejected with `DAILY_LIMIT_EXCEEDED`; no transaction is saved. |
| 8 | `XXXX4001` | `XXXX2002` | `1,000.00` | Sending account was opened exactly 30×24 hours ago; its IST-day total is Rs 99,000; sufficient balance. | Accepted; the account total becomes Rs 1,00,000. |
| 9 | `XXXX3001` | `XXXX2002` | `1,000.00` | The customer's other sending account has already transferred Rs 50,000 today; this account's own IST-day total is Rs 49,000 and it is 29 days old. | Accepted; only this sending account's total is used. |

## Success Criteria

### Measurable Outcomes

- **SC-001**: Every tested transfer with a positive amount, sufficient sender balance, a per-sending-account daily total at or below the applicable account-age cap, two different active accounts, and valid verification is accepted.
- **SC-002**: Every tested transfer violating any one of the documented amount, balance, account-age daily-limit, account-identity, or account-status rules is rejected.
- **SC-003**: Every accepted transfer is saved with a unique transaction identifier and matching balance changes; a failed transfer leaves neither a saved transfer nor a balance change.
- **SC-004**: The customer can see an accepted or rejected outcome within one second of submission.
- **SC-005**: Customers can identify the reason for a rejected transfer from its presented outcome.
- **SC-006**: Every accepted transfer reduces the sender's balance and increases the recipient's balance by the same amount; no rejected transfer changes either balance.
- **SC-007**: Every accepted transfer has successful additional verification tied to that customer and exact request before either account balance changes.
- **SC-008**: Test cases immediately below and exactly at 30×24 hours after account opening select the Rs 50,000 and Rs 1,00,000 account-level daily caps respectively, and transfers from other accounts do not affect either account's daily total.

## Assumptions

- The customer is using the Simple Bank web app and is authorized to initiate transfers from their savings account.
- The transfer recipient is another Simple Bank account.
- Monetary amounts are expressed in Rs, as in the source requirement.
- "Per day" means accepted transfers from the same sending account are aggregated from midnight to midnight India Standard Time; another account's transfers are not included.
- Account age is elapsed time from its opening timestamp. An account is subject to the Rs 50,000 cap before 30×24 hours have elapsed and the Rs 1,00,000 cap at or after that instant.
- A response includes the accepted or rejected outcome and is presented within one second of submission.
# Feature Specification: Minimum Balance Enforcement for All Accounts

**Feature Branch**: _not created_

**Created**: 2026-10-14

**Status**: Draft

**Input**: User description: "Block withdrawal if balance goes below Rs 1,000. Savings accounts must keep a minimum balance of Rs 1,000. A withdrawal or transfer is rejected if the balance after it would be less than Rs 1,000. Error code: MIN_BALANCE_REQUIRED. The minimum balance amount must come from configuration, not hard-coded."

## Clarifications

### Session 2026-10-14

- Q: Where should the account number appear in error responses? → A: Error message should show the masked account number (XXXX1234) when referencing the account, consistent with Constitution Principle II (Account Data Confidentiality).
- Q: What is the exact configuration parameter name and location? → A: Parameter name: `MIN_BALANCE_SAVINGS` (Decimal, default: 1000.00); defined as environment variable or in `settings.py` with other configuration defaults.
- Q: Should minimum balance apply only to savings accounts or all account types? → A: Apply to ALL account types; do not filter by account type. All accounts must maintain the minimum balance threshold.

## Summary

All accounts in Simple Bank must maintain a minimum balance of Rs 1,000. Any withdrawal or transfer that would reduce an account's balance below this threshold must be rejected with error code `MIN_BALANCE_REQUIRED`. The minimum balance amount must be configurable to support future policy changes.

---

## User Scenarios & Testing

### User Story 1 - Enforce Minimum Balance on Transfer (Priority: P1)

A customer attempts to transfer funds and receives a clear rejection if the transfer would bring their account balance below Rs 1,000.

**Why this priority**: Protecting minimum balance is a core business requirement that prevents accounts from falling into overdraft.

**Independent Test**: Submit transfer attempts that would violate the minimum balance and verify each is rejected with error code `MIN_BALANCE_REQUIRED`.

**Acceptance Scenarios**:

1. **Given** a customer's account has a balance of Rs 5,000 and the minimum balance is Rs 1,000, **When** the customer submits a transfer of Rs 4,000, **Then** the transfer is accepted because the balance after (Rs 1,000) equals the minimum.
2. **Given** a customer's account has a balance of Rs 5,000 and the minimum balance is Rs 1,000, **When** the customer submits a transfer of Rs 4,001, **Then** the transfer is rejected with error code `MIN_BALANCE_REQUIRED` because the balance after (Rs 999) would fall below the minimum.
3. **Given** a customer's account has a balance of Rs 1,000 and the minimum balance is Rs 1,000, **When** the customer submits a transfer of Rs 1, **Then** the transfer is rejected with error code `MIN_BALANCE_REQUIRED` because the balance after (Rs 999) would fall below the minimum.
4. **Given** a customer's account has a balance of Rs 1,000 and the minimum balance is Rs 1,000, **When** the customer submits a transfer of Rs 0.01, **Then** the transfer is rejected with error code `MIN_BALANCE_REQUIRED` because the balance after would fall below the minimum.

### User Story 2 - Configurable Minimum Balance (Priority: P1)

The minimum balance amount must be retrieved from configuration, not hard-coded in the application, allowing policy changes without code deployment.

**Why this priority**: Banking regulations and policy decisions about minimum balance thresholds change independently of software releases. Configuration-driven defaults enable business flexibility.

**Independent Test**: Deploy the feature with different minimum balance values in configuration and verify that the enforcement threshold updates accordingly.

**Acceptance Scenarios**:

1. **Given** the minimum balance is configured as Rs 1,000, **When** a transfer would leave Rs 1,000, **Then** it is accepted.
2. **Given** the minimum balance is configured as Rs 5,000, **When** a transfer would leave Rs 4,999, **Then** it is rejected with error code `MIN_BALANCE_REQUIRED`.
3. **Given** the minimum balance configuration is updated from Rs 1,000 to Rs 2,000, **When** new transfers are evaluated, **Then** the new threshold (Rs 2,000) is applied to all subsequent transfers.

### User Story 3 - Understand Why Transfer Was Rejected (Priority: P2)

A customer receives a clear explanation when a transfer is rejected due to minimum balance enforcement, distinguishing it from other rejection reasons.

**Why this priority**: A customer needs to understand that the issue is the minimum balance policy, not technical failure or insufficient funds, and know what action to take.

**Independent Test**: Reject a transfer due to minimum balance and verify the customer receives error code `MIN_BALANCE_REQUIRED` and a user-friendly message explaining the policy.

**Acceptance Scenarios**:

1. **Given** a transfer is rejected due to the minimum balance rule, **When** the customer receives the rejection, **Then** the response includes error code `MIN_BALANCE_REQUIRED`.
2. **Given** a transfer is rejected due to the minimum balance rule, **When** the customer reads the error message, **Then** it clearly explains that the account must maintain a Rs 1,000 minimum balance.

### Edge Cases

- A balance that is exactly equal to the minimum balance (e.g., Rs 1,000) must not be reduced further; any transfer that would reduce it is rejected.
- Transfers of very small amounts (e.g., Rs 0.01) are also subject to the minimum balance rule; they cannot bring the balance below the minimum.
- The minimum balance check applies to all types of balance-reducing transactions: transfers to other accounts and (if withdrawal feature is implemented) cash withdrawals.
- Deposits and credit transactions may bring the balance above the minimum; no check is applied to credit-only transactions.
- The check is performed on the balance *after* the transaction would be applied (not before), ensuring the final balance cannot fall below the minimum.

---

## Functional Requirements

1. **Minimum Balance Validation**: Before accepting any debit transaction (transfer or withdrawal), the system must verify that the resulting balance would not fall below the configured minimum balance. This applies to ALL account types without exception.

2. **Configurable Threshold**: The minimum balance amount must be read from application configuration via the parameter `MIN_BALANCE_SAVINGS` (Decimal, default: 1000.00 rupees). This parameter must be defined as an environment variable or in `settings.py` to match existing configuration patterns.

3. **Rejection with Error Code**: If a transaction would violate the minimum balance requirement, it must be rejected with error code `MIN_BALANCE_REQUIRED`.

4. **Decimal Precision**: All balance calculations must use the `Decimal` type to ensure accuracy with monetary amounts; floating-point arithmetic must not be used.

5. **Clear Error Message with Masked Account**: When a transaction is rejected due to minimum balance enforcement, the error response must include:
   - The error code `MIN_BALANCE_REQUIRED`
   - A user-friendly message explaining that the account must maintain the minimum balance
   - The configured minimum balance amount (for clarity)
   - The masked account number (e.g., XXXX1234) showing only the last four digits, per Constitution Principle II

6. **Applicable to All Debit Transactions**: The minimum balance check must be enforced for all transaction types that reduce account balance (transfers, withdrawals, etc.), regardless of account type.

7. **Zero and Negative Amounts**: Transfers of zero or negative amounts are already rejected by other rules; the minimum balance check applies to valid positive amounts only.

---

## Success Criteria

1. **Functional Correctness**: Transfers that would reduce balance to exactly the minimum (or above) are accepted; transfers that would reduce balance below the minimum are rejected with error code `MIN_BALANCE_REQUIRED`.

2. **Configuration-Driven**: The minimum balance threshold can be changed via configuration file or environment variable without modifying application code.

3. **Clear Error Feedback**: 100% of minimum-balance violations result in rejection with error code `MIN_BALANCE_REQUIRED` and a user-comprehensible explanation message.

4. **Test Coverage**: All acceptance scenarios (including edge cases) have automated tests with passing results.

5. **Precision**: All balance calculations are accurate to the paisa (0.01 rupee) using Decimal arithmetic.

6. **Performance**: Minimum balance validation adds negligible latency (<10 ms) to transaction processing.

---

## Key Entities

### Account
- **balance**: Decimal (current account balance in rupees)
- **account_id**: String (account identifier)
- (Note: no account_type filtering; minimum balance applies to all accounts)

### Transfer (or Withdrawal)
- **from_account_id**: String (account being debited)
- **amount**: Decimal (amount in rupees)
- **balance_after**: Decimal (calculated: current_balance - amount)

### Configuration
- **MIN_BALANCE_SAVINGS**: Decimal (default: 1000.00, in rupees) — minimum balance threshold for all account types

### Error Response
- **error_code**: String (value: "MIN_BALANCE_REQUIRED")
- **message**: String (user-friendly explanation, includes masked account number per Constitution Principle II)

---

## Assumptions

1. **Decimal Type**: The application already uses Python's `Decimal` type for balance storage and calculations (verified in existing fund transfer feature).

2. **Configuration System**: The application has an existing configuration system (environment variables or `settings.py`) that can be extended; the `MIN_BALANCE_SAVINGS` parameter will be added to this system.

3. **Universal Application**: Minimum balance check applies to ALL account types without account_type filtering. No distinction is made between savings, current, or other account types.

4. **Existing Transfer Validation**: The fund transfer feature already validates transfers (sufficient balance, account status, daily limits, etc.); minimum balance check is an additional validation layer.

5. **Transaction Atomicity**: If minimum balance check passes and transfer is accepted, both balance update and transaction record save complete together or both fail (atomicity already ensured by existing transaction management).

6. **Currency**: All amounts are in Indian Rupees (INR); no currency conversion is needed.

7. **Account Number Masking**: Existing transfer error responses already mask account numbers per Constitution Principle II; the minimum balance error will follow the same masking pattern.

---

## Constraints & Dependencies

1. **Depends On**: Fund Transfer feature (001) — minimum balance check is a validation rule applied during transfer processing.

2. **Scope**: Applies to all debit transactions only; credit transactions and deposits do not check minimum balance.

3. **Account Scope**: Minimum balance applies universally to all accounts (no account type filtering); a customer with multiple accounts has the same minimum balance requirement for each account.

4. **Universal Enforcement**: The minimum balance threshold applies to all account types equally. No exceptions or account-type-specific minimums.

5. **Backward Compatibility**: Existing valid transfers (those that would have passed without this feature) must remain valid; this feature only rejects previously-accepted transfers that would fall below the new minimum.

---

## Out of Scope

- Different minimum balance thresholds for different account types (all accounts use the same `MIN_BALANCE_SAVINGS` threshold)
- Withdrawal feature (only transfers are in scope; withdrawal API may reuse this validation if implemented)
- Minimum balance grace periods or temporary exceptions
- Notifications to customers about approaching minimum balance
- Penalties or fees for violating minimum balance
- Account freezing or closing due to minimum balance violations

---

## Acceptance Criteria (Test-Driven)

- [ ] Unit tests for minimum balance validation logic (with Decimal arithmetic)
- [ ] Integration tests for transfer rejection with error code `MIN_BALANCE_REQUIRED`
- [ ] Configuration tests verifying minimum balance threshold is read from configuration
- [ ] Edge case tests: balance exactly at minimum, very small amounts, etc.
- [ ] Error message tests: verify `MIN_BALANCE_REQUIRED` code and user-friendly explanation are returned
- [ ] Performance tests: verify validation adds <10 ms latency

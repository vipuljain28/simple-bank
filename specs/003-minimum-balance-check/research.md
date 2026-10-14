# Research & Technical Validation

**Phase**: 0 - Research  
**Feature**: 003 - Minimum Balance Enforcement for All Accounts

---

## Summary

This phase validates technical assumptions and resolves any ambiguities identified in the Technical Context section of the plan. All research items were resolved during `/speckit-clarify`; no additional investigation needed.

---

## Research Findings

### 1. Account Type Scope (RESOLVED)

**Question**: Should minimum balance enforcement apply only to savings accounts, or all account types?

**Finding**: Applies to **ALL account types** universally.

**Rationale**: 
- Clarification from `/speckit-clarify` session: "Apply to ALL account types; do not filter by account type."
- Banking regulation perspective: Minimum balance is a policy applied across all account tiers in Simple Bank.
- Implementation: No account_type-specific branches in validation logic; use single formula for all.

**Decision**: Use configuration `MIN_BALANCE_SAVINGS` (despite the name including "SAVINGS") as the universal threshold for all accounts.

**Alternatives Considered**:
- Separate thresholds per account type (e.g., MIN_BALANCE_SAVINGS, MIN_BALANCE_CURRENT) — **Rejected**: adds complexity; spec requires single configurable value.
- No enforcement for checking/current accounts — **Rejected**: contradicts clarification.

---

### 2. Configuration Parameter Definition (RESOLVED)

**Question**: What is the exact parameter name, location, and data type for minimum balance configuration?

**Finding**: 
- **Name**: `MIN_BALANCE_SAVINGS` (string key)
- **Type**: Decimal with 2 decimal places (e.g., 1000.00)
- **Default**: 1000.00 (1,000 rupees)
- **Locations** (in order of precedence):
  1. Environment variable: `MIN_BALANCE_SAVINGS`
  2. Database configuration table: `configuration.key = 'MIN_BALANCE_SAVINGS'`
  3. Application default: `Decimal('1000.00')`

**Rationale**:
- Environment variable precedence allows override in deployment without database change.
- Database fallback enables runtime updates without redeployment.
- Application default ensures backward compatibility.

**Implementation**:

```python
# In settings.py or config module
from decimal import Decimal
import os

MIN_BALANCE_SAVINGS = Decimal(
    os.getenv('MIN_BALANCE_SAVINGS', '1000.00')
)
```

**Alternatives Considered**:
- Hard-coded constant — **Rejected**: spec requires configuration.
- Float type — **Rejected**: Constitution Principle I requires Decimal for all monetary values.
- Single configuration file (no environment override) — **Rejected**: reduces operational flexibility.

---

### 3. Account Number Masking in Error Responses (RESOLVED)

**Question**: Should account numbers be masked in error responses returned to users?

**Finding**: **Yes, always mask account numbers in error responses.**

**Details**:
- Format: `XXXX{last_4_digits}` (e.g., XXXX1234)
- This applies to both `message` and `details.account` fields in error response.
- Reuse existing `mask_account_number()` utility function already in codebase.

**Rationale**: 
- Constitution Principle II (Account Data Confidentiality): "Account numbers must be masked."
- Security best practice: Never expose full account number to user even in error context.
- Compliance: Aligns with PCI DSS and banking privacy standards.

**Implementation**:

```python
from simple_bank.domain.account_numbers import mask_account_number

# In transfer validation error handler
masked_account = mask_account_number(from_account.account_number)
error_message = f"Transfer rejected: insufficient balance in account {masked_account}. ..."
```

**Alternatives Considered**:
- Show full account number for verification — **Rejected**: violates Constitution and privacy principles.
- Show only UUID (not account number) — **Rejected**: less user-friendly; customers identify by account number.
- Show first 4 digits instead of last 4 — **Rejected**: last 4 is industry standard (credit cards, bank statements).

---

## Dependency Analysis

### External Dependencies

**FastAPI** (existing)
- Used for: HTTP endpoint definition, request/response serialization
- Status: Already in project; no version change needed
- Confidence: High

**Pydantic** (existing)
- Used for: Request/response validation and schema definition
- Status: Already in project; no version change needed
- Confidence: High

**SQLAlchemy** (existing)
- Used for: Database queries (fetch account balance, check transfer status)
- Status: Already in project; no version change needed
- Confidence: High

**Python Decimal** (built-in)
- Used for: Monetary arithmetic with 2 decimal place precision
- Status: Built-in standard library; no installation needed
- Confidence: High

**pytest** (existing)
- Used for: Unit and integration testing
- Status: Already in project; no version change needed
- Confidence: High

### New Dependencies

**None** — Feature uses only existing libraries.

---

## Integration Points

### 1. Transfer Service Integration

**Existing Code**: `simple_bank/services/transfer_service.py`

**Change Required**: Add validation gate before approving transfer.

**Integration Type**: Direct function call inside `process_transfer()` method.

**Complexity**: Low — validation is a single conditional check.

---

### 2. Configuration Loading

**Existing Code**: `simple_bank/settings.py` or configuration mechanism

**Change Required**: Add `MIN_BALANCE_SAVINGS` to configuration.

**Integration Type**: Read-only; no schema changes.

**Complexity**: Very Low — add 1-2 lines to settings module.

---

### 3. Account Masking

**Existing Code**: `simple_bank/domain/account_numbers.py`

**Function**: `mask_account_number(account_number: str) -> str`

**Status**: Already exists and is production-tested.

**Integration Type**: Direct import and function call.

**Complexity**: Very Low — reuse existing utility.

---

### 4. Error Response Schema

**Existing Code**: `simple_bank/api/schemas/error_schemas.py` (or similar)

**Change Required**: Extend error response schema to include `MIN_BALANCE_REQUIRED` case.

**Integration Type**: Add new error code constant and response formatter.

**Complexity**: Low — follows existing error handling pattern.

---

## Technology Recommendations

### Decimal Arithmetic

**Decision**: Use Python `Decimal` from `decimal` module.

**Why**: 
- Built-in standard library (no installation).
- Provides exact decimal arithmetic (unlike float).
- Already used in project for existing transfer logic.
- Matches Constitution Principle I.

**Example**:

```python
from decimal import Decimal

current_balance = Decimal('5000.00')
transfer_amount = Decimal('4001.00')
balance_after = current_balance - transfer_amount  # Decimal('999.00')

if balance_after < Decimal('1000.00'):
    # Reject transfer
```

---

### Configuration Storage

**Decision**: Environment variable with database fallback.

**Why**:
- Environment variable: Fast (no database query), secure (loaded at startup), deployment-friendly.
- Database fallback: Enables runtime updates without restart.
- Precedence: Env var > Database > Application default.

**Implementation**:

```python
# settings.py
import os
from decimal import Decimal

MIN_BALANCE_SAVINGS = Decimal(
    os.getenv('MIN_BALANCE_SAVINGS', '1000.00')
)

# In transfer validation:
if balance_after < settings.MIN_BALANCE_SAVINGS:
    # Reject
```

---

### Error Response Format

**Decision**: JSON with three-level structure (error_code, message, details).

**Why**:
- Matches existing error response pattern in Simple Bank.
- Provides both human-readable message and machine-readable error code.
- Details object supports detailed breakdown for frontend UI.
- JSON is standard for REST APIs.

**Example**:

```json
{
  "error_code": "MIN_BALANCE_REQUIRED",
  "message": "Transfer rejected: insufficient balance in account XXXX1234...",
  "details": {
    "account": "XXXX1234",
    "current_balance": "5000.00",
    "requested_amount": "4001.00",
    "balance_after": "999.00",
    "minimum_required": "1000.00"
  }
}
```

---

## Testing Strategy

### Unit Tests

**Focus**: Minimum balance validation logic in isolation.

**Test File**: `apps/api/tests/unit/test_minimum_balance_validation.py`

**Scenarios**:
- Balance at threshold (allowed)
- Balance below threshold (rejected)
- Exact minimum + 1 paisa (rejected)
- Decimal precision (0.01 formatted correctly)
- Configuration override (different MIN_BALANCE values)

**Tool**: pytest

---

### Integration Tests

**Focus**: Minimum balance check within transfer workflow.

**Test File**: `apps/api/tests/integration/test_minimum_balance_transfer.py`

**Scenarios**:
- E2E transfer submission → validation → rejection with 422 response
- Response schema matches contract
- Account masking in error message
- Database state unchanged after rejection

**Tool**: pytest with database fixtures

---

### API Contract Tests

**Focus**: Error response format matches contract.

**Test File**: `apps/api/tests/api/test_minimum_balance.py`

**Scenarios**:
- HTTP status 422 for MIN_BALANCE_REQUIRED
- Response JSON structure (error_code, message, details)
- All monetary amounts formatted as Decimal strings with 2 places
- Account number is masked

**Tool**: pytest with HTTP client

---

### Manual Testing

**Focus**: End-to-end validation via web UI and curl.

**Scenarios**: See `quickstart.md`.

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|-----------|
| Decimal precision lost if using float | Low | High | Use `Decimal` type throughout; add test for paisa amounts |
| Account number leaked in error response | Low | High | Reuse existing masking function; test error message |
| Configuration not loaded correctly | Low | Medium | Add unit test for MIN_BALANCE_SAVINGS loading |
| Existing transfers break after deployment | Low | Medium | Apply rule only to new transfers; no retro-active validation |
| Frontend doesn't handle 422 error | Medium | Medium | Update frontend error handling; include in acceptance tests |

---

## Timeline

**Phase 0 (Research)**: ✅ Complete (this document)

**Phase 1 (Design)**: ✅ Complete
- data-model.md
- contracts/transfer-errors.md
- quickstart.md

**Phase 2 (Tasks)**: → Next step: Run `/speckit-tasks` to generate task breakdown.

**Estimated Implementation**: 4–6 hours (including tests and code review).

---

## Conclusion

All research questions have been resolved through existing documentation and `/speckit-clarify` session. No blocking ambiguities remain. Technical approach is aligned with project architecture and constitutional principles. Ready to proceed to Phase 2: Task generation and implementation.

---

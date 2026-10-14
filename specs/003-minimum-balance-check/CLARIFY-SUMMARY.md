# ✅ Specification Clarified: Minimum Balance Enforcement (003)

## Clarification Session Summary

**Date**: 2026-10-14  
**Status**: ✅ All critical ambiguities resolved  
**Spec File**: `specs/003-minimum-balance-check/spec.md`  

---

## Key Changes from Clarifications

### Change 1: Account Type Scope (Q3)
**Original**: Minimum balance applies to savings accounts only  
**Clarified**: Applies to **ALL account types equally** (no filtering by account_type)

**Impact**:
- Simplified implementation (no account_type check needed)
- Universal policy across all customer accounts
- Removed account-type-specific business logic

**Spec Updates**:
- Title: "Minimum Balance Enforcement for **All Accounts**" (was "for Savings Accounts")
- Functional Requirement 1: Added "This applies to ALL account types without exception"
- Key Entities: Removed `account_type` field from Account entity
- Constraints: Added "Universal Enforcement" principle

---

### Change 2: Configuration Parameter (Q2)
**Original**: "configuration file or environment variable" (vague)  
**Clarified**: Parameter name: **`MIN_BALANCE_SAVINGS`**; location: **`settings.py` or environment variable**

**Impact**:
- Agents know exact parameter name to use
- Tests can mock/override this specific config
- Consistent with existing project patterns

**Spec Updates**:
- Functional Requirement 2: Specifies exact parameter name and default (1000.00)
- Key Entities: Clarified Configuration entity with parameter name and default
- Assumptions: Specified configuration location matching existing patterns

---

### Change 3: Account Masking in Errors (Q1)
**Original**: Error message unclear if account should be included  
**Clarified**: Error message **MUST include masked account number** (XXXX1234) per Constitution Principle II

**Impact**:
- Aligns with bank security policy
- Consistent with existing transfer error responses
- Prevents exposure of sensitive identifiers

**Spec Updates**:
- Functional Requirement 5: Added "masked account number (e.g., XXXX1234), per Constitution Principle II"
- Key Entities: Updated Error Response to include account masking note
- Assumptions: Added Assumption 7 about account number masking

---

## Ambiguity Coverage Analysis

| Category | Before | After | Status |
|----------|--------|-------|--------|
| Functional Scope | ✅ Clear | ✅ Clear | Resolved |
| Account Type Application | ⚠️ Partial | ✅ Clear | **Resolved** |
| Configuration Details | ⚠️ Partial | ✅ Clear | **Resolved** |
| Account Masking | ⚠️ Partial | ✅ Clear | **Resolved** |
| Error Handling | ✅ Clear | ✅ Clear | Clear |
| Data Model | ✅ Clear | ✅ Clear | Clear |
| Test Coverage | ✅ Clear | ✅ Clear | Clear |
| Non-Functional | ✅ Clear | ✅ Clear | Clear |

**Result**: All ambiguities resolved. Spec is unambiguous and ready for implementation.

---

## Quality Checklist Results

**Before Clarification**: 10/10 items passing ✅  
**After Clarification**: 10/10 items passing ✅  
**Newly Validated Items**: 
- [x] Configuration parameter names specified
- [x] Account masking requirements aligned with Constitution
- [x] Universal application to all account types confirmed

---

## Key Implementation Guidance (for Copilot Agent)

The clarifications provide the agent with:

1. **Exact Configuration**
   - Parameter: `MIN_BALANCE_SAVINGS`
   - Default: 1000.00
   - Location: settings.py or env var
   - Type: Decimal

2. **Error Response Format**
   - Code: `MIN_BALANCE_REQUIRED`
   - Message: Include minimum amount AND masked account (XXXX1234)
   - Example: "Account XXXX1234 must maintain a minimum balance of Rs 1,000"

3. **Implementation Scope**
   - No account type checking needed
   - Apply validation to ALL accounts universally
   - Simplifies validation logic

---

## Sections Modified

| Section | Change | Impact |
|---------|--------|--------|
| Title | Added "for All Accounts" | Clarity on universal scope |
| Clarifications | Added new session section | Records decisions for audit trail |
| Functional Requirement 1 | Added "ALL account types without exception" | Removes ambiguity |
| Functional Requirement 2 | Specified `MIN_BALANCE_SAVINGS` parameter | Exact config name |
| Functional Requirement 5 | Added masked account masking requirement | Aligns with Constitution |
| Key Entities | Removed `account_type` from Account | Reflects simplified validation |
| Assumptions | Added Assumption 3 & 7 | Universal application & masking |
| Constraints | Added "Universal Enforcement" | Reinforces scope |
| Out of Scope | Refined to exclude account-type-specific rules | Clarifies what's not needed |

---

## Compliance with Constitution

✅ **Principle I (Exact Monetary Arithmetic)**  
- Decimal type explicitly required
- Precision to paisa (0.01 rupee) specified

✅ **Principle II (Account Data Confidentiality)**  
- Masked account numbers in error responses
- XXXX1234 format specified

✅ **Principle III (Every Rule Has a Test)**  
- 6 test categories in acceptance criteria
- All scenarios covered by tests

✅ **Principle IV (Versioned API Contract)**  
- Error codes are part of `/api/v1` contract
- `MIN_BALANCE_REQUIRED` code documented

✅ **Principle V (React Web Client Uses the API)**  
- Error responses flow through API
- Client consumes via standard error handling

---

## Next Steps

### Immediate
✅ **Clarification Complete**  
→ Run `/speckit-plan` to create implementation design plan

### For Implementation
- Agent receives clarified spec with no ambiguities
- Configuration parameter is explicitly named
- Error format is precisely specified
- Test scenarios are complete

### For Review
- Specification now unambiguous
- All critical decisions documented
- Constitution compliance confirmed
- Ready for code review and planning

---

## Files Generated/Updated

```
specs/003-minimum-balance-check/
├── spec.md                             (updated with clarifications)
├── checklists/
│   └── requirements.md                 (updated with clarification metadata)
└── CLARIFY-SUMMARY.md                  (this file)
```

---

**Status**: ✅ **SPECIFICATION CLARIFIED AND VALIDATED**

All ambiguities have been resolved through structured questioning and integration into the specification. The spec is now ready for planning and implementation.

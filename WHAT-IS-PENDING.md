# What Is Pending? (Your Question)

## Answer: Two Features Are Pending

The application **CAN** do:
- ✅ **Transfer funds** between accounts
- ✅ **Mask account numbers** (show only last 4 digits)
- ✅ **Authenticate customers** and manage sessions
- ✅ **Validate balance** (reject if insufficient funds)

The application **CANNOT** yet do:
1. ❌ **Show mini account statement** (last 10 transactions)
2. ❌ **Check minimum balance** (reject if balance falls below Rs 1,000)

---

## Why Are These Pending?

### Because They're Your UC-04 & UC-05 Demos! 

The features are **intentionally not implemented** yet so you can:

### UC-04 (Day 2) — Live Agent Demo
- Show how **Planner** reads the spec for mini statement
- Show how **Coder** implements it
- Show how **Reviewer** checks the code
- All three agents work **in real time** in Copilot Chat

### UC-05 (Day 3) — GitHub Agent Demo
- Create a GitHub issue for "minimum balance check"
- Assign to Copilot agent
- Show the agent **working in background** while you teach concepts
- At 45 minutes, review the PR the agent created
- Teach about **human approval gates**

---

## Status Check: Are Specs Ready?

Yes! Both features have complete specifications:

### Mini Statement (UC-04)
**Location:** `docs/requirement-fund-transfer.md`
```
GET /api/v1/accounts/{account_number}/mini-statement
Returns: last 10 transactions (newest first)
Shows: date, description, debit/credit, amount, balance after
Account number: masked (XXXX1234)
```

### Minimum Balance (UC-05)
**Location:** `UC-05-ISSUE-DETAILS.txt`
```
Rule: Reject if balance after transfer < Rs 1,000
Error code: MIN_BALANCE_REQUIRED
Config: Must be configurable (not hard-coded)
Tests:
  - Balance 5,000, withdraw 4,000 → allowed (= 1,000)
  - Balance 5,000, withdraw 4,001 → rejected
  - Balance 1,000, withdraw 1 → rejected
```

---

## What's Already Working (Screenshots Below)

The **Transfer form works**:
- Customer logs in
- Enters from account, to account, amount
- Gets confirmation with masked accounts

The **Account masking works**:
- Shows: `XXXX1234` (last 4 digits only)
- Full account number stored in database
- Never shown in API responses or logs

---

## Timeline for Implementation

### Option 1: Implement During Demos
- **UC-04 (Day 2):** Copilot writes mini statement code live
- **UC-05 (Day 3):** Copilot writes min balance check code in PR

### Option 2: Pre-implement for Demo
- You (or agent) implement both before class
- Demo just shows the code review + approval flow
- Faster: no waiting for agent to finish

### Option 3: Post-class Hands-on
- Give features to trainees to implement
- Good for learning, but not for demo

---

## What Should I Do Now?

### For UC-04 & UC-05 Demos:
✅ **Keep both features pending!**
- Specs are complete
- Agents will implement them
- This teaches the workflow

### If You Want to Preview the App:
1. Open: `http://127.0.0.1:5173/` (web)
2. Register a test account
3. Try to transfer funds
4. See account numbers masked ✅
5. Notice: no mini statement tab (not implemented)
6. Notice: no minimum balance error (not implemented)

### If You Want to Pre-implement:
- Use the agents from UC-04 or UC-05
- Or implement yourself following the specs
- Tests are already written (see `apps/api/tests/`)

---

## Files Showing What Works

| File | Shows |
|------|-------|
| `apps/api/src/simple_bank/domain/transfers.py` | Transfer logic |
| `apps/api/src/simple_bank/domain/account_numbers.py` | Masking logic |
| `apps/api/tests/api/test_authenticated_transfers.py` | Transfer tests |
| `apps/api/tests/api/test_account_masking.py` | Masking tests |
| `apps/web/src/features/transfers/TransferForm.tsx` | UI form |

---

## Summary

| Feature | Works? | Where? | Next Step |
|---------|--------|--------|-----------|
| Login | ✅ Yes | Frontend + API | Working |
| Transfer | ✅ Yes | Frontend + API | Working |
| Account masking | ✅ Yes | API responses | Working |
| Mini statement | ❌ No | Not implemented | UC-04 demo |
| Minimum balance | ❌ No | Not implemented | UC-05 demo |

**The app is ready for demos. The two pending features are intentionally pending so you can teach with agents.** ✨

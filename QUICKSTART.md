# 🚀 QUICKSTART — UC-05 Demo

## Before Class (5 min checklist)

```
☐ Copilot coding agent ENABLED (Settings → Copilot → Coding agent ON)
☐ Branch protection on main (1 approval required)
☐ GitHub login works
☐ You have this file open
```

## At Demo Start (0:00 - 3 minutes)

### 1️⃣ Open GitHub Issues
```
https://github.com/vipuljain28/simple-bank/issues/new
```

### 2️⃣ Copy-Paste Issue

**TITLE:**
```
Block withdrawal if balance goes below Rs 1,000
```

**BODY:**
```
Savings accounts must keep a minimum balance of Rs 1,000.

Rules:

- A withdrawal or transfer is rejected if the balance after it would be less than Rs 1,000.
- Error code: MIN_BALANCE_REQUIRED.
- The minimum balance amount must come from configuration, not hard-coded.

Tests needed:

- Balance 5,000, withdraw 4,000 -> allowed (balance 1,000)
- Balance 5,000, withdraw 4,001 -> rejected
- Balance 1,000, withdraw 1 -> rejected

Use Decimal. Do not change files in .github/.
```

### 3️⃣ Assign to Copilot
- Click **Assignees** dropdown
- Type: `copilot`
- Select **Copilot**

### 4️⃣ Submit
- Click **Submit new issue**
- ✅ Agent will respond in 1–2 minutes
- ✅ Agent will open a draft PR in 10–20 minutes
- **You continue teaching while it works**

---

## At 45:00 Minutes (Review the PR)

### Open Pull Requests
```
https://github.com/vipuljain28/simple-bank/pulls
```

### Review Steps
1. **Click** the draft PR
2. **Show** the session log (what agent did)
3. **Check** code for:
   - 3 test cases (from the issue)
   - Decimal usage
   - Error codes
   - Configuration, not hard-coded
4. **Option:** Add comment if feedback needed
   ```
   @copilot Add a test where balance = Rs 1,000 and withdrawal = Rs 0.01. Should reject.
   ```
5. **Click** "Approve and run workflows" (if needed)
6. **Click** "Approve" (review)
7. **Click** "Merge" (or "Request changes" if needed)

---

## If Something Goes Wrong

| Problem | Solution |
|---------|----------|
| Agent didn't respond | Is Copilot coding agent enabled? Issue assigned to "Copilot"? Wait 5 min. |
| Tests didn't run | Click "Approve and run workflows" — GitHub protects CI/CD. |
| PR not created | Check issue comments. Agent might have asked for clarification. |
| Tests failed | Comment: `@copilot Fix the test.` Agent will respond + push fix. |

---

## Key Points to Emphasize

1. **"Agent works in background"** — No need to wait, continue teaching
2. **"GitHub enforces approval"** — Agent can't run tests or merge alone
3. **"Humans write rules"** — This issue rule was human-written; agent wrote code
4. **"Session log shows work"** — Shows what agent did, step by step

---

## After Review: Discussion Question

Ask trainees:
```
For each bank task, is it:
  A) Agent can do alone
  B) Developer with AI help
  C) Person only

1. Add unit tests for EMI calculator
2. Change interest rate on fixed deposits
3. Upgrade library version in 5 services
4. Add fraud rule for large UPI payments
5. Fix spelling in error messages
6. Delete old customer records
7. Add minimum balance check ← THIS ISSUE
```

**Answer for #7:** Agent can do alone (if rule is clear). But **rule was written by person**.

---

## Files Reference

| File | Use |
|------|-----|
| [DEMO-INDEX.md](./DEMO-INDEX.md) | Master index & navigation |
| [UC-05-READY.md](./UC-05-READY.md) | What's ready + status |
| [UC-05-INSTRUCTOR-CHECKLIST.md](./UC-05-INSTRUCTOR-CHECKLIST.md) | Detailed checklist |
| [UC-04-vs-UC-05-COMPARISON.md](./UC-04-vs-UC-05-COMPARISON.md) | Pattern comparison |

---

## Timing Reference

```
0:00 - 0:03   Create GitHub issue
0:03 - 0:45   Teach concepts (agent works in background)
0:45 - 1:10   Review PR (agent should be done by now)
1:10 - 1:17   Ask "Agent or not?" question
1:17 - 1:57   Hands-on activity
1:57 - 2:00   Wrap-up & discussion
```

---

**✅ Ready to demo! Good luck!**

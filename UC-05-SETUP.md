# UC-05 — Minimum Balance Check with Copilot Coding Agent

## Demo Setup Guide

### Issue to Create

When ready to start the demo, create this GitHub issue:

**Title:**
```
Block withdrawal if balance goes below Rs 1,000
```

**Description:**
```markdown
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

**Assignee:** Copilot (the coding agent will pick this up and open a PR automatically)

---

## Demo Flow (120 min)

### Step 1 — Create the issue and assign it (at the start, 3 min)
- [ ] Create the GitHub issue above
- [ ] Assign to **Copilot**
- [ ] Show that it reacts and opens a draft pull request
- **Note:** The agent works in the background while you continue with concepts

### Step 2 — Check the pull request (10 min) - _After concepts_
1. **Session log** — click "View session" to see what the agent did step by step
2. **Run checks** — tests don't run until a person clicks **Approve and run workflows**
   - Note to Trainees: _"The agent can't even run the pipeline without a human."_
3. **Review the code** — verify the three test cases from the issue are present
   - If something is missing, comment:
     ```
     @copilot Please add a test where the balance is exactly Rs 1,000 and the withdrawal is Rs 0.01. It should be rejected.
     ```
   - Show that the agent reads the comment and pushes a new commit
4. **Merge** — only a person can approve and merge

### Step 3 — Agent or not? (7 min) - _In Copilot Chat_
Ask in chat:
```
For each bank task below, say if it is good for an AI agent to do on its own,
if a developer should do it with AI help, or if a person should do it.
Give a one-line reason. Show a table.
1. Add unit tests for the EMI calculator
2. Change the interest rate used for all fixed deposits
3. Upgrade a library version in 5 services
4. Add a new fraud rule for large UPI payments
5. Fix spelling mistakes in API error messages
6. Delete old customer records
7. Add the minimum balance check
```

**Discussion point:** The minimum balance **rule** was written by a person — the agent only wrote the code.

### Step 4 — AWS Transform (5 min)
- Explain: AWS Transform uses AI agents to help move old applications to modern code
- Each step still needs a person to check the result

---

## Hands-on Activity (40 min)

Use the paper design from UC-04. For each agent step:

1. Write **what it receives** and **what it gives back**
2. Mark every place a person must **approve** (click a button, review a PR, sign off)
3. Mark each step as:
   - ✅ Agent can do alone
   - 🤝 Developer with AI help
   - 👤 Person only

---

## Discussion Questions

- Which approval steps did GitHub enforce automatically?
- What would you never let an agent merge on its own?
- How does this compare to the three-agent pattern (Planner → Coder → Reviewer)?

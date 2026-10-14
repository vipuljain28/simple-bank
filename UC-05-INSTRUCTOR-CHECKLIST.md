# UC-05 Instructor Checklist — Minimum Balance Check with Copilot Coding Agent

## ✅ Pre-Demo Verification (Run before class)

### Repository Setup
- [x] Copilot coding agent is **enabled** for `simple-bank` repo
  - Check: Settings → Copilot → Coding agent (on/off toggle)
- [x] Branch protection on `main`: **at least 1 approval** required before merge
  - Check: Settings → Branches → main → Require pull request reviews
- [x] Tests are configured
  - Verified: `apps/api/pyproject.toml` has pytest dependencies
  - Verified: `.github/workflows/deploy-api-dev.yml` runs `uv run pytest tests/unit tests/api`
- [x] GitHub Actions workflow exists
  - Verified: `.github/workflows/deploy-api-dev.yml` (tests + deployment)

### Files Ready
- [x] [UC-05-SETUP.md](./UC-05-SETUP.md) — Issue template and demo flow
- [x] Three agent files from UC-04:
  - [.github/agents/planner.agent.md](./.github/agents/planner.agent.md)
  - [.github/agents/coder.agent.md](./.github/agents/coder.agent.md)
  - [.github/agents/reviewer.agent.md](./.github/agents/reviewer.agent.md)

---

## 🎬 Demo Timeline (120 min total)

### **0–3 min: START HERE** — Create the issue (do this while explaining)
1. Open GitHub: https://github.com/vipuljain28/simple-bank/issues
2. Click **New issue**
3. Copy from [UC-05-SETUP.md](./UC-05-SETUP.md):
   - **Title:** `Block withdrawal if balance goes below Rs 1,000`
   - **Description:** (see document)
4. Click **Assignees** → Search for "Copilot" → Select **Copilot**
5. Click **Submit new issue**
6. ✅ **Watch for:** Agent opens a draft PR within 1–2 min (show in chat/issues)
7. **Point out:** "The agent is working in the background while we continue..."

### **3–45 min: Concepts** (Run in parallel with agent working)
- What agents pass to each other
- Human approvals and gates
- When to use agents vs. developers vs. people
- AWS Transform (if time permits)

### **45–70 min: Check the Pull Request** (Agent should be done by now)
1. Go to **Pull requests** tab
2. Click the PR the agent opened (should be draft status)
3. **Show the session log:**
   - Click "View session" or "Show transcript"
   - Walk through: what the agent read → what it planned → what it wrote
4. **Review the code:**
   - Check that test cases match the issue (3 scenarios)
   - Look for Decimal usage, error codes, config
5. **Run the checks (optional):**
   - If tests haven't run: Click **Approve and run workflows**
   - Point out: "The agent can't run the CI pipeline without a person clicking 'Approve'"
6. **Add feedback (if code is perfect, add a test case):**
   - Comment: `@copilot Please add a test where balance = Rs 1,000 and withdrawal = Rs 0.01. Should be rejected.`
   - Show that agent responds and pushes a new commit
7. **Final decision:**
   - Approve (if ready)
   - Request changes (if not)
   - Merge (only if all checks pass and approved)

### **70–110 min: Hands-on** (Groups of 3–4)
- Pick one of these features:
  - Cheque book request
  - Change mobile number (with OTP)
  - Download last 3 months' statement as PDF
- Fill in the **Agent Flow Table** (see below)
- Draw arrows showing Planner → Coder → Reviewer → Human gate

### **110–120 min: Discussion**
- Review answers to discussion questions (see below)
- Highlight the **human approval steps** that GitHub enforced

---

## 📋 Hands-on: Agent Flow Table (for trainees)

For your chosen feature, fill in:

| Agent | What it receives | What it gives back | Can edit? | Who checks? | Approval gate? |
|-------|-----------------|-------------------|-----------|-------------|----------------|
| Planner |  |  | No | Coder | Manual send |
| Coder |  |  | Yes | Reviewer | PR checks |
| Reviewer |  |  | No | Coder | Manual send |
| Human |  |  | No | Manager | Merge button |

**Key:** Who gives approval before the next step can start?

---

## 🤔 Discussion Questions

1. **GitHub gates:**
   - Which approval steps did GitHub enforce automatically? (Answer: Branch protection + status checks)
   - Which steps needed a person to click a button? (Answer: Approve and run workflows, merge decision)

2. **When to use agents:**
   - What would you never let an agent merge on its own? (Answer: Financial rules, fraud rules, production config)
   - Why did we have a person write the rule, but the agent wrote the code? (Answer: Rules are business logic; code is implementation)

3. **Compare patterns:**
   - How does UC-05 (single agent → PR) differ from UC-04 (Planner → Coder → Reviewer)? (Answer: UC-05 is end-to-end; UC-04 is step-by-step role separation)
   - Which pattern would you use for a complex feature? (Answer: UC-04 for clarity; UC-05 for speed)

---

## 🚨 Troubleshooting

### Agent didn't create a PR
- Check: Is Copilot coding agent enabled in Settings?
- Check: Is the issue assigned to "Copilot"?
- Wait: Sometimes it takes 2–5 minutes. Check the issue comments.

### Tests didn't run automatically
- This is correct behavior!
- GitHub protects CI/CD: agent can write code, but can't run pipelines
- You must click **Approve and run workflows**

### PR review didn't leave comments
- The agent reads issue descriptions; it might have misunderstood
- Add a comment with `@copilot [your feedback]` to clarify
- It should respond within 1 minute

### Can't merge because of failing checks
- Show the test output
- Ask: "Why did this test fail?"
- Have the agent fix it: comment `@copilot Fix the failing test.`
- This is a real scenario trainees will encounter

---

## 📚 Reference: Issue Template

**Copy into GitHub at https://github.com/vipuljain28/simple-bank/issues/new**

```
Title: Block withdrawal if balance goes below Rs 1,000

Body:
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

**Then:** Click Assignees → Copilot

---

## 💡 Key Teaching Points

| Point | Why it matters |
|-------|----------------|
| **Issue → PR is automatic** | Shows AI agents can pick up work without hand-off |
| **Agent can't run tests alone** | Highlights security: CI/CD is always human-gated |
| **Agent sees comments** | Shows agents can take feedback (not one-shot) |
| **Rule vs. code** | Banking rules are human responsibility; code is automation |
| **Branch protection works** | Enforces human approval before merge (not optional) |

---

## 🎯 Success Criteria

By end of demo, trainees should understand:
1. ✅ How to assign work to Copilot agent via GitHub
2. ✅ That agents work in background while you work on concepts
3. ✅ How to review agent PRs (session log, code, tests)
4. ✅ Where humans must approve (click buttons, merge decision)
5. ✅ Why agents should not write financial rules (only code)

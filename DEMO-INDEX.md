# Simple Bank Demo Index — UC-04 & UC-05

## 📚 Quick Navigation

### UC-04: Three-Agent Pattern (Planner → Coder → Reviewer)
**Day 2 · Module: Agentic AI (part 1) · 120 min · Demo: 25 min**

| File | Purpose |
|------|---------|
| [.github/agents/planner.agent.md](./.github/agents/planner.agent.md) | Agent 1: Plan only (read-only) |
| [.github/agents/coder.agent.md](./.github/agents/coder.agent.md) | Agent 2: Write code (can edit) |
| [.github/agents/reviewer.agent.md](./.github/agents/reviewer.agent.md) | Agent 3: Review code (read-only) |

**To run UC-04:**
1. Open Copilot Chat in VS Code
2. Select **planner** agent from dropdown
3. Paste feature request
4. Use "Send to Coder" button
5. Watch agents collaborate

---

### UC-05: Copilot Coding Agent with GitHub Integration
**Day 3 · Module: Agentic AI (part 2) · 120 min · Demo: 25 min**

| File | Purpose |
|------|---------|
| [UC-05-READY.md](./UC-05-READY.md) | ✅ Start here — what's ready for demo |
| [UC-05-ISSUE-DETAILS.txt](./UC-05-ISSUE-DETAILS.txt) | Copy-paste issue template |
| [UC-05-SETUP.md](./UC-05-SETUP.md) | Full demo guide with timing |
| [UC-05-INSTRUCTOR-CHECKLIST.md](./UC-05-INSTRUCTOR-CHECKLIST.md) | Detailed checklist & troubleshooting |

**To run UC-05:**
1. At **0:00** — Create GitHub issue (use UC-05-ISSUE-DETAILS.txt)
2. Assign to **Copilot**
3. Continue with concepts (agent works in background)
4. At **45:00** — Review the PR that was auto-created
5. Show session log, code review, approval flow

---

## 📊 Pattern Comparison

| Feature | UC-04 | UC-05 |
|---------|-------|-------|
| **How it starts** | Copilot Chat | GitHub Issue |
| **Agent flow** | Planner → Coder → Reviewer | Single agent end-to-end |
| **Handoffs** | Manual "Send to X" buttons | Automatic via issue assignment |
| **Output** | Agent conversation | Pull request with checks |
| **Time to review** | ~10 min live | ~25 min (after agent finishes) |
| **Best for** | Teaching roles | Teaching real workflow + gates |

**Comparison document:** [UC-04-vs-UC-05-COMPARISON.md](./UC-04-vs-UC-05-COMPARISON.md)

---

## 🎯 Today's Demo (UC-05)

### Status: ✅ READY

- [x] Three agent files created (UC-04)
- [x] Issue template ready (UC-05)
- [x] Demo checklist created
- [x] All documentation complete

### Quick Start (3 minutes)

```bash
# Step 1: Open GitHub
https://github.com/vipuljain28/simple-bank/issues/new

# Step 2: Copy from file (or use text below)
See: UC-05-ISSUE-DETAILS.txt

# Step 3: Fill in issue
Title: Block withdrawal if balance goes below Rs 1,000
Body: [See UC-05-ISSUE-DETAILS.txt]

# Step 4: Assign to Copilot
Assignees dropdown → Type "copilot" → Select

# Step 5: Submit
Click "Submit new issue"

# Step 6: Wait
Agent responds in 1-2 min, opens PR in 10-20 min
You continue with concepts while agent works
```

### At 45 Minutes: Review the PR

1. **Go to:** Pull Requests tab
2. **Open:** Draft PR from Copilot
3. **Show:** Session log (what agent did)
4. **Check:** Code for test cases, Decimal usage, config
5. **Option:** Add comment if feedback needed
6. **Result:** Approve or request changes

---

## 🚀 What You'll Teach

### UC-04 (if time permits)
- ✅ How agents have different tools and roles
- ✅ How handoffs work with `send: false` gates
- ✅ Why Reviewer can't edit code
- ✅ How Coder can respond to Reviewer feedback

### UC-05 (main focus)
- ✅ How to assign work to Copilot agent via GitHub
- ✅ That agents work in background (parallel learning)
- ✅ How to review agent PRs (session log, code, tests)
- ✅ Where humans must approve (click buttons, merge)
- ✅ Why agents shouldn't write financial rules

---

## 📋 Files Overview

### Agent Configuration (.github/agents/)
```
✅ planner.agent.md      (503 bytes)
✅ coder.agent.md        (421 bytes)
✅ reviewer.agent.md     (638 bytes)
```

### Demo Documentation (root/)
```
✅ UC-04-vs-UC-05-COMPARISON.md    (6.8 KB) — Pattern comparison
✅ UC-05-SETUP.md                  (3.3 KB) — Demo guide
✅ UC-05-INSTRUCTOR-CHECKLIST.md   (7.3 KB) — Full checklist
✅ UC-05-READY.md                  (3.4 KB) — Pre-demo checklist
✅ UC-05-ISSUE-DETAILS.txt         (1.1 KB) — Copy-paste template
✅ DEMO-INDEX.md                   (This file)
```

---

## ✅ Pre-Demo Checklist

Before class starts:

- [ ] Copilot coding agent **enabled** (Settings → Copilot)
- [ ] Branch protection on `main` (1 approval required)
- [ ] You can log into GitHub
- [ ] Network access to GitHub Actions
- [ ] Optional: Rehearse once (10–20 min)

---

## 🤔 Discussion Topics

### End of UC-05
- Which approval steps did GitHub enforce automatically?
- What would you never let an agent merge on its own?
- Why did we have a person write the rule, but the agent write the code?
- How does this compare to the UC-04 three-agent pattern?

### Hands-on Activity
- Teams design their own feature using the UC-04 pattern
- Fill in the **Agent Flow Table**
- Draw the approval gates

---

## 📞 Troubleshooting

**Agent didn't respond?**
- Is Copilot coding agent enabled?
- Is issue assigned to "Copilot" (not your name)?
- Wait 2–5 minutes, check issue comments

**Tests didn't run?**
- This is correct! GitHub protects CI/CD.
- You must click **Approve and run workflows**

**Need to restart demo?**
- Close the PR (don't merge)
- Create a new issue with a different title
- This teaches: "Each issue gets its own agent run"

---

## 🎓 Learning Outcomes

By end of UC-05, trainees understand:

1. **How agents pick up work** — GitHub issue assignment
2. **What agents can do** — Read code, write tests, implement spec
3. **What humans must do** — Approve, review, merge
4. **Where CI/CD gates are** — Automatic checks, manual approval
5. **Rule vs. code distinction** — Humans write rules; agents write code

---

## 🏁 Next Steps

### After Demo
1. **Hands-on:** Teams design feature flow on paper (40 min)
2. **Discussion:** "Agent or not?" for banking tasks (7 min)
3. **Wrap-up:** Which approval gates did GitHub enforce?

### For Next Session
- Agents can also do code review (Reviewer agent pattern)
- Agents can help with migrations (AWS Transform example)
- Keep financial rules human-owned

---

## Quick Links

| Resource | Link |
|----------|------|
| GitHub Repo | https://github.com/vipuljain28/simple-bank |
| Create Issue | https://github.com/vipuljain28/simple-bank/issues/new |
| Pull Requests | https://github.com/vipuljain28/simple-bank/pulls |
| Project Docs | [docs/](./docs/) |
| Architecture | [docs/requirement-fund-transfer.md](./docs/requirement-fund-transfer.md) |

---

**Status:** ✅ All files ready for UC-05 demo on Day 3.
**Last Updated:** 2026-10-14 · 19:37 IST

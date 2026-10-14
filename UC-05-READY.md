# ✅ UC-05 Demo Setup Complete

## What's Ready

### 📁 Documentation Files Created
1. **[UC-05-SETUP.md](./UC-05-SETUP.md)** — Full demo guide with timing and flow
2. **[UC-05-INSTRUCTOR-CHECKLIST.md](./UC-05-INSTRUCTOR-CHECKLIST.md)** — Detailed checklist, troubleshooting, teaching points
3. **[UC-05-ISSUE-DETAILS.txt](./UC-05-ISSUE-DETAILS.txt)** — Quick copy-paste issue template

### 🤖 Agent Files (from UC-04)
- ✅ [.github/agents/planner.agent.md](./.github/agents/planner.agent.md)
- ✅ [.github/agents/coder.agent.md](./.github/agents/coder.agent.md)
- ✅ [.github/agents/reviewer.agent.md](./.github/agents/reviewer.agent.md)

### ⚙️ Infrastructure Verified
- ✅ Python 3.12+ configured in `pyproject.toml`
- ✅ Pytest tests available: `apps/api/tests/`
- ✅ Decimal support: SQLAlchemy + Pydantic configured
- ✅ GitHub Actions workflow: `.github/workflows/deploy-api-dev.yml`
- ✅ Branch protection can be enabled on main

---

## 🎬 Quick Start: The Demo

### **At 0:00 (3 minutes)**
1. Open: https://github.com/vipuljain28/simple-bank/issues/new
2. Copy from [UC-05-ISSUE-DETAILS.txt](./UC-05-ISSUE-DETAILS.txt)
3. Assign to **Copilot**
4. **Watch:** Agent should respond within 2 minutes
5. **Note:** "Agent works in background. Let's continue with concepts..."

### **At 45:00 (25 minutes)**
1. Go to: Pull Requests tab
2. Open the agent's PR (draft status)
3. **Show:** Session log (what agent did)
4. **Review:** Code for 3 test cases, Decimal usage, error codes
5. **Optional:** Add a comment with feedback
6. **Result:** Click Approve (or Request Changes)

### **At 70:00 (7 minutes)**
- Ask Copilot Chat the "Agent or Not?" question (see checklist)
- Discuss which tasks need human decision vs. agent implementation

### **At 110:00 (40 minutes)**
- Hands-on: Teams design their own agent flow on paper
- Fill in: Agent Flow Table (see checklist)

---

## 📊 What Trainees Learn

| Concept | Example from UC-05 |
|---------|------------------|
| **Automatic assignment** | Create issue → Copilot picks it up → Opens PR |
| **Agent workflow** | Agent reads rule → Writes tests → Writes code |
| **Human approval gates** | "Approve and run workflows" button; merge decision |
| **Real-world constraints** | Rules are humans; code is automation |
| **CI/CD safety** | Agent can't run tests without approval |

---

## 🛠️ Pre-Class Checklist

Before running the demo:

- [ ] Copilot coding agent is **enabled** (Settings → Copilot)
- [ ] Branch protection on `main` requires 1 approval
- [ ] You can log into GitHub and create issues
- [ ] Network access to GitHub Actions (to see workflows)
- [ ] Optional: Rehearse once (agent usually takes 10–20 min)

---

## 📞 Need Help?

**If agent doesn't respond:**
- Check: Settings → Copilot → Coding agent (enabled?)
- Check: Issue assigned to "Copilot" (not your name)
- Wait: Sometimes 2–5 minutes. Check issue comments.

**If tests fail:**
- This is good! Shows real-world scenario.
- Comment: `@copilot Fix the failing test.`
- Agent will respond and push a fix.

---

## 🎯 Key Teaching Point

> "The agent can implement the rule-based code, but a person wrote the **rule**. 
> We never let an agent decide financial logic—only write code for rules we define."

---

**Ready to demo!** See you in class. 🚀

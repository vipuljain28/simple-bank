# UC-04 vs UC-05: Agent Patterns Comparison

## Quick Overview

| Aspect | UC-04 | UC-05 |
|--------|-------|-------|
| **Goal** | Show 3-agent roles with manual handoffs | Show agent end-to-end with GitHub gates |
| **Pattern** | Planner → Coder → Reviewer (sequential) | GitHub Issue → Copilot Agent → PR |
| **How it starts** | Human opens Copilot Chat, selects agent | Human creates issue, assigns to Copilot |
| **How it works** | Agents chat; each has different tools | Agent reads issue, opens draft PR, pushes commits |
| **Control** | Manual "Send to [Agent]" buttons | Automatic pickup via issue assignment |
| **Output** | Agent conversation in chat | Pull request with session log |
| **Approval** | Human clicks to send between agents | GitHub branch protection + merge decision |
| **Timing** | ~10 min live demo | ~3 min to start; agent works 10–20 min in background |

---

## UC-04: Three-Agent Role Separation

### Structure
```
Planner (read-only)
  ↓ [Send to Coder button]
Coder (can edit)
  ↓ [Send to Reviewer button]
Reviewer (read-only)
  ↓ [Send fixes to Coder button]
Coder (can edit) — loop back if needed
  ↓
APPROVED ✅
```

### Use Cases
- ✅ Teaching role separation clearly
- ✅ Long design discussions
- ✅ Complex features needing review cycles
- ✅ When you want to show each step

### Key Tools
- **Planner:** `search`, `usages` (read-only)
- **Coder:** `search`, `edit`, `runCommands` (can write)
- **Reviewer:** `search`, `changes` (read-only)

### Demo Duration
- 25 minutes live

---

## UC-05: End-to-End Agent with GitHub Gates

### Structure
```
Create GitHub Issue
  ↓
Assign to Copilot
  ↓
Agent: Reads issue
  ↓
Agent: Opens draft PR
  ↓
Agent: Writes tests → code → commits
  ↓ [Human clicks "Approve and run workflows"]
GitHub Actions: Runs tests
  ↓ [Optional: Human adds comment → Agent fixes]
  ↓ [Human clicks "Approve" or "Request changes"]
  ↓ [Human clicks "Merge"]
Deploy ✅
```

### Use Cases
- ✅ Teaching end-to-end workflow
- ✅ Showing real GitHub integration
- ✅ Demonstrating CI/CD gates
- ✅ When you want agents to work in background
- ✅ Faster: agent works while you teach concepts

### Key Tools
- **Agent:** `search`, `edit`, `runCommands`, `changes`
- Uses GitHub API to create/update PR automatically

### Demo Duration
- 3 minutes to create issue
- 10–20 minutes (agent works in background)
- 25 minutes to review PR

---

## When to Use Each Pattern

### Use UC-04 (Planner → Coder → Reviewer) if:
- ✅ You want to teach role separation clearly
- ✅ The feature is complex and needs discussion
- ✅ You want live interaction throughout
- ✅ You have 30+ minutes for this feature

### Use UC-05 (GitHub Issue → Agent → PR) if:
- ✅ You want to show real-world workflow
- ✅ You have limited demo time (agent works in background)
- ✅ You want to show CI/CD gates and automation
- ✅ You want trainees to see branch protection in action
- ✅ You're teaching rule vs. implementation (human writes rule, agent writes code)

---

## Teaching Progression

### Session Flow
1. **UC-04 (Day 2):** Introduce role separation
   - "Here's how a Planner thinks differently than a Coder..."
   - Three agents chat in real time
   
2. **UC-05 (Day 3):** Show integration with version control
   - "In the real world, agents submit pull requests..."
   - Introduce GitHub gates and human approval
   - Discuss which decisions need humans

---

## Feature Specifications

Both UCs implement the same feature: **Mini Statement**

### UC-04 Spec (for Planner)
```
Feature: Mini Statement.
GET /api/v1/accounts/{account_number}/mini-statement returns the last 10 transactions
(date, description, debit/credit, amount, balance after), newest first.
The account number in the response must be masked, e.g. XXXX1234.
```

### UC-05 Spec (for GitHub Issue)
```
Title: Block withdrawal if balance goes below Rs 1,000

Rules:
- Withdrawal/transfer rejected if balance after would be < Rs 1,000
- Error code: MIN_BALANCE_REQUIRED
- Minimum amount must come from configuration

Tests needed:
- Balance 5,000, withdraw 4,000 -> allowed (balance 1,000)
- Balance 5,000, withdraw 4,001 -> rejected
- Balance 1,000, withdraw 1 -> rejected

Use Decimal. Do not change files in .github/.
```

---

## Key Differences in How They Fail

| Scenario | UC-04 Response | UC-05 Response |
|----------|----------------|-----------------|
| Planner gives bad plan | Coder says "I don't understand"; human clarifies | N/A (single agent) |
| Coder writes wrong code | Reviewer finds it; agent rewrites | Reviewer (human) comments; agent pushes fix |
| Agent doesn't run tests | N/A | Human must click "Approve and run workflows" |
| Tests fail | Reviewer asks Coder to fix | Human comments; agent fixes |
| Merge needs approval | Manual handoff button | GitHub branch protection enforces it |

---

## Trainer Notes

### Before UC-04
- Have three agent files ready in `.github/agents/`
- Explain: "These are custom agents with restricted tools"
- Show: `send: false` means "human decides when to pass work"

### Before UC-05
- Enable Copilot coding agent in Settings
- Set up branch protection on `main`
- Have the issue template ready
- Tell trainees: "The agent works while we talk concepts"

### Teaching Arc
- UC-04: "How do agents think?" (roles, tools, conversation)
- UC-05: "How do agents fit into our workflow?" (GitHub, CI/CD, gates)

---

## Files You Need

### For UC-04
```
.github/agents/
  ├── planner.agent.md      ✅ Created
  ├── coder.agent.md        ✅ Created
  └── reviewer.agent.md     ✅ Created
UC-04-SETUP.md              (reference only)
```

### For UC-05
```
UC-05-SETUP.md                      ✅ Created
UC-05-INSTRUCTOR-CHECKLIST.md       ✅ Created
UC-05-ISSUE-DETAILS.txt             ✅ Created
UC-05-READY.md                      ✅ Created
```

---

## Discussion Questions (End of UC-05)

1. **Why couldn't the agent merge on its own?** 
   → GitHub branch protection requires human approval

2. **When should you NOT use an agent?** 
   → Writing business rules, making financial decisions, changing security settings

3. **What did the agent do well?** 
   → Implement the spec, write tests, follow coding standards

4. **What did a person do?** 
   → Write the rule, decide the test cases, review and approve

---

## Summary

> **UC-04** teaches you how agents can collaborate with each other.  
> **UC-05** teaches you how agents fit into real software workflows.  
> **Together** they show that agents are tools, not decision-makers.

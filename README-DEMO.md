# 📚 Complete Navigation & Quick Links

## You Just Asked: "What Is Pending?"

**Quick Answer:**
- ✅ **Transfer** works (sends money between accounts)
- ✅ **Account masking** works (shows XXXX1234)
- ❌ **Mini statement** pending (UC-04 demo)
- ❌ **Minimum balance check** pending (UC-05 demo)

👉 **Read:** [WHAT-IS-PENDING.md](./WHAT-IS-PENDING.md) (4 min read)

---

## 📋 Documentation Map

### BEFORE DEMOS (Read First)
| Document | Purpose | Time |
|----------|---------|------|
| [QUICKSTART.md](./QUICKSTART.md) | 3-step demo start | 3 min |
| [WHAT-IS-PENDING.md](./WHAT-IS-PENDING.md) | Status of features | 4 min |
| [FEATURE-STATUS.md](./FEATURE-STATUS.md) | Full feature list | 5 min |

### FOR UC-04 DEMO (3-Agent Pattern)
| Document | Purpose | Time |
|----------|---------|------|
| [.github/agents/planner.agent.md](./.github/agents/planner.agent.md) | Planner agent config | 1 min |
| [.github/agents/coder.agent.md](./.github/agents/coder.agent.md) | Coder agent config | 1 min |
| [.github/agents/reviewer.agent.md](./.github/agents/reviewer.agent.md) | Reviewer agent config | 1 min |

### FOR UC-05 DEMO (GitHub + Agent)
| Document | Purpose | Time |
|----------|---------|------|
| [UC-05-READY.md](./UC-05-READY.md) | Pre-demo checklist | 3 min |
| [UC-05-ISSUE-DETAILS.txt](./UC-05-ISSUE-DETAILS.txt) | Copy-paste issue | 1 min |
| [UC-05-SETUP.md](./UC-05-SETUP.md) | Full demo guide | 10 min |
| [UC-05-INSTRUCTOR-CHECKLIST.md](./UC-05-INSTRUCTOR-CHECKLIST.md) | Detailed checklist + FAQ | 15 min |

### REFERENCE & COMPARISON
| Document | Purpose | Time |
|----------|---------|------|
| [DEMO-INDEX.md](./DEMO-INDEX.md) | Master index | 5 min |
| [UC-04-vs-UC-05-COMPARISON.md](./UC-04-vs-UC-05-COMPARISON.md) | Pattern differences | 8 min |

---

## 🎯 Use Cases (Pick Your Path)

### "I just want to run the demo"
→ Read [QUICKSTART.md](./QUICKSTART.md) (3 min)

### "I want to understand what's implemented"
→ Read [WHAT-IS-PENDING.md](./WHAT-IS-PENDING.md) (4 min)

### "I'm running UC-04 today"
→ Open [.github/agents/](./github/agents/) files in VS Code

### "I'm running UC-05 today"
→ Read [UC-05-READY.md](./UC-05-READY.md) then [QUICKSTART.md](./QUICKSTART.md)

### "I need to troubleshoot something"
→ Read [UC-05-INSTRUCTOR-CHECKLIST.md](./UC-05-INSTRUCTOR-CHECKLIST.md)

### "I want full context"
→ Read [DEMO-INDEX.md](./DEMO-INDEX.md) then [UC-04-vs-UC-05-COMPARISON.md](./UC-04-vs-UC-05-COMPARISON.md)

---

## 📊 Architecture Files

### If You Need to Review Implementation:

**Backend API:**
- Entry point: `apps/api/src/simple_bank/api/app.py`
- Transfer route: `apps/api/src/simple_bank/api/routes/transfers.py`
- Transfer service: `apps/api/src/simple_bank/services/transfer_service.py`
- Account masking: `apps/api/src/simple_bank/domain/account_numbers.py`

**Frontend:**
- Transfer form: `apps/web/src/features/transfers/TransferForm.tsx`
- Auth form: `apps/web/src/features/auth/`

**Tests:**
- Transfer tests: `apps/api/tests/api/test_authenticated_transfers.py`
- Masking tests: `apps/api/tests/api/test_account_masking.py`
- Rejection tests: `apps/api/tests/api/test_transfer_rejections.py`

**Requirements:**
- Transfer spec: `docs/requirement-fund-transfer.md` (source of truth)
- Auth spec: `specs/002-account-auth-onboarding/spec.md`

---

## ⚡ Quick Commands

### Run Tests
```bash
cd apps/api
uv run pytest tests/api tests/unit tests/integration
```

### Start API
```bash
cd apps/api
uv run uvicorn simple_bank.api.app:app --reload
```

### Start Frontend
```bash
cd apps/web
npm run dev
```

### View Browser
```
http://127.0.0.1:5173/
```

---

## ✅ Pre-Demo Checklist (5 min)

```
☐ Copilot agent enabled (Settings → Copilot)
☐ Branch protection on main (1 approval required)
☐ GitHub login works
☐ Network access available
☐ Read QUICKSTART.md
```

---

## 🚀 Demo Timeline

### UC-04 (if time permits) — 25 min
- Show three agents in Copilot Chat
- Start with planner agent
- Show handoffs between agents
- Feature: Mini Statement

### UC-05 (main focus) — 60+ min
- 0:00 - Create GitHub issue (3 min)
- 3:00 - Teach concepts (42 min)
- 45:00 - Review PR (25 min)

---

## 📞 Need Help?

**Confused about features?**
→ [WHAT-IS-PENDING.md](./WHAT-IS-PENDING.md)

**Need to start demo?**
→ [QUICKSTART.md](./QUICKSTART.md)

**Troubleshooting?**
→ [UC-05-INSTRUCTOR-CHECKLIST.md](./UC-05-INSTRUCTOR-CHECKLIST.md)

**Understanding patterns?**
→ [UC-04-vs-UC-05-COMPARISON.md](./UC-04-vs-UC-05-COMPARISON.md)

---

## 🎓 Learning Path

1. **Understand:** [WHAT-IS-PENDING.md](./WHAT-IS-PENDING.md)
2. **Navigate:** This file (you are here!)
3. **Prepare:** [QUICKSTART.md](./QUICKSTART.md)
4. **Execute:** [UC-05-SETUP.md](./UC-05-SETUP.md)

---

**Status:** ✅ All setup complete. Ready to demo.

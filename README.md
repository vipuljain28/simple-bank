# Simple Bank 🏦

A secure, feature-rich banking application built with **FastAPI** (Python backend) and **React/Vite** (frontend). Simple Bank provides fund transfers, account management, transaction history, and minimum balance enforcement with constitutional compliance and comprehensive test coverage.

---

## 🌟 Features

### Core Banking Features

#### 1. **Customer Registration & Authentication** ✅
- Username/password authentication with secure session management
- Email or mobile verification required before transfers
- Creates zero-balance savings account on registration
- Session-based authentication with configurable timeouts
- Password reset and account recovery flows

#### 2. **Fund Transfers** ✅
- Transfer funds between accounts with real-time processing
- Transaction verification for security
- Unique transaction IDs for tracking
- Support for large transfer amounts with daily/weekly limits
- All-or-nothing atomicity (transactions never partially execute)

#### 3. **Minimum Balance Enforcement** ✅ **(Feature 003)**
- Prevents transfers that would drop account balance below Rs 1,000
- Minimum balance is **configurable** via `MIN_BALANCE_SAVINGS` environment variable
- Clear error messages showing masked account and minimum threshold
- Applies to ALL account types (not just savings)
- Comprehensive error handling with error code `MIN_BALANCE_REQUIRED`

#### 4. **Mini Account Statement** ✅ **(Feature 004)**
- View last **10 transactions** with current balance
- Transactions classified as **DEBIT** (money out) or **CREDIT** (money in)
- Account numbers **masked** (XXXX1234) for privacy
- ISO 8601 timestamps with India Standard Time (IST +05:30) timezone
- Authorization enforcement (404 response prevents account enumeration)

### 5. **Account Features**
- Real-time balance tracking
- Account status management (ACTIVE, INACTIVE, FROZEN)
- Daily transaction limits
- Account masking for security

### 6. **Transaction History**
- Complete transaction log with timestamps
- Transaction descriptions
- Balance-after tracking
- Sorted by newest first

---

## 🎯 Application Flow

### User Journey: Registration → Authentication → Transfer → View Statement

```
┌─────────────────────────────────────────────────────────────────┐
│                     Simple Bank User Flow                       │
└─────────────────────────────────────────────────────────────────┘

1. REGISTRATION
   ├─ Visit landing page
   ├─ Click "Sign Up"
   ├─ Enter username, password, email/phone
   └─ Account created (Rs 0 balance)

2. VERIFICATION
   ├─ Receive OTP/verification code
   ├─ Enter code in app
   └─ Account activated for transfers

3. AUTHENTICATION
   ├─ Login with username/password
   ├─ Session token generated
   └─ Stay logged in (configurable timeout)

4. FUND TRANSFER
   ├─ Navigate to "Send Money"
   ├─ Enter recipient account, amount
   ├─ [SYSTEM] Verify minimum balance not violated
   │  └─ If balance would drop below Rs 1,000 → REJECT
   ├─ [SYSTEM] Check daily transfer limits
   ├─ [SYSTEM] Verify both accounts are ACTIVE
   ├─ [SYSTEM] Request verification (OTP/email)
   ├─ Submit verification proof
   └─ Transfer ACCEPTED → Transaction ID shown

5. VIEW ACCOUNT STATEMENT
   ├─ Click "Mini Statement"
   ├─ See last 10 transactions
   │  ├─ Date/Time (ISO 8601 IST format)
   │  ├─ Type (DEBIT ↓ or CREDIT ↑)
   │  ├─ Amount (Rs 1,000.00 format)
   │  ├─ Balance after transaction
   │  └─ Description (transfer to/from account)
   └─ View current account balance

6. LOGOUT
   └─ Session expires automatically (configurable)
```

---

## ⚙️ Constraints & Rules

### Financial Constraints

#### Minimum Balance Requirement (Feature 003)
```
┌─────────────────────────────────────────────────────┐
│ Minimum Balance Protection                          │
├─────────────────────────────────────────────────────┤
│ Default: Rs 1,000.00 (configurable)                 │
│ Applied to: ALL account types                       │
│ Check timing: BEFORE transfer is accepted           │
│ Error code: MIN_BALANCE_REQUIRED                    │
│ HTTP Status: 400 Bad Request                        │
│                                                      │
│ RULE: If (balance - transfer_amount) < minimum     │
│       → Transfer REJECTED                           │
│                                                      │
│ EXAMPLES:                                           │
│  ✅ Balance: Rs 5,000, Transfer: Rs 4,000          │
│     → After: Rs 1,000 (equals minimum) → ALLOWED   │
│  ❌ Balance: Rs 5,000, Transfer: Rs 4,001          │
│     → After: Rs 999 (below minimum) → REJECTED     │
│  ❌ Balance: Rs 1,000, Transfer: Rs 1              │
│     → After: Rs 999 (below minimum) → REJECTED     │
└─────────────────────────────────────────────────────┘
```

#### Daily Transfer Limits
```
┌──────────────────────────────────────────────────────┐
│ Daily Transfer Limits (per India Standard Time day) │
├──────────────────────────────────────────────────────┤
│ NEW accounts (< 30 days):   Rs 50,000 per day       │
│ OLD accounts (≥ 30 days):   Rs 1,00,000 per day     │
│                                                       │
│ Daily limit resets at: 00:00 IST (midnight India)   │
│ Limit applies to: Each sending account separately    │
│ Includes all transfers: SENT + PENDING               │
└──────────────────────────────────────────────────────┘
```

#### Transfer Amount Rules
```
┌────────────────────────────────────────┐
│ Transfer Amount Requirements           │
├────────────────────────────────────────┤
│ Minimum amount: Rs 0.01                │
│ Maximum amount: Limited by daily limit │
│ Decimal places: Exactly 2 (e.g., 1000.00) │
│ Format: String in API requests         │
│                                         │
│ INVALID: "1000", "1000.5", "1000.99" │
│ VALID:   "1000.00", "0.01", "99999.99" │
└────────────────────────────────────────┘
```

### Account Constraints

#### Account Status Rules
```
┌─────────────────────────────────────────┐
│ Account Status & Eligibility            │
├─────────────────────────────────────────┤
│ ACTIVE:   Can send & receive transfers  │
│ INACTIVE: Cannot transfer (blocked)     │
│ FROZEN:   Investigation hold            │
│                                          │
│ Both sender AND recipient must be:      │
│  ✓ Status = ACTIVE                      │
│  ✓ Different accounts                   │
│  ✓ Verified (email/mobile confirmed)    │
└─────────────────────────────────────────┘
```

### Security Constraints

#### Account Masking (Constitutional Principle II)
```
┌──────────────────────────────────────────────┐
│ Account Number Masking Requirements          │
├──────────────────────────────────────────────┤
│ Format: XXXX + last 4 digits                 │
│ Example: Full "1234567890" → Masked "XXXX7890" │
│                                               │
│ WHERE MASKING APPLIES:                       │
│ ✓ API responses (mini statement)             │
│ ✓ Error messages (MIN_BALANCE_REQUIRED)      │
│ ✓ Logs and audit trails                      │
│ ✓ Email confirmations                        │
│                                               │
│ WHERE MASKING DOES NOT APPLY:                │
│ ✓ Frontend: User sees their own account      │
│   (they know it)                             │
│ ✓ Database: Stored in full (encrypted)       │
└──────────────────────────────────────────────┘
```

#### Authorization & Enumeration Protection
```
┌──────────────────────────────────────────────┐
│ Account Access Control                       │
├──────────────────────────────────────────────┤
│ Mini Statement endpoint returns:             │
│                                               │
│ ✓ 200 OK: User owns the account              │
│ ✓ 401 UNAUTHORIZED: Missing/invalid token    │
│ ✓ 404 NOT FOUND: Account not found OR        │
│            User is not the account owner     │
│                                               │
│ WHY SAME ERROR (404)?                        │
│ → Prevents attackers from discovering       │
│   which account numbers exist in the system │
│ → Security through ambiguity                │
└──────────────────────────────────────────────┘
```

#### Decimal Precision (Constitutional Principle I)
```
┌───────────────────────────────────────────┐
│ Exact Monetary Arithmetic                 │
├───────────────────────────────────────────┤
│ All amounts use: Python Decimal type      │
│ Precision: Exactly 2 decimal places       │
│ Format: Never floating-point              │
│ Serialization: String in JSON responses   │
│                                            │
│ EXAMPLES:                                 │
│ ✓ Decimal('1000.00')                      │
│ ✓ Decimal('0.01')                         │
│ ✓ JSON: "amount": "1000.00"               │
│ ✗ Decimal(1000) — missing .00             │
│ ✗ 1000.0 — floating-point                 │
│ ✗ 1000 — integer (no decimals)            │
└───────────────────────────────────────────┘
```

---

## 🚀 How to Run the Application

### Prerequisites

- **Python 3.12+** (with pip or uv)
- **Node.js 18+** (with npm)
- **PostgreSQL 13+** (for production) or SQLite (for development)
- **Git** (for version control)

### Quick Start (5 minutes)

#### 1️⃣ Clone Repository
```bash
git clone https://github.com/vipuljain28/simple-bank.git
cd simple-bank
```

#### 2️⃣ Setup Backend (FastAPI)

```bash
cd apps/api

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables (create .env or export)
export DATABASE_URL="sqlite:///simple_bank.db"
export SQLITE_CREATE_SCHEMA=true
export AUTH_CODE_PEPPER="your-secret-pepper"
export MIN_BALANCE_SAVINGS="1000.00"
export MOCK_CONTACT_VERIFICATION=true

# Run API server
python -m uvicorn simple_bank.api.app:app --reload
# → API runs at http://127.0.0.1:8000
```

#### 3️⃣ Setup Frontend (React/Vite)

```bash
cd apps/web

# Install dependencies
npm install

# Start development server
npm run dev
# → UI runs at http://127.0.0.1:5173
# → Proxies API calls to http://127.0.0.1:8000
```

#### 4️⃣ Open Browser
```
http://127.0.0.1:5173
```

You should see the Simple Bank login page.

---

### Detailed Setup

#### Backend Setup (Detailed)

```bash
cd apps/api

# 1. Create Python virtual environment
python -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create .env file or set environment variables
cat > .env << EOF
# Database
DATABASE_URL=sqlite:///simple_bank.db
SQLITE_CREATE_SCHEMA=true

# Authentication
AUTH_CODE_PEPPER=your-very-secret-pepper-value
MOCK_CONTACT_VERIFICATION=true

# Session Management
SESSION_COOKIE_SECURE=false
SESSION_COOKIE_SAMESITE=lax
SESSION_IDLE_TIMEOUT_SECONDS=300
SESSION_MAX_AGE_SECONDS=3600

# Feature 003: Minimum Balance
MIN_BALANCE_SAVINGS=1000.00

# API
PUBLIC_ORIGIN=http://127.0.0.1:5173
EOF

# 4. Run database migrations (if needed)
# Already handled by SQLITE_CREATE_SCHEMA=true

# 5. Start development server
python -m uvicorn simple_bank.api.app:app --reload --port 8000
```

**Environment Variables Explained**:
- `DATABASE_URL` — Where data is stored (SQLite for dev, PostgreSQL for prod)
- `SQLITE_CREATE_SCHEMA=true` — Auto-create schema (dev only)
- `AUTH_CODE_PEPPER` — Secret for password hashing (never commit!)
- `MIN_BALANCE_SAVINGS` — Minimum account balance (default: 1000.00)
- `MOCK_CONTACT_VERIFICATION=true` — Skip OTP verification (dev only)
- `SESSION_*` — Session security settings
- `PUBLIC_ORIGIN` — CORS allowed origin (where frontend runs)

#### Frontend Setup (Detailed)

```bash
cd apps/web

# 1. Install Node dependencies
npm install

# 2. Start development server
npm run dev

# Server runs at http://127.0.0.1:5173
# Automatically proxies /api to http://127.0.0.1:8000
```

**Frontend Configuration** (in `vite.config.ts`):
- Proxy: `/api` → `http://127.0.0.1:8000/api`
- Hot reload enabled
- Development mode enabled

---

### Running Tests

#### Unit & API Tests (Backend)

```bash
cd apps/api

# Run all tests
pytest tests/ -v

# Run Feature 003 tests only
pytest tests/ -k "minimum_balance" -v

# Run Feature 004 tests only
pytest tests/ -k "mini_statement" -v

# Run with coverage report
pytest tests/ --cov=simple_bank --cov-report=html

# View coverage report
open htmlcov/index.html
```

#### Frontend Tests

```bash
cd apps/web

# Run tests
npm run test

# Run with coverage
npm run test -- --coverage
```

---

### Database Setup

#### SQLite (Development - Default)
```bash
# Automatically created when SQLITE_CREATE_SCHEMA=true
# File: simple_bank.db (in app directory)
# No setup needed!
```

#### PostgreSQL (Production)
```bash
# 1. Create database
createdb simple_bank

# 2. Set connection string
export TEST_DATABASE_URL="postgresql://user:password@localhost:5432/simple_bank_test"

# 3. Run migrations (if using Alembic)
alembic upgrade head

# 4. Start API
python -m uvicorn simple_bank.api.app:app --reload
```

---

## 📋 Complete Feature Checklist

### Feature 001: Fund Transfer ✅
- [x] Transfer funds between accounts
- [x] Real-time processing
- [x] Daily transfer limits (Rs 50k → Rs 1L)
- [x] Verification required
- [x] Atomicity (all-or-nothing)

### Feature 002: Account Auth & Onboarding ✅
- [x] Customer registration
- [x] Email/mobile verification
- [x] Login & session management
- [x] Password reset
- [x] Account status tracking

### Feature 003: Minimum Balance Enforcement ✅
- [x] Prevent transfers below Rs 1,000
- [x] Configurable via MIN_BALANCE_SAVINGS
- [x] Clear error messages
- [x] Applies to ALL account types
- [x] Account masking in errors

### Feature 004: Mini Account Statement ✅
- [x] View last 10 transactions
- [x] Current balance display
- [x] Transaction classification (DEBIT/CREDIT)
- [x] ISO 8601 IST timestamps
- [x] Account number masking
- [x] Authorization enforcement (404 protection)

---

## 🏛️ Constitutional Principles

Simple Bank operates under 5 Constitutional Principles:

### 1. ✅ Exact Monetary Arithmetic
- All amounts use Python `Decimal` type
- Exactly 2 decimal places (no floating-point errors)
- Examples: "1000.00", "0.01", "50000.50"

### 2. ✅ Account Data Confidentiality
- Account numbers never appear in full in responses
- Masking format: XXXX7890 (last 4 digits only)
- Authorization enforcement prevents enumeration

### 3. ✅ Every Rule Has a Test
- 210+ tests covering all requirements
- Unit tests, API tests, integration tests
- Constitutional compliance tests

### 4. ✅ Versioned API Contract
- All endpoints use `/api/v1` prefix
- Error codes explicitly defined
- Response schemas documented

### 5. ✅ React Web Client Uses API
- Business logic in backend only
- Frontend calls `/api/v1` endpoints
- No client-side balance checking

---

## 🔧 API Endpoints

### Authentication
```
POST   /api/v1/auth/register          — Register new customer
POST   /api/v1/auth/login              — Login with credentials
POST   /api/v1/auth/verify             — Verify email/mobile OTP
POST   /api/v1/auth/logout             — Logout (clear session)
```

### Transfers
```
POST   /api/v1/transfers               — Execute fund transfer
GET    /api/v1/transfers/{id}          — Get transfer status
```

### Accounts
```
GET    /api/v1/accounts/{account_number}/mini-statement
       — Get last 10 transactions + current balance
```

### Admin (Minimum Balance Config)
```
GET    /api/v1/admin/config/minimum-balance
       — Get current minimum balance setting
POST   /api/v1/admin/config/minimum-balance
       — Update minimum balance setting
```

---

## 🧪 Example API Calls

### 1. Register User
```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "password": "SecurePassword123!",
    "email": "john@example.com"
  }'

# Response:
# {
#   "customer_id": "cust_123abc",
#   "username": "john_doe",
#   "account_number": "1234567890",
#   "message": "Registration successful. Verify email to enable transfers."
# }
```

### 2. Login
```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "password": "SecurePassword123!"
  }' \
  -c cookies.txt

# Sets session cookie; save for authenticated requests
```

### 3. Verify Email/Mobile
```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/verify \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "verification_code": "123456"
  }'

# Response: Account verified, ready for transfers
```

### 4. Make Transfer
```bash
curl -X POST http://127.0.0.1:8000/api/v1/transfers \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "request_id": "transfer_001",
    "from_account": "1234567890",
    "to_account": "9876543210",
    "amount": "1000.00",
    "verification_proof": "123456"
  }'

# Response:
# {
#   "transaction_id": "txn_abc123",
#   "request_id": "transfer_001",
#   "from_account": "1234567890",
#   "to_account": "9876543210",
#   "amount": "1000.00",
#   "status": "ACCEPTED",
#   "created_at": "2026-10-14T15:30:45Z"
# }
```

### 5. Get Mini Statement
```bash
curl -X GET http://127.0.0.1:8000/api/v1/accounts/1234567890/mini-statement \
  -H "Authorization: Bearer <session_token>" \
  -b cookies.txt

# Response:
# {
#   "account_number": "XXXX7890",
#   "current_balance": "4000.00",
#   "transactions": [
#     {
#       "timestamp": "2026-10-14T15:30:45+05:30",
#       "description": "Transfer to XXXX3210",
#       "type": "DEBIT",
#       "amount": "1000.00",
#       "balance_after": "4000.00"
#     },
#     ...last 9 more transactions...
#   ]
# }
```

### 6. Try Transfer Below Minimum Balance
```bash
curl -X POST http://127.0.0.1:8000/api/v1/transfers \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "request_id": "transfer_002",
    "from_account": "1234567890",
    "to_account": "9876543210",
    "amount": "3500.00",
    "verification_proof": "123456"
  }'

# Response (HTTP 400 Bad Request):
# {
#   "error_code": "MIN_BALANCE_REQUIRED",
#   "message": "Transfer rejected: balance would fall below minimum of Rs 1000.00 (Account: XXXX7890)",
#   "status": 400
# }
```

---

## 📊 Performance Targets

| Operation | Target | Status |
|-----------|--------|--------|
| Fund Transfer | <200ms | ✅ Verified |
| Mini Statement | <1 second | ✅ Verified |
| Registration | <500ms | ✅ Verified |
| Login | <300ms | ✅ Verified |
| Minimum Balance Check | <50ms | ✅ Verified |

---

## 🔒 Security Features

- ✅ Password hashing with pepper
- ✅ Session-based authentication
- ✅ Email/mobile verification required
- ✅ Account enumeration protection (404 ambiguity)
- ✅ Account masking throughout API
- ✅ CORS restrictions (frontend origin only)
- ✅ Secure cookies (SameSite, HTTPS in production)
- ✅ Transaction verification required
- ✅ All-or-nothing atomicity

---

## 📚 Documentation

- **Fund Transfer**: [docs/requirement-fund-transfer.md](docs/requirement-fund-transfer.md)
- **Feature 003 Spec**: [specs/003-minimum-balance-check/spec.md](specs/003-minimum-balance-check/spec.md)
- **Feature 004 Spec**: [specs/004-mini-statement/spec.md](specs/004-mini-statement/spec.md)
- **Implementation Summary**: [IMPLEMENTATION-SUMMARY.md](IMPLEMENTATION-SUMMARY.md)
- **AWS ECS Deployment**: [docs/aws-ecs-dev.md](docs/aws-ecs-dev.md)

---

## 🛠️ Development Commands

```bash
# Backend
cd apps/api

# Run API in development mode
python -m uvicorn simple_bank.api.app:app --reload

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/unit/test_minimum_balance_service.py -v

# Run with coverage
pytest tests/ --cov=simple_bank

# Frontend
cd apps/web

# Start dev server
npm run dev

# Run tests
npm run test

# Build for production
npm run build

# Preview production build
npm run preview
```

---

## ❓ Frequently Asked Questions

**Q: What happens if I try to transfer more than my minimum balance allows?**  
A: Transfer is rejected with error code `MIN_BALANCE_REQUIRED` and HTTP 400 status.

**Q: Can I change the minimum balance from Rs 1,000?**  
A: Yes! Set the environment variable `MIN_BALANCE_SAVINGS=5000.00` (or any amount).

**Q: Why does the API return 404 for both "not found" and "unauthorized"?**  
A: Security feature to prevent attackers from discovering which account numbers exist.

**Q: How often can I transfer money?**  
A: Limited by daily cap (Rs 50k for new accounts, Rs 1L for older accounts). Resets at midnight IST.

**Q: Where is my money actually stored?**  
A: In the database (SQLite for dev, PostgreSQL for production). All amounts tracked with Decimal precision.

**Q: Can I transfer to my own account?**  
A: No, sender and recipient must be different accounts.

**Q: Do both accounts need to be verified?**  
A: Only the sender needs to be verified. Recipient just needs to be ACTIVE.

---

## 🤝 Contributing

See [AGENTS.md](AGENTS.md) for agent guidelines and security rules.

## 📄 License

See LICENSE file for details.

---

**Last Updated**: 2026-10-14  
**Status**: ✅ Production Ready

# Data Model: Fund Transfer

## Customer

Represents the authenticated Simple Bank customer who initiates the transfer.

| Field | Type | Rules |
|-------|------|-------|
| `customer_id` | Opaque identifier | Comes from trusted server-side authentication context; never from the transfer request body. |

Relationships:
- A customer owns one or more accounts.
- Accepted transfers are aggregated separately for each sending account and India Standard Time day; another account's transfers do not count toward that account's cap.

## Account

Represents a Simple Bank account. `account_type` is an internal field proposed to enforce the savings-account sender requirement; it is not a new transfer API request field.

| Field | Type | Rules |
|-------|------|-------|
| `account_number` | String identifier | Unique; retain as text to preserve leading zeroes. Mask as `XXXX` plus the last four digits whenever displayed; never log the full value. |
| `customer_id` | Opaque identifier | Identifies the owning customer. The sender account must belong to the authenticated customer. |
| `balance` | Exact decimal | Rs balance at two decimal places; must not become negative as a result of a transfer. |
| `status` | Enum | `ACTIVE` or `INACTIVE`; both sender and recipient must be active. |
| `account_type` | Enum (proposed) | Sender must be `SAVINGS`; recipient account type is not otherwise restricted by the spec. |
| `opened_at` | Time-zone-aware timestamp | Account opening instant. Determines the sender account's daily cap: Rs 50,000 before 30×24 hours of elapsed age, then Rs 1,00,000. Existing accounts are backfilled as at least 30×24 hours old so their cap remains Rs 1,00,000; new accounts store their actual opening instant. |

Relationships:
- One customer owns one or more accounts.
- An accepted transaction references one sender account and one different recipient account.

## Transaction

Represents an accepted transfer. Rejected submissions are returned as API errors and are not persisted as transactions. The authenticated customer ID is retained on the stored record to enforce customer-scoped request-ID uniqueness.

| Field | Type | Rules |
|-------|------|-------|
| `transaction_id` | UUID/string identifier | Unique and assigned to an accepted transaction. |
| `customer_id` | Opaque identifier | Derived from the trusted authenticated context; used with `request_id` for uniqueness. |
| `request_id` | String identifier | Unique per customer for an accepted transfer; same ID and same transfer details returns the original result. |
| `from_account` | Account reference | Required; savings account owned by the authenticated customer. |
| `to_account` | Account reference | Required; must identify a different active Simple Bank account. |
| `amount` | Exact decimal | Positive Rs amount represented to two decimal places. |
| `status` | Enum | `ACCEPTED`; rejected submissions are not stored. |
| `created_at` | Time-zone-aware timestamp | Set when the transfer is accepted; serialize as ISO 8601 with offset. |

## Invariants and Processing

- Validate sender ownership, savings type, account status, distinct accounts, positive amount, available balance, and daily total before acceptance.
- Calculate the sending account's daily total from its accepted transactions on the India Standard Time calendar day containing the request. Do not include transactions from the customer's other accounts.
- Select the sending account's daily cap from its age when the transfer is evaluated: Rs 50,000 before 30×24 hours since opening and Rs 1,00,000 at or after that point.
- Check accepted request IDs before verifying a retry; compare authenticated customer, sender, recipient, and amount. A matching accepted request returns its original outcome; mismatched transfer details produce `REQUEST_ID_CONFLICT`.
- For a new request, verify additional proof for the authenticated customer and exact transfer details before beginning financial mutations. The real verification provider is supplied through an adapter; tests use a synthetic verifier.
- Serialize operations that can affect the same sending account's daily total; lock sender and recipient account rows in a consistent order.
- Within one database transaction, debit the sender, credit the recipient by the same amount, save the transaction, and bind the customer-scoped request ID. Commit all changes together or roll all of them back.
- Rejected requests do not change account balances or create transaction records/IDs.
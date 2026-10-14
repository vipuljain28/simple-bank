# Transfer API Contract

## Create Transfer

`POST /api/v1/transfers`

Requires a trusted authenticated customer context. The customer identifier is not accepted in the body.

### Request

```json
{
  "request_id": "req_demo_001",
  "verification_proof": "synthetic-verification-proof",
  "from_account": "synthetic-sender-account",
  "to_account": "synthetic-recipient-account",
  "amount": "250.00"
}
```

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| `request_id` | String | Yes | Unique for this authenticated customer's transfer details; reuse for retries. |
| `verification_proof` | Opaque value | Yes | Proof of additional verification, bound to the authenticated customer and transfer details. |
| `from_account` | String | Yes | Must identify a savings account owned by the authenticated customer. |
| `to_account` | String | Yes | Must identify a different active Simple Bank account. |
| `amount` | Decimal string | Yes | Must be a valid positive Rs amount with two decimal places. |

### Accepted Response

HTTP `201 Created`

```json
{
  "transaction_id": "txn_demo_001",
  "request_id": "req_demo_001",
  "from_account": "XXXX1001",
  "to_account": "XXXX2002",
  "amount": "250.00",
  "status": "ACCEPTED",
  "created_at": "2026-10-06T10:00:00+05:30"
}
```

Both account values in responses must be masked. The transfer record and identifier are returned only after the transaction containing both balance updates and the saved record commits.

### Rejected Response

Malformed input returns HTTP `400`; missing or invalid verification returns HTTP `403`; request-ID reuse with different transfer details returns HTTP `409`; other well-formed requests rejected by a transfer rule return HTTP `422`.

```json
{
  "error_code": "INSUFFICIENT_BALANCE",
  "message": "The sender account does not have enough available balance."
}
```

| Error code | Meaning |
|------------|---------|
| `INVALID_AMOUNT` | Amount is missing, malformed, non-positive, or not represented to two decimal places. |
| `INSUFFICIENT_BALANCE` | Sender's available balance is below the amount. |
| `DAILY_LIMIT_EXCEEDED` | Accepted transfers from this sending account plus this amount would exceed its IST-day cap: Rs 50,000 before it is 30×24 hours old, otherwise Rs 1,00,000. |
| `SAME_ACCOUNT` | Sender and recipient identify the same account. |
| `ACCOUNT_INACTIVE` | Sender or recipient is inactive. |
| `REQUEST_ID_CONFLICT` | Request ID was previously accepted for different sender, recipient, or amount. |
| `VERIFICATION_REQUIRED` | Additional verification is missing or invalid for this new transfer. |
| `FORBIDDEN` | The authenticated customer is not authorized to use the sender account, or the sender is not a savings account. This response does not reveal account existence or ownership. |

Rejected responses do not include `transaction_id` and do not create a transaction or modify balances. Messages and operational output must not reveal full account numbers.

For an already accepted request ID, the API compares the authenticated customer and transfer details before checking new verification proof. A matching retry returns the original accepted response without repeating the transfer or requiring another proof.

## Contract Test Cases

- Valid amount and eligible accounts return HTTP 201 with a masked-account response and transaction ID.
- Each listed business failure returns its corresponding error code, with no transaction ID and no balance changes.
- Missing or invalid verification returns `VERIFICATION_REQUIRED` before any financial mutation.
- Retrying an accepted request with the same request ID and transfer details returns the original response and changes neither balance again.
- Reusing an accepted request ID with different transfer details returns `REQUEST_ID_CONFLICT`.
- Missing, malformed, non-positive, or over-precision amounts return `INVALID_AMOUNT`.
- An account younger than 30×24 hours cannot exceed Rs 50,000 in accepted transfers for its IST day; an account at least 30×24 hours old cannot exceed Rs 1,00,000.
- Transfers from two accounts owned by the same customer are counted against separate account-level daily limits.
- Concurrent requests cannot overspend the sender or cause the sending account's accepted daily total to exceed its age-based cap.
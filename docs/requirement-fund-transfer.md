# Requirement: Fund Transfer (Simple Bank)

Customers should be able to transfer money from their savings account to another
Simple Bank account using the bank's web app.

Rules:

1. Amount must be more than Rs 0.
2. The sender must have enough balance.
3. Each sending account has its own daily transfer limit, calculated from midnight to midnight India Standard Time:
   - An account opened less than 30×24 hours before transfer evaluation can transfer at most Rs 50,000 that day.
   - An account opened at least 30×24 hours before transfer evaluation can transfer at most Rs 1,00,000 that day.
   - The age threshold is based on elapsed time from the account opening timestamp. Exactly 30×24 hours qualifies for the Rs 1,00,000 limit.
   - Transfers from other accounts, even accounts owned by the same customer, do not count toward this account's limit.
4. A customer cannot transfer to the same account.
5. Both accounts must be active.
6. Every transfer gets a unique transaction ID and is saved.
7. The customer should get a quick response.

Examples:

- A sending account 29×24 hours old with Rs 49,000 already transferred today may send Rs 1,000 more; Rs 1,000.01 more is rejected.
- A sending account exactly 30×24 hours old with Rs 99,000 already transferred today may send Rs 1,000 more; a transfer that brings its daily total above Rs 1,00,000 is rejected.
- If one of a customer's accounts has reached its daily limit, a different sending account's separate daily limit is evaluated independently.
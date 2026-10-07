CREATE TABLE customers (
    customer_id VARCHAR(128) PRIMARY KEY
);

CREATE TABLE accounts (
    account_number VARCHAR(64) PRIMARY KEY,
    customer_id VARCHAR(128) NOT NULL REFERENCES customers(customer_id),
    balance NUMERIC(14, 2) NOT NULL CHECK (balance >= 0),
    status VARCHAR(8) NOT NULL CHECK (status IN ('ACTIVE', 'INACTIVE')),
    account_type VARCHAR(32) NOT NULL
);

CREATE INDEX ix_accounts_customer_id ON accounts(customer_id);

CREATE TABLE transactions (
    transaction_id VARCHAR(36) PRIMARY KEY,
    customer_id VARCHAR(128) NOT NULL REFERENCES customers(customer_id),
    request_id VARCHAR(128) NOT NULL,
    from_account VARCHAR(64) NOT NULL REFERENCES accounts(account_number),
    to_account VARCHAR(64) NOT NULL REFERENCES accounts(account_number),
    amount NUMERIC(14, 2) NOT NULL CHECK (amount > 0),
    status VARCHAR(8) NOT NULL CHECK (status = 'ACCEPTED'),
    created_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT uq_transactions_customer_request UNIQUE (customer_id, request_id),
    CONSTRAINT ck_transactions_different_accounts CHECK (from_account <> to_account)
);

CREATE INDEX ix_transactions_customer_created_at
    ON transactions(customer_id, created_at);
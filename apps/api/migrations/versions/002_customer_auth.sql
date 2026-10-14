CREATE TABLE customer_profiles (
    customer_id VARCHAR(128) PRIMARY KEY
        REFERENCES customers(customer_id) ON DELETE CASCADE,
    name TEXT NOT NULL CHECK (length(btrim(name)) > 0),
    email TEXT NOT NULL CHECK (length(btrim(email)) > 0),
    mobile_number TEXT NOT NULL,
    username TEXT NOT NULL CHECK (length(btrim(username)) > 0),
    password_hash TEXT NOT NULL,
    email_verified_at TIMESTAMPTZ,
    mobile_verified_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_customer_profiles_email UNIQUE (email),
    CONSTRAINT uq_customer_profiles_username UNIQUE (username)
);

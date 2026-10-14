CREATE TABLE auth_sessions (
    session_id VARCHAR(36) PRIMARY KEY,
    customer_id VARCHAR(128) NOT NULL REFERENCES customer_profiles(customer_id) ON DELETE CASCADE,
    token_digest CHAR(64) NOT NULL UNIQUE,
    csrf_token_digest CHAR(64) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    last_activity_at TIMESTAMPTZ NOT NULL,
    revoked_at TIMESTAMPTZ,
    CONSTRAINT ck_auth_sessions_activity_after_creation CHECK (last_activity_at >= created_at)
);

CREATE INDEX ix_auth_sessions_customer_id ON auth_sessions(customer_id);

CREATE TABLE auth_challenges (
    challenge_id VARCHAR(36) PRIMARY KEY,
    customer_id VARCHAR(128) NOT NULL REFERENCES customer_profiles(customer_id) ON DELETE CASCADE,
    purpose VARCHAR(32) NOT NULL CHECK (purpose IN ('CONTACT_VERIFICATION', 'PASSWORD_RESET')),
    channel VARCHAR(16) NOT NULL CHECK (channel IN ('email', 'mobile')),
    token_digest CHAR(64) NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    attempt_count INTEGER NOT NULL DEFAULT 0 CHECK (attempt_count BETWEEN 0 AND 5),
    consumed_at TIMESTAMPTZ,
    CONSTRAINT ck_auth_challenges_expiry CHECK (expires_at > created_at)
);

CREATE INDEX ix_auth_challenges_customer_purpose_channel
    ON auth_challenges(customer_id, purpose, channel);

CREATE TABLE login_throttles (
    normalized_username VARCHAR(128) PRIMARY KEY,
    consecutive_failures INTEGER NOT NULL DEFAULT 0 CHECK (consecutive_failures >= 0),
    blocked_until TIMESTAMPTZ,
    updated_at TIMESTAMPTZ NOT NULL
);
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class ContactChannel(StrEnum):
    EMAIL = "email"
    MOBILE = "mobile"


class ChallengePurpose(StrEnum):
    CONTACT_VERIFICATION = "contact_verification"
    PASSWORD_RESET = "password_reset"


@dataclass(frozen=True)
class RegistrationCommand:
    name: str
    email: str
    mobile_number: str
    username: str
    password: str
    account_number_suffix: str


@dataclass(frozen=True)
class CustomerProfileRecord:
    customer_id: str
    name: str
    email: str
    mobile_number: str
    username: str
    password_hash: str
    email_verified_at: datetime | None = None
    mobile_verified_at: datetime | None = None

    @property
    def transfer_eligible(self) -> bool:
        return self.email_verified_at is not None or self.mobile_verified_at is not None


@dataclass(frozen=True)
class RegisteredAccount:
    account_number: str
    account_type: str
    status: str
    balance: str


@dataclass(frozen=True)
class RegistrationResult:
    customer_id: str
    account: RegisteredAccount
    transfer_eligible: bool


@dataclass(frozen=True)
class ContactVerificationResult:
    customer_id: str
    channel: ContactChannel
    transfer_eligible: bool


@dataclass(frozen=True)
class AuthSessionRecord:
    session_id: str
    customer_id: str
    token_digest: str
    csrf_token_digest: str
    created_at: datetime
    last_activity_at: datetime
    revoked_at: datetime | None = None


@dataclass(frozen=True)
class SessionGrant:
    session_id: str
    customer_id: str
    session_token: str
    csrf_token: str
    expires_at: datetime


@dataclass(frozen=True)
class AuthenticatedPrincipal:
    customer_id: str
    session_id: str
    display_name: str
    email_verified: bool
    mobile_verified: bool
    csrf_token_digest: str

    @property
    def transfer_eligible(self) -> bool:
        return self.email_verified or self.mobile_verified


@dataclass(frozen=True)
class ChallengeRecord:
    challenge_id: str
    customer_id: str
    purpose: ChallengePurpose
    channel: ContactChannel
    token_digest: str
    created_at: datetime
    expires_at: datetime
    attempt_count: int = 0
    consumed_at: datetime | None = None


@dataclass(frozen=True)
class LoginThrottleState:
    normalized_username: str
    consecutive_failures: int
    blocked_until: datetime | None
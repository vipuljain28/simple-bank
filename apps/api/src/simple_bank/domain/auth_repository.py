from datetime import datetime
from typing import Protocol

from simple_bank.domain.auth import (
    AuthenticatedPrincipal,
    AuthSessionRecord,
    ChallengePurpose,
    ChallengeRecord,
    ContactChannel,
    CustomerProfileRecord,
    LoginThrottleState,
    RegistrationResult,
)


class AuthRepository(Protocol):
    def register_customer(
        self,
        profile: CustomerProfileRecord,
        account_number: str,
        *,
        created_at: datetime,
    ) -> RegistrationResult: ...

    def get_profile_by_username(self, normalized_username: str) -> CustomerProfileRecord | None: ...

    def get_profile_by_id(self, customer_id: str) -> CustomerProfileRecord | None: ...

    def create_session(self, session: AuthSessionRecord) -> None: ...

    def resolve_session(self, token_digest: str, now: datetime) -> AuthenticatedPrincipal | None: ...

    def touch_session(self, session_id: str, now: datetime) -> None: ...

    def update_session_csrf_digest(self, session_id: str, token_digest: str) -> None: ...

    def revoke_session(self, session_id: str, now: datetime) -> None: ...

    def revoke_customer_sessions(self, customer_id: str, now: datetime) -> None: ...

    def get_login_throttle(self, normalized_username: str) -> LoginThrottleState | None: ...

    def record_login_failure(
        self, normalized_username: str, now: datetime, *, threshold: int, cooldown_seconds: int
    ) -> LoginThrottleState: ...

    def clear_login_throttle(self, normalized_username: str) -> None: ...

    def create_challenge(self, challenge: ChallengeRecord) -> None: ...

    def get_challenge(self, token_digest: str, purpose: ChallengePurpose) -> ChallengeRecord | None: ...

    def find_active_challenge(
        self,
        customer_id: str,
        purpose: ChallengePurpose,
        channel: ContactChannel,
    ) -> ChallengeRecord | None: ...

    def record_challenge_failure(self, challenge_id: str) -> int: ...

    def consume_challenge(self, challenge_id: str, now: datetime) -> None: ...

    def mark_contact_verified(
        self, customer_id: str, channel: ContactChannel, now: datetime
    ) -> None: ...

    def set_password_hash(self, customer_id: str, password_hash: str) -> None: ...
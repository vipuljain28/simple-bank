from collections.abc import Callable, Iterator
from contextlib import contextmanager
from copy import deepcopy
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from threading import RLock

import pytest

from simple_bank.domain.transfer_repository import AccountSnapshot
from simple_bank.domain.transfers import TransferRecord
from simple_bank.domain.auth_errors import RegistrationConflict
from simple_bank.domain.auth import (
    AuthenticatedPrincipal,
    AuthSessionRecord,
    ChallengePurpose,
    ChallengeRecord,
    ContactChannel,
    CustomerProfileRecord,
    LoginThrottleState,
    RegisteredAccount,
    RegistrationResult,
)


class MemoryTransferRepository:
    def __init__(self) -> None:
        self.accounts = {
            "000000001001": AccountSnapshot(
                "000000001001", "customer-001", Decimal("500.00"), "ACTIVE", "SAVINGS"
            ),
            "000000002002": AccountSnapshot(
                "000000002002", "customer-002", Decimal("100.00"), "ACTIVE", "CURRENT"
            ),
        }
        self.transfers: dict[tuple[str, str], TransferRecord] = {}
        self._lock = RLock()

    @contextmanager
    def transaction(
        self, customer_id: str, account_numbers: tuple[str, str]
    ) -> Iterator["MemoryTransferRepository"]:
        with self._lock:
            previous_accounts = deepcopy(self.accounts)
            previous_transfers = deepcopy(self.transfers)
            try:
                yield self
            except Exception:
                self.accounts = previous_accounts
                self.transfers = previous_transfers
                raise

    def find_transfer(self, customer_id: str, request_id: str) -> TransferRecord | None:
        return self.transfers.get((customer_id, request_id))

    def get_account(self, account_number: str) -> AccountSnapshot | None:
        return self.accounts.get(account_number)

    def get_daily_total(self, customer_id: str, start: datetime, end: datetime) -> Decimal:
        return sum(
            (
                transfer.amount
                for transfer in self.transfers.values()
                if transfer.customer_id == customer_id and start <= transfer.created_at < end
            ),
            Decimal("0.00"),
        )

    def save_transfer(self, transfer: TransferRecord) -> None:
        sender = self.accounts[transfer.from_account]
        recipient = self.accounts[transfer.to_account]
        self.accounts[transfer.from_account] = AccountSnapshot(
            sender.account_number,
            sender.customer_id,
            sender.balance - transfer.amount,
            sender.status,
            sender.account_type,
        )
        self.accounts[transfer.to_account] = AccountSnapshot(
            recipient.account_number,
            recipient.customer_id,
            recipient.balance + transfer.amount,
            recipient.status,
            recipient.account_type,
        )
        self.transfers[(transfer.customer_id, transfer.request_id)] = transfer

class SyntheticTransferVerifier:
    def __init__(self, expected: tuple[str, str, str, str, Decimal]):
        self.expected = expected
        self.calls: list[tuple[str, str, str, str, Decimal]] = []

    def verify(
        self,
        *,
        customer_id: str,
        request_id: str,
        from_account: str,
        to_account: str,
        amount: Decimal,
        proof: str,
    ) -> bool:
        claim = (customer_id, request_id, from_account, to_account, amount)
        self.calls.append(claim)
        return proof == "synthetic-verification-proof" and claim == self.expected


@pytest.fixture
def verifier_factory() -> Callable[..., SyntheticTransferVerifier]:
    def create(
        *,
        customer_id: str,
        request_id: str,
        from_account: str,
        to_account: str,
        amount: Decimal,
    ) -> SyntheticTransferVerifier:
        return SyntheticTransferVerifier(
            (customer_id, request_id, from_account, to_account, amount)
        )

    return create


@pytest.fixture
def transfer_repository() -> MemoryTransferRepository:
    return MemoryTransferRepository()


class FrozenClock:
    def __init__(self, now: datetime | None = None) -> None:
        self.current = now or datetime(2026, 10, 12, 12, tzinfo=UTC)

    def __call__(self) -> datetime:
        return self.current

    def advance(self, **delta: int) -> None:
        self.current += timedelta(**delta)


class RecordingContactDelivery:
    def __init__(self) -> None:
        self.sent: list[tuple[ContactChannel, str, str]] = []

    def send_code(self, channel: ContactChannel, destination: str, code: str) -> None:
        self.sent.append((channel, destination, code))


class MemoryAuthRepository:
    def __init__(self) -> None:
        self.profiles: dict[str, CustomerProfileRecord] = {}
        self.usernames: dict[str, str] = {}
        self.emails: dict[str, str] = {}
        self.accounts: dict[str, RegistrationResult] = {}
        self.sessions: dict[str, AuthSessionRecord] = {}
        self.challenges: dict[str, ChallengeRecord] = {}
        self.throttles: dict[str, LoginThrottleState] = {}
        self._lock = RLock()

    def register_customer(
        self,
        profile: CustomerProfileRecord,
        account_number: str,
        *,
        created_at: datetime,
    ) -> RegistrationResult:
        with self._lock:
            if (
                profile.username in self.usernames
                or profile.email in self.emails
                or account_number in self.accounts
            ):
                raise RegistrationConflict()
            account = RegistrationResult(
                customer_id=profile.customer_id,
                account=RegisteredAccount(
                    account_number=account_number,
                    account_type="SAVINGS",
                    status="ACTIVE",
                    balance="0.00",
                ),
                transfer_eligible=False,
            )
            self.profiles[profile.customer_id] = profile
            self.usernames[profile.username] = profile.customer_id
            self.emails[profile.email] = profile.customer_id
            self.accounts[account_number] = account
            return account

    def get_profile_by_username(self, normalized_username: str) -> CustomerProfileRecord | None:
        customer_id = self.usernames.get(normalized_username)
        return self.profiles.get(customer_id) if customer_id else None

    def get_profile_by_id(self, customer_id: str) -> CustomerProfileRecord | None:
        return self.profiles.get(customer_id)

    def create_session(self, session: AuthSessionRecord) -> None:
        self.sessions[session.session_id] = session

    def resolve_session(self, token_digest: str, now: datetime) -> AuthenticatedPrincipal | None:
        session = next(
            (
                value
                for value in self.sessions.values()
                if value.token_digest == token_digest and value.revoked_at is None
            ),
            None,
        )
        if session is None:
            return None
        if (
            now - session.last_activity_at >= timedelta(minutes=5)
            or now - session.created_at >= timedelta(hours=1)
        ):
            return None
        from dataclasses import replace

        self.sessions[session.session_id] = replace(session, last_activity_at=now)
        profile = self.profiles.get(session.customer_id)
        if profile is None:
            return None
        return AuthenticatedPrincipal(
            customer_id=profile.customer_id,
            session_id=session.session_id,
            display_name=profile.name,
            email_verified=profile.email_verified_at is not None,
            mobile_verified=profile.mobile_verified_at is not None,
            csrf_token_digest=session.csrf_token_digest,
        )

    def touch_session(self, session_id: str, now: datetime) -> None:
        from dataclasses import replace

        session = self.sessions[session_id]
        self.sessions[session_id] = replace(session, last_activity_at=now)

    def update_session_csrf_digest(self, session_id: str, token_digest: str) -> None:
        from dataclasses import replace

        session = self.sessions[session_id]
        self.sessions[session_id] = replace(session, csrf_token_digest=token_digest)

    def revoke_session(self, session_id: str, now: datetime) -> None:
        from dataclasses import replace

        if session_id in self.sessions:
            self.sessions[session_id] = replace(self.sessions[session_id], revoked_at=now)

    def revoke_customer_sessions(self, customer_id: str, now: datetime) -> None:
        for session in tuple(self.sessions.values()):
            if session.customer_id == customer_id:
                self.revoke_session(session.session_id, now)

    def get_login_throttle(self, normalized_username: str) -> LoginThrottleState | None:
        return self.throttles.get(normalized_username)

    def record_login_failure(
        self,
        normalized_username: str,
        now: datetime,
        *,
        threshold: int,
        cooldown_seconds: int,
    ) -> LoginThrottleState:
        previous = self.throttles.get(normalized_username)
        failures = 1 if previous is None else previous.consecutive_failures + 1
        blocked_until = (
            now + timedelta(seconds=cooldown_seconds) if failures >= threshold else None
        )
        state = LoginThrottleState(normalized_username, failures, blocked_until)
        self.throttles[normalized_username] = state
        return state

    def clear_login_throttle(self, normalized_username: str) -> None:
        self.throttles.pop(normalized_username, None)

    def create_challenge(self, challenge: ChallengeRecord) -> None:
        self.challenges[challenge.challenge_id] = challenge

    def get_challenge(
        self, token_digest: str, purpose: ChallengePurpose
    ) -> ChallengeRecord | None:
        return next(
            (
                item
                for item in self.challenges.values()
                if item.token_digest == token_digest and item.purpose == purpose
            ),
            None,
        )

    def find_active_challenge(
        self,
        customer_id: str,
        purpose: ChallengePurpose,
        channel: ContactChannel,
    ) -> ChallengeRecord | None:
        matches = [
            item
            for item in self.challenges.values()
            if item.customer_id == customer_id
            and item.purpose == purpose
            and item.channel == channel
            and item.consumed_at is None
        ]
        return max(matches, key=lambda item: item.created_at) if matches else None

    def record_challenge_failure(self, challenge_id: str) -> int:
        from dataclasses import replace

        challenge = self.challenges[challenge_id]
        failures = challenge.attempt_count + 1
        self.challenges[challenge_id] = replace(challenge, attempt_count=failures)
        return failures

    def consume_challenge(self, challenge_id: str, now: datetime) -> None:
        from dataclasses import replace

        self.challenges[challenge_id] = replace(
            self.challenges[challenge_id], consumed_at=now
        )

    def mark_contact_verified(
        self, customer_id: str, channel: ContactChannel, now: datetime
    ) -> None:
        from dataclasses import replace

        profile = self.profiles[customer_id]
        field_name = "email_verified_at" if channel == ContactChannel.EMAIL else "mobile_verified_at"
        self.profiles[customer_id] = replace(profile, **{field_name: now})

    def set_password_hash(self, customer_id: str, password_hash: str) -> None:
        from dataclasses import replace

        self.profiles[customer_id] = replace(
            self.profiles[customer_id], password_hash=password_hash
        )


@pytest.fixture
def auth_repository() -> MemoryAuthRepository:
    return MemoryAuthRepository()


@pytest.fixture
def contact_delivery() -> RecordingContactDelivery:
    return RecordingContactDelivery()


@pytest.fixture
def frozen_clock() -> FrozenClock:
    return FrozenClock()
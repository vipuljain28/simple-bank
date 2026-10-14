from datetime import datetime
from decimal import Decimal

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

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
from simple_bank.domain.auth_errors import RegistrationConflict
from simple_bank.persistence.models import (
    Account,
    AuthChallenge,
    AuthSession,
    Customer,
    CustomerProfile,
    LoginThrottle,
)


class SqlAlchemyAuthRepository:
    def __init__(self, session_factory: sessionmaker[Session]):
        self._session_factory = session_factory

    def register_customer(
        self,
        profile: CustomerProfileRecord,
        account_number: str,
        *,
        created_at: datetime,
    ) -> RegistrationResult:
        try:
            with self._session_factory.begin() as session:
                session.add(Customer(customer_id=profile.customer_id))
                session.flush()
                session.add(
                    CustomerProfile(
                        customer_id=profile.customer_id,
                        name=profile.name,
                        email=profile.email,
                        mobile_number=profile.mobile_number,
                        username=profile.username,
                        password_hash=profile.password_hash,
                        email_verified_at=profile.email_verified_at,
                        mobile_verified_at=profile.mobile_verified_at,
                        created_at=created_at,
                    )
                )
                session.add(
                    Account(
                        account_number=account_number,
                        customer_id=profile.customer_id,
                        balance=Decimal("0.00"),
                        status="ACTIVE",
                        account_type="SAVINGS",
                    )
                )
                session.flush()
        except IntegrityError as error:
            raise RegistrationConflict() from error

        return RegistrationResult(
            customer_id=profile.customer_id,
            account=RegisteredAccount(
                account_number=account_number,
                account_type="SAVINGS",
                status="ACTIVE",
                balance="0.00",
            ),
            transfer_eligible=profile.transfer_eligible,
        )

    def get_profile_by_username(self, normalized_username: str) -> CustomerProfileRecord | None:
        with self._session_factory() as session:
            row = session.scalar(
                select(CustomerProfile).where(CustomerProfile.username == normalized_username)
            )
            return self._profile_record(row) if row is not None else None

    def get_profile_by_id(self, customer_id: str) -> CustomerProfileRecord | None:
        with self._session_factory() as session:
            row = session.get(CustomerProfile, customer_id)
            return self._profile_record(row) if row is not None else None

    def create_session(self, auth_session: AuthSessionRecord) -> None:
        with self._session_factory.begin() as session:
            session.add(
                AuthSession(
                    session_id=auth_session.session_id,
                    customer_id=auth_session.customer_id,
                    token_digest=auth_session.token_digest,
                    csrf_token_digest=auth_session.csrf_token_digest,
                    created_at=auth_session.created_at,
                    last_activity_at=auth_session.last_activity_at,
                    revoked_at=auth_session.revoked_at,
                )
            )

    def resolve_session(self, token_digest: str, now: datetime) -> AuthenticatedPrincipal | None:
        with self._session_factory.begin() as session:
            result = session.execute(
                select(AuthSession, CustomerProfile)
                .join(CustomerProfile, CustomerProfile.customer_id == AuthSession.customer_id)
                .where(
                    AuthSession.token_digest == token_digest,
                    AuthSession.revoked_at.is_(None),
                )
                .with_for_update()
            ).first()
            if result is None:
                return None
            auth_session, profile = result
            if (
                (now - auth_session.last_activity_at).total_seconds() >= 300
                or (now - auth_session.created_at).total_seconds() >= 3600
            ):
                auth_session.revoked_at = now
                return None
            auth_session.last_activity_at = now
            return AuthenticatedPrincipal(
                customer_id=profile.customer_id,
                session_id=auth_session.session_id,
                display_name=profile.name,
                email_verified=profile.email_verified_at is not None,
                mobile_verified=profile.mobile_verified_at is not None,
                csrf_token_digest=auth_session.csrf_token_digest,
            )

    def touch_session(self, session_id: str, now: datetime) -> None:
        with self._session_factory.begin() as session:
            row = session.scalar(
                select(AuthSession).where(AuthSession.session_id == session_id).with_for_update()
            )
            if row is not None and row.revoked_at is None:
                row.last_activity_at = now

    def update_session_csrf_digest(self, session_id: str, token_digest: str) -> None:
        with self._session_factory.begin() as session:
            row = session.scalar(
                select(AuthSession).where(AuthSession.session_id == session_id).with_for_update()
            )
            if row is not None and row.revoked_at is None:
                row.csrf_token_digest = token_digest

    def update_session_csrf_digest(self, session_id: str, token_digest: str) -> None:
        with self._session_factory.begin() as session:
            row = session.scalar(
                select(AuthSession).where(AuthSession.session_id == session_id).with_for_update()
            )
            if row is not None and row.revoked_at is None:
                row.csrf_token_digest = token_digest

    def revoke_session(self, session_id: str, now: datetime) -> None:
        with self._session_factory.begin() as session:
            session.execute(
                update(AuthSession)
                .where(AuthSession.session_id == session_id, AuthSession.revoked_at.is_(None))
                .values(revoked_at=now)
            )

    def revoke_customer_sessions(self, customer_id: str, now: datetime) -> None:
        with self._session_factory.begin() as session:
            session.execute(
                update(AuthSession)
                .where(AuthSession.customer_id == customer_id, AuthSession.revoked_at.is_(None))
                .values(revoked_at=now)
            )

    def get_login_throttle(self, normalized_username: str) -> LoginThrottleState | None:
        with self._session_factory() as session:
            row = session.get(LoginThrottle, normalized_username)
            return self._throttle_record(row) if row is not None else None

    def record_login_failure(
        self,
        normalized_username: str,
        now: datetime,
        *,
        threshold: int,
        cooldown_seconds: int,
    ) -> LoginThrottleState:
        from datetime import timedelta

        with self._session_factory.begin() as session:
            row = session.scalar(
                select(LoginThrottle)
                .where(LoginThrottle.normalized_username == normalized_username)
                .with_for_update()
            )
            if row is None:
                row = LoginThrottle(
                    normalized_username=normalized_username,
                    consecutive_failures=0,
                    updated_at=now,
                )
                session.add(row)
                session.flush()
            if row.blocked_until is not None and now >= row.blocked_until:
                row.consecutive_failures = 0
                row.blocked_until = None
            row.consecutive_failures += 1
            row.updated_at = now
            if row.consecutive_failures >= threshold:
                row.blocked_until = now + timedelta(seconds=cooldown_seconds)
            session.flush()
            return self._throttle_record(row)

    def clear_login_throttle(self, normalized_username: str) -> None:
        with self._session_factory.begin() as session:
            row = session.get(LoginThrottle, normalized_username)
            if row is not None:
                session.delete(row)

    def create_challenge(self, challenge: ChallengeRecord) -> None:
        with self._session_factory.begin() as session:
            session.add(
                AuthChallenge(
                    challenge_id=challenge.challenge_id,
                    customer_id=challenge.customer_id,
                    purpose=challenge.purpose.name,
                    channel=challenge.channel.value,
                    token_digest=challenge.token_digest,
                    created_at=challenge.created_at,
                    expires_at=challenge.expires_at,
                    attempt_count=challenge.attempt_count,
                    consumed_at=challenge.consumed_at,
                )
            )

    def get_challenge(
        self, token_digest: str, purpose: ChallengePurpose
    ) -> ChallengeRecord | None:
        with self._session_factory() as session:
            row = session.scalar(
                select(AuthChallenge).where(
                    AuthChallenge.token_digest == token_digest,
                    AuthChallenge.purpose == purpose.name,
                )
            )
            return self._challenge_record(row) if row is not None else None

    def find_active_challenge(
        self,
        customer_id: str,
        purpose: ChallengePurpose,
        channel: ContactChannel,
    ) -> ChallengeRecord | None:
        with self._session_factory() as session:
            row = session.scalar(
                select(AuthChallenge)
                .where(
                    AuthChallenge.customer_id == customer_id,
                    AuthChallenge.purpose == purpose.name,
                    AuthChallenge.channel == channel.value,
                    AuthChallenge.consumed_at.is_(None),
                )
                .order_by(AuthChallenge.created_at.desc())
                .limit(1)
            )
            return self._challenge_record(row) if row is not None else None

    def record_challenge_failure(self, challenge_id: str) -> int:
        with self._session_factory.begin() as session:
            row = session.scalar(
                select(AuthChallenge)
                .where(AuthChallenge.challenge_id == challenge_id)
                .with_for_update()
            )
            if row is None:
                return 5
            row.attempt_count = min(row.attempt_count + 1, 5)
            session.flush()
            return row.attempt_count

    def consume_challenge(self, challenge_id: str, now: datetime) -> None:
        with self._session_factory.begin() as session:
            row = session.scalar(
                select(AuthChallenge)
                .where(AuthChallenge.challenge_id == challenge_id)
                .with_for_update()
            )
            if row is not None and row.consumed_at is None:
                row.consumed_at = now

    def mark_contact_verified(
        self, customer_id: str, channel: ContactChannel, now: datetime
    ) -> None:
        with self._session_factory.begin() as session:
            row = session.scalar(
                select(CustomerProfile)
                .where(CustomerProfile.customer_id == customer_id)
                .with_for_update()
            )
            if row is not None:
                if channel == ContactChannel.EMAIL:
                    row.email_verified_at = now
                else:
                    row.mobile_verified_at = now

    def set_password_hash(self, customer_id: str, password_hash: str) -> None:
        with self._session_factory.begin() as session:
            row = session.scalar(
                select(CustomerProfile)
                .where(CustomerProfile.customer_id == customer_id)
                .with_for_update()
            )
            if row is not None:
                row.password_hash = password_hash

    @staticmethod
    def _profile_record(row: CustomerProfile) -> CustomerProfileRecord:
        return CustomerProfileRecord(
            customer_id=row.customer_id,
            name=row.name,
            email=row.email,
            mobile_number=row.mobile_number,
            username=row.username,
            password_hash=row.password_hash,
            email_verified_at=row.email_verified_at,
            mobile_verified_at=row.mobile_verified_at,
        )

    @staticmethod
    def _challenge_record(row: AuthChallenge) -> ChallengeRecord:
        return ChallengeRecord(
            challenge_id=row.challenge_id,
            customer_id=row.customer_id,
            purpose=ChallengePurpose[row.purpose],
            channel=ContactChannel(row.channel),
            token_digest=row.token_digest,
            created_at=row.created_at,
            expires_at=row.expires_at,
            attempt_count=row.attempt_count,
            consumed_at=row.consumed_at,
        )

    @staticmethod
    def _throttle_record(row: LoginThrottle) -> LoginThrottleState:
        return LoginThrottleState(
            normalized_username=row.normalized_username,
            consecutive_failures=row.consecutive_failures,
            blocked_until=row.blocked_until,
        )
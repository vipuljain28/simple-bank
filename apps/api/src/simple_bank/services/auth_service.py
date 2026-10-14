from collections.abc import Callable
from datetime import UTC, datetime, timedelta
import hashlib
import hmac
import re
import secrets
from uuid import uuid4

import phonenumbers
from argon2 import PasswordHasher
from argon2.exceptions import HashingError, VerificationError

from simple_bank.domain.auth import (
    AuthSessionRecord,
    ChallengePurpose,
    ChallengeRecord,
    ContactChannel,
    ContactVerificationResult,
    CustomerProfileRecord,
    RegistrationCommand,
    RegistrationResult,
    SessionGrant,
)
from simple_bank.domain.auth_errors import (
    ContactDeliveryUnavailable,
    InvalidCredentials,
    InvalidOrExpiredChallenge,
    InvalidRegistration,
    LoginTemporarilyThrottled,
)
from simple_bank.domain.auth_repository import AuthRepository
from simple_bank.security.contact_delivery import ContactDelivery
from simple_bank.settings import Settings


_ACCOUNT_SUFFIX = re.compile(r"[0-9]{10}\Z", re.ASCII)
_EMAIL = re.compile(
    r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@"
    r"(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+[A-Za-z]{2,63}\Z",
    re.ASCII,
)


class CustomerAuthService:
    def __init__(
        self,
        repository: AuthRepository,
        contact_delivery: ContactDelivery,
        *,
        settings: Settings,
        clock: Callable[[], datetime] | None = None,
        password_hasher: PasswordHasher | None = None,
    ) -> None:
        self._repository = repository
        self._contact_delivery = contact_delivery
        self._settings = settings
        self._clock = clock or (lambda: datetime.now(UTC))
        self._password_hasher = password_hasher or PasswordHasher()
        self._dummy_password_hash = self._password_hasher.hash(
            "synthetic-dummy-password-never-used"
        )

    def register(self, command: RegistrationCommand) -> RegistrationResult:
        name = command.name.strip()
        email = self._normalize_email(command.email)
        username = command.username.strip().casefold()
        mobile_number = self._normalize_mobile(command.mobile_number)
        suffix = command.account_number_suffix
        password = command.password

        if not name or len(name) > 200:
            raise InvalidRegistration()
        if not username or len(username) > 128:
            raise InvalidRegistration()
        if len(password) < 12 or len(password) > 128:
            raise InvalidRegistration()
        if not _ACCOUNT_SUFFIX.fullmatch(suffix):
            raise InvalidRegistration()

        now = self._clock()
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("The authentication clock must return a timezone-aware datetime.")
        try:
            password_hash = self._password_hasher.hash(password)
        except HashingError as error:
            raise RuntimeError("Password hashing failed.") from error

        profile = CustomerProfileRecord(
            customer_id=str(uuid4()),
            name=name,
            email=email,
            mobile_number=mobile_number,
            username=username,
            password_hash=password_hash,
        )
        return self._repository.register_customer(
            profile,
            f"1991{suffix}",
            created_at=now.astimezone(UTC),
        )

    def profile_for_customer(self, customer_id: str) -> CustomerProfileRecord:
        profile = self._repository.get_profile_by_id(customer_id)
        if profile is None:
            raise InvalidCredentials()
        return profile

    def login(self, username: str, password: str) -> SessionGrant:
        normalized_username = username.strip().casefold()
        now = self._now()
        throttle = self._repository.get_login_throttle(normalized_username)
        if throttle is not None and throttle.blocked_until is not None:
            if now < throttle.blocked_until:
                raise LoginTemporarilyThrottled()
            self._repository.clear_login_throttle(normalized_username)

        profile = self._repository.get_profile_by_username(normalized_username)
        candidate_hash = profile.password_hash if profile is not None else self._dummy_password_hash
        try:
            password_matches = self._password_hasher.verify(candidate_hash, password)
        except VerificationError:
            password_matches = False

        if profile is None or not password_matches:
            self._repository.record_login_failure(
                normalized_username, now, threshold=5, cooldown_seconds=900
            )
            raise InvalidCredentials()

        self._repository.clear_login_throttle(normalized_username)
        session_token = secrets.token_urlsafe(32)
        csrf_token = secrets.token_urlsafe(32)
        session = AuthSessionRecord(
            session_id=str(uuid4()),
            customer_id=profile.customer_id,
            token_digest=self._token_digest(session_token),
            csrf_token_digest=self._token_digest(csrf_token),
            created_at=now,
            last_activity_at=now,
        )
        self._repository.create_session(session)
        return SessionGrant(
            session_id=session.session_id,
            customer_id=session.customer_id,
            session_token=session_token,
            csrf_token=csrf_token,
            expires_at=min(
                now + timedelta(seconds=self._settings.session_idle_timeout_seconds),
                now + timedelta(seconds=self._settings.session_max_age_seconds),
            ),
        )

    def logout(self, session_id: str) -> None:
        self._repository.revoke_session(session_id, self._now())

    def request_contact_verification(
        self, customer_id: str, channel: ContactChannel
    ) -> None:
        profile = self._repository.get_profile_by_id(customer_id)
        if profile is None:
            raise InvalidOrExpiredChallenge()
        if channel == ContactChannel.EMAIL:
            destination = profile.email
        elif channel == ContactChannel.MOBILE:
            destination = profile.mobile_number
        else:
            raise InvalidOrExpiredChallenge()
        self._create_and_deliver_challenge(
            customer_id,
            channel,
            ChallengePurpose.CONTACT_VERIFICATION,
            destination,
            expires_in=timedelta(minutes=10),
        )

    def confirm_contact_verification(
        self, customer_id: str, channel: ContactChannel, code: str
    ) -> ContactVerificationResult:
        now = self._now()
        challenge = self._repository.find_active_challenge(
            customer_id, ChallengePurpose.CONTACT_VERIFICATION, channel
        )
        if not self._challenge_is_usable(challenge, now):
            raise InvalidOrExpiredChallenge()
        assert challenge is not None
        if not hmac.compare_digest(challenge.token_digest, self._challenge_digest(code)):
            attempts = self._repository.record_challenge_failure(challenge.challenge_id)
            if attempts >= 5:
                self._repository.consume_challenge(challenge.challenge_id, now)
            raise InvalidOrExpiredChallenge()
        self._repository.consume_challenge(challenge.challenge_id, now)
        self._repository.mark_contact_verified(customer_id, channel, now)
        profile = self._repository.get_profile_by_id(customer_id)
        if profile is None:
            raise InvalidOrExpiredChallenge()
        return ContactVerificationResult(
            customer_id=customer_id,
            channel=channel,
            transfer_eligible=profile.transfer_eligible,
        )

    def request_password_reset(self, username: str, channel: ContactChannel) -> None:
        profile = self._repository.get_profile_by_username(username.strip().casefold())
        if profile is None:
            raise InvalidOrExpiredChallenge()
        if channel == ContactChannel.EMAIL and profile.email_verified_at is not None:
            destination = profile.email
        elif channel == ContactChannel.MOBILE and profile.mobile_verified_at is not None:
            destination = profile.mobile_number
        else:
            raise InvalidOrExpiredChallenge()
        self._create_and_deliver_challenge(
            profile.customer_id,
            channel,
            ChallengePurpose.PASSWORD_RESET,
            destination,
            expires_in=timedelta(minutes=15),
        )

    def confirm_password_reset(self, code: str, new_password: str) -> None:
        now = self._now()
        if len(new_password) < 12 or len(new_password) > 128:
            raise InvalidRegistration()
        challenge = self._repository.get_challenge(
            self._challenge_digest(code), ChallengePurpose.PASSWORD_RESET
        )
        if not self._challenge_is_usable(challenge, now):
            raise InvalidOrExpiredChallenge()
        assert challenge is not None
        self._repository.consume_challenge(challenge.challenge_id, now)
        self._repository.set_password_hash(
            challenge.customer_id, self._password_hasher.hash(new_password)
        )
        profile = self._repository.get_profile_by_id(challenge.customer_id)
        if profile is not None:
            self._repository.clear_login_throttle(profile.username)
        self._repository.revoke_customer_sessions(challenge.customer_id, now)

    def _create_and_deliver_challenge(
        self,
        customer_id: str,
        channel: ContactChannel,
        purpose: ChallengePurpose,
        destination: str,
        *,
        expires_in: timedelta,
    ) -> None:
        pepper = self._settings.auth_code_pepper
        if not pepper:
            raise ContactDeliveryUnavailable()
        now = self._now()
        mock_email_verification = (
            self._settings.mock_contact_verification
            and channel == ContactChannel.EMAIL
            and purpose == ChallengePurpose.CONTACT_VERIFICATION
        )
        code = "1234" if mock_email_verification else f"{secrets.randbelow(1_000_000):06d}"
        challenge = ChallengeRecord(
            challenge_id=str(uuid4()),
            customer_id=customer_id,
            purpose=purpose,
            channel=channel,
            token_digest=self._challenge_digest(code),
            created_at=now,
            expires_at=now + expires_in,
        )
        if not mock_email_verification:
            try:
                self._contact_delivery.send_code(channel, destination, code)
            except Exception as error:
                raise ContactDeliveryUnavailable() from error
        self._repository.create_challenge(challenge)

    @staticmethod
    def _token_digest(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def _challenge_digest(self, code: str) -> str:
        pepper = self._settings.auth_code_pepper
        if not pepper:
            raise ContactDeliveryUnavailable()
        return hmac.new(pepper.encode("utf-8"), code.encode("utf-8"), hashlib.sha256).hexdigest()

    def _now(self) -> datetime:
        now = self._clock()
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("The authentication clock must return a timezone-aware datetime.")
        return now.astimezone(UTC)

    @staticmethod
    def _challenge_is_usable(challenge: ChallengeRecord | None, now: datetime) -> bool:
        return bool(
            challenge is not None
            and challenge.consumed_at is None
            and challenge.attempt_count < 5
            and now < challenge.expires_at
        )

    @staticmethod
    def _normalize_email(value: str) -> str:
        normalized = value.strip().casefold()
        if len(normalized) > 254 or not _EMAIL.fullmatch(normalized):
            raise InvalidRegistration()
        return normalized

    @staticmethod
    def _normalize_mobile(value: str) -> str:
        candidate = value.strip()
        try:
            number = phonenumbers.parse(candidate, None)
        except phonenumbers.NumberParseException as error:
            raise InvalidRegistration() from error
        if not phonenumbers.is_valid_number(number):
            raise InvalidRegistration()
        return phonenumbers.format_number(number, phonenumbers.PhoneNumberFormat.E164)
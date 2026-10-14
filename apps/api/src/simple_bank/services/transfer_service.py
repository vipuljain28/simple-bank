from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4
from zoneinfo import ZoneInfo

from simple_bank.config.minimum_balance import get_min_balance_threshold
from simple_bank.domain.errors import (
    AccountInactive,
    DailyLimitExceeded,
    Forbidden,
    InsufficientBalance,
    InvalidAmount,
    MinimumBalanceRequired,
    RequestIdConflict,
    SameAccount,
    VerificationRequired,
)
from simple_bank.domain.transfer_repository import TransferRepository
from simple_bank.domain.transfers import TransferCommand, TransferRecord
from simple_bank.security.verification import TransferVerifier
from simple_bank.settings import Settings


_INDIA = ZoneInfo("Asia/Kolkata")
_DAILY_LIMIT = Decimal("100000.00")


class TransferService:
    def __init__(
        self,
        repository: TransferRepository,
        verifier: TransferVerifier,
        *,
        settings: Settings | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._repository = repository
        self._verifier = verifier
        self._settings = settings or Settings.from_environment()
        self._clock = clock or (lambda: datetime.now(UTC))

    def execute(self, customer_id: str, command: TransferCommand) -> TransferRecord:
        with self._repository.transaction(
            customer_id, (command.from_account, command.to_account)
        ) as unit_of_work:
            previous = unit_of_work.find_transfer(customer_id, command.request_id)
            if previous is not None:
                if (
                    previous.from_account != command.from_account
                    or previous.to_account != command.to_account
                    or previous.amount != command.amount
                ):
                    raise RequestIdConflict()
                return previous

            self._validate_amount(command.amount)
            sender = unit_of_work.get_account(command.from_account)
            if (
                sender is None
                or sender.customer_id != customer_id
                or sender.account_type != "SAVINGS"
            ):
                raise Forbidden()
            if command.from_account == command.to_account:
                raise SameAccount()

            recipient = unit_of_work.get_account(command.to_account)
            if (
                sender.status != "ACTIVE"
                or recipient is None
                or recipient.status != "ACTIVE"
            ):
                raise AccountInactive()
            if sender.balance < command.amount:
                raise InsufficientBalance()

            min_balance_threshold = get_min_balance_threshold(self._settings)
            from simple_bank.services.minimum_balance_service import is_balance_valid
            if not is_balance_valid(sender.balance, command.amount, min_balance_threshold):
                raise MinimumBalanceRequired()

            now = self._clock()
            if now.tzinfo is None or now.utcoffset() is None:
                raise ValueError("The transfer clock must return a timezone-aware datetime.")
            local_now = now.astimezone(_INDIA)
            day_start = local_now.replace(hour=0, minute=0, second=0, microsecond=0)
            start_utc = day_start.astimezone(UTC)
            end_utc = (day_start + timedelta(days=1)).astimezone(UTC)
            daily_total = unit_of_work.get_daily_total(
                customer_id, start_utc, end_utc
            )
            if daily_total + command.amount > _DAILY_LIMIT:
                raise DailyLimitExceeded()

            if not self._verifier.verify(
                customer_id=customer_id,
                request_id=command.request_id,
                from_account=command.from_account,
                to_account=command.to_account,
                amount=command.amount,
                proof=command.verification_proof,
            ):
                raise VerificationRequired()

            record = TransferRecord(
                transaction_id=str(uuid4()),
                customer_id=customer_id,
                request_id=command.request_id,
                from_account=command.from_account,
                to_account=command.to_account,
                amount=command.amount,
                status="ACCEPTED",
                created_at=now.astimezone(UTC),
            )
            unit_of_work.save_transfer(record)
            return record

    @staticmethod
    def _validate_amount(amount: Decimal) -> None:
        if (
            not amount.is_finite()
            or amount <= 0
            or amount.as_tuple().exponent != -2
        ):
            raise InvalidAmount()
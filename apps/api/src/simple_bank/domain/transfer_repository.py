from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import ContextManager, Protocol

from simple_bank.domain.transfers import TransferRecord


@dataclass(frozen=True)
class AccountSnapshot:
    account_number: str
    customer_id: str
    balance: Decimal
    status: str
    account_type: str


class TransferUnitOfWork(Protocol):
    def find_transfer(self, customer_id: str, request_id: str) -> TransferRecord | None: ...

    def get_account(self, account_number: str) -> AccountSnapshot | None: ...

    def get_daily_total(self, customer_id: str, start: datetime, end: datetime) -> Decimal: ...

    def save_transfer(self, transfer: TransferRecord) -> None: ...


class TransferRepository(Protocol):
    def transaction(
        self, customer_id: str, account_numbers: tuple[str, str]
    ) -> ContextManager[TransferUnitOfWork]: ...
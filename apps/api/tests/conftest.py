from collections.abc import Callable, Iterator
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime
from decimal import Decimal
from threading import RLock

import pytest

from simple_bank.domain.transfer_repository import AccountSnapshot
from simple_bank.domain.transfers import TransferRecord


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
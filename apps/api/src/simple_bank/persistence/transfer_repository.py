from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from simple_bank.domain.errors import Forbidden
from simple_bank.domain.transfer_repository import AccountSnapshot
from simple_bank.domain.transfers import TransferRecord
from simple_bank.persistence.models import Account, Customer, Transaction


class SqlAlchemyTransferUnitOfWork:
    def __init__(self, session: Session):
        self._session = session

    def find_transfer(self, customer_id: str, request_id: str) -> TransferRecord | None:
        row = self._session.scalar(
            select(Transaction).where(
                Transaction.customer_id == customer_id,
                Transaction.request_id == request_id,
            )
        )
        if row is None:
            return None
        return TransferRecord(
            transaction_id=row.transaction_id,
            customer_id=row.customer_id,
            request_id=row.request_id,
            from_account=row.from_account,
            to_account=row.to_account,
            amount=row.amount,
            status=row.status,
            created_at=row.created_at,
        )

    def get_account(self, account_number: str) -> AccountSnapshot | None:
        account = self._session.get(Account, account_number)
        if account is None:
            return None
        return AccountSnapshot(
            account_number=account.account_number,
            customer_id=account.customer_id,
            balance=account.balance,
            status=account.status,
            account_type=account.account_type,
        )

    def get_daily_total(self, customer_id: str, start: datetime, end: datetime) -> Decimal:
        total = self._session.scalar(
            select(func.coalesce(func.sum(Transaction.amount), 0)).where(
                Transaction.customer_id == customer_id,
                Transaction.status == "ACCEPTED",
                Transaction.created_at >= start,
                Transaction.created_at < end,
            )
        )
        return Decimal(total)

    def save_transfer(self, transfer: TransferRecord) -> None:
        sender = self._session.get(Account, transfer.from_account)
        recipient = self._session.get(Account, transfer.to_account)
        if sender is None or recipient is None:
            raise RuntimeError("Locked transfer accounts were not available.")
        sender.balance -= transfer.amount
        recipient.balance += transfer.amount
        self._session.add(
            Transaction(
                transaction_id=transfer.transaction_id,
                customer_id=transfer.customer_id,
                request_id=transfer.request_id,
                from_account=transfer.from_account,
                to_account=transfer.to_account,
                amount=transfer.amount,
                status=transfer.status,
                created_at=transfer.created_at,
            )
        )


class SqlAlchemyTransferRepository:
    def __init__(self, session_factory: sessionmaker[Session]):
        self._session_factory = session_factory

    @contextmanager
    def transaction(
        self, customer_id: str, account_numbers: tuple[str, str]
    ) -> Iterator[SqlAlchemyTransferUnitOfWork]:
        session = self._session_factory()
        try:
            with session.begin():
                customer = session.scalar(
                    select(Customer)
                    .where(Customer.customer_id == customer_id)
                    .with_for_update()
                )
                if customer is None:
                    raise Forbidden()
                locked_numbers = sorted(set(account_numbers))
                session.scalars(
                    select(Account)
                    .where(Account.account_number.in_(locked_numbers))
                    .order_by(Account.account_number)
                    .with_for_update()
                ).all()
                yield SqlAlchemyTransferUnitOfWork(session)
        finally:
            session.close()
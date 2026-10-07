from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy import select, event
from sqlalchemy.orm import Session

from simple_bank.domain.transfers import TransferCommand
from simple_bank.persistence.models import Account, Transaction
from simple_bank.persistence.transfer_repository import SqlAlchemyTransferRepository
from simple_bank.services.transfer_service import TransferService

def test_transfer_record_and_both_balance_changes_commit_together(
    postgres_session_factory, verifier_factory, seeded_transfer_accounts
):
    customer_id, sender, recipient = seeded_transfer_accounts
    amount = Decimal("125.50")
    request_id = f"req-{uuid4()}"
    verifier = verifier_factory(
        customer_id=customer_id,
        request_id=request_id,
        from_account=sender,
        to_account=recipient,
        amount=amount,
    )
    service = TransferService(
        SqlAlchemyTransferRepository(postgres_session_factory),
        verifier,
        clock=lambda: datetime(2026, 10, 6, 10, tzinfo=UTC),
    )

    result = service.execute(
        customer_id,
        TransferCommand(request_id, "synthetic-verification-proof", sender, recipient, amount),
    )

    with postgres_session_factory() as session:
        assert session.get(Account, sender).balance == Decimal("374.50")
        assert session.get(Account, recipient).balance == Decimal("225.50")
        assert session.get(Transaction, result.transaction_id).amount == amount


def test_failed_transaction_flush_rolls_back_both_balances_and_record(
    postgres_session_factory, verifier_factory, seeded_transfer_accounts
):
    customer_id, sender, recipient = seeded_transfer_accounts
    amount = Decimal("125.50")
    request_id = f"req-{uuid4()}"
    service = TransferService(
        SqlAlchemyTransferRepository(postgres_session_factory),
        verifier_factory(
            customer_id=customer_id,
            request_id=request_id,
            from_account=sender,
            to_account=recipient,
            amount=amount,
        ),
        clock=lambda: datetime(2026, 10, 6, 10, tzinfo=UTC),
    )

    def fail_transfer_flush(session, flush_context, instances):
        if any(isinstance(item, Transaction) for item in session.new):
            raise RuntimeError("synthetic failure before commit")

    event.listen(Session, "before_flush", fail_transfer_flush)
    try:
        with pytest.raises(RuntimeError, match="synthetic failure"):
            service.execute(
                customer_id,
                TransferCommand(
                    request_id, "synthetic-verification-proof", sender, recipient, amount
                ),
            )
    finally:
        event.remove(Session, "before_flush", fail_transfer_flush)

    with postgres_session_factory() as session:
        assert session.get(Account, sender).balance == Decimal("500.00")
        assert session.get(Account, recipient).balance == Decimal("100.00")
        assert session.scalar(
            select(Transaction).where(Transaction.request_id == request_id)
        ) is None
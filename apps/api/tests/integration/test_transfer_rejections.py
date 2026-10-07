from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import select

from simple_bank.domain.errors import (
    AccountInactive,
    DailyLimitExceeded,
    Forbidden,
    InsufficientBalance,
    InvalidAmount,
    SameAccount,
    VerificationRequired,
)
from simple_bank.domain.transfers import TransferCommand
from simple_bank.persistence.models import Account, Transaction
from simple_bank.persistence.transfer_repository import SqlAlchemyTransferRepository
from simple_bank.services.transfer_service import TransferService
@pytest.mark.parametrize(
    "rule,error_type",
    [
        ("invalid_amount", InvalidAmount),
        ("insufficient_balance", InsufficientBalance),
        ("daily_limit", DailyLimitExceeded),
        ("same_account", SameAccount),
        ("sender_inactive", AccountInactive),
        ("recipient_inactive", AccountInactive),
        ("unowned_sender", Forbidden),
        ("non_savings_sender", Forbidden),
        ("verification", VerificationRequired),
    ],
)
def test_rejected_transfer_leaves_postgres_state_unchanged(
    postgres_session_factory,
    verifier_factory,
    seeded_transfer_accounts,
    rule,
    error_type,
):
    customer_id, sender, recipient = seeded_transfer_accounts
    amount = Decimal("200.00")
    recipient_request = sender if rule == "same_account" else recipient
    proof = "invalid-proof" if rule == "verification" else "synthetic-verification-proof"

    with postgres_session_factory.begin() as session:
        if rule == "insufficient_balance":
            session.get(Account, sender).balance = Decimal("10.00")
        elif rule == "sender_inactive":
            session.get(Account, sender).status = "INACTIVE"
        elif rule == "recipient_inactive":
            session.get(Account, recipient).status = "INACTIVE"
        elif rule == "unowned_sender":
            session.get(Account, sender).customer_id = session.get(Account, recipient).customer_id
        elif rule == "non_savings_sender":
            session.get(Account, sender).account_type = "CURRENT"
        elif rule == "daily_limit":
            session.add(
                Transaction(
                    transaction_id=str(uuid4()),
                    customer_id=customer_id,
                    request_id=f"prior-{uuid4()}",
                    from_account=sender,
                    to_account=recipient,
                    amount=Decimal("99900.00"),
                    status="ACCEPTED",
                    created_at=datetime(2026, 10, 7, 10, tzinfo=UTC),
                )
            )

    request_id = f"req-{uuid4()}"
    verifier = verifier_factory(
        customer_id=customer_id,
        request_id=request_id,
        from_account=sender,
        to_account=recipient_request,
        amount=Decimal("0.00") if rule == "invalid_amount" else amount,
    )
    service = TransferService(
        SqlAlchemyTransferRepository(postgres_session_factory),
        verifier,
        clock=lambda: datetime(2026, 10, 7, 12, tzinfo=UTC),
    )
    command_amount = Decimal("0.00") if rule == "invalid_amount" else amount
    command = TransferCommand(
        request_id, proof, sender, recipient_request, command_amount
    )

    with postgres_session_factory() as session:
        original_balances = {
            sender: session.get(Account, sender).balance,
            recipient: session.get(Account, recipient).balance,
        }
        original_count = len(session.scalars(select(Transaction)).all())

    with pytest.raises(error_type):
        service.execute(customer_id, command)

    with postgres_session_factory() as session:
        assert session.get(Account, sender).balance == original_balances[sender]
        assert session.get(Account, recipient).balance == original_balances[recipient]
        assert len(session.scalars(select(Transaction)).all()) == original_count
        assert session.scalar(
            select(Transaction).where(Transaction.request_id == request_id)
        ) is None
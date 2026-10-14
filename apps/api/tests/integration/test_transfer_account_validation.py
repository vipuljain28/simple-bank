from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import select

from simple_bank.domain.errors import AccountInactive, Forbidden, SameAccount
from simple_bank.domain.transfers import TransferCommand
from simple_bank.persistence.models import Account, Transaction
from simple_bank.persistence.transfer_repository import SqlAlchemyTransferRepository
from simple_bank.services.transfer_service import TransferService


@pytest.mark.parametrize(
    "case,error_type",
    [
        ("missing_sender", Forbidden),
        ("missing_recipient", AccountInactive),
        ("inactive_sender", AccountInactive),
        ("inactive_recipient", AccountInactive),
        ("unowned_sender", Forbidden),
        ("non_savings_sender", Forbidden),
        ("same_account", SameAccount),
    ],
)
def test_invalid_account_is_rejected_without_financial_mutation(
    postgres_session_factory,
    verifier_factory,
    seeded_transfer_accounts,
    case,
    error_type,
):
    customer_id, sender, recipient = seeded_transfer_accounts
    requested_sender = "19910000999998" if case == "missing_sender" else sender
    requested_recipient = (
        "19910000999999"
        if case == "missing_recipient"
        else requested_sender
        if case == "same_account"
        else recipient
    )

    with postgres_session_factory.begin() as session:
        if case == "inactive_sender":
            session.get(Account, sender).status = "INACTIVE"
        elif case == "inactive_recipient":
            session.get(Account, recipient).status = "INACTIVE"
        elif case == "unowned_sender":
            session.get(Account, sender).customer_id = session.get(
                Account, recipient
            ).customer_id
        elif case == "non_savings_sender":
            session.get(Account, sender).account_type = "CURRENT"

    amount = Decimal("10.00")
    request_id = f"req-{uuid4()}"
    verifier = verifier_factory(
        customer_id=customer_id,
        request_id=request_id,
        from_account=requested_sender,
        to_account=requested_recipient,
        amount=amount,
    )
    service = TransferService(
        SqlAlchemyTransferRepository(postgres_session_factory),
        verifier,
        clock=lambda: datetime.now(UTC),
    )
    command = TransferCommand(
        request_id,
        "synthetic-verification-proof",
        requested_sender,
        requested_recipient,
        amount,
    )

    with postgres_session_factory() as session:
        original_balances = {
            sender: session.get(Account, sender).balance,
            recipient: session.get(Account, recipient).balance,
        }
        original_transactions = len(session.scalars(select(Transaction)).all())

    with pytest.raises(error_type):
        service.execute(customer_id, command)

    with postgres_session_factory() as session:
        assert session.get(Account, sender).balance == original_balances[sender]
        assert session.get(Account, recipient).balance == original_balances[recipient]
        assert len(session.scalars(select(Transaction)).all()) == original_transactions


def test_legacy_numeric_account_identifiers_remain_valid(
    postgres_session_factory, verifier_factory, seeded_transfer_accounts
):
    customer_id, sender, recipient = seeded_transfer_accounts
    assert sender.isdigit() and not sender.startswith("1991")
    amount = Decimal("10.00")
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
        clock=lambda: datetime.now(UTC),
    )

    result = service.execute(
        customer_id,
        TransferCommand(
            request_id, "synthetic-verification-proof", sender, recipient, amount
        ),
    )

    assert result.from_account == sender
    assert result.to_account == recipient
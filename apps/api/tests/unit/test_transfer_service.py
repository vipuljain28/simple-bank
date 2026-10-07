from datetime import UTC, datetime
from decimal import Decimal

from simple_bank.domain.transfers import TransferCommand
from simple_bank.services.transfer_service import TransferService


def test_eligible_transfer_saves_record_and_moves_exact_amount(
    transfer_repository, verifier_factory
):
    amount = Decimal("125.50")
    verifier = verifier_factory(
        customer_id="customer-001",
        request_id="req-001",
        from_account="000000001001",
        to_account="000000002002",
        amount=amount,
    )
    service = TransferService(
        transfer_repository,
        verifier,
        clock=lambda: datetime(2026, 10, 6, 10, tzinfo=UTC),
    )

    accepted = service.execute(
        "customer-001",
        TransferCommand(
            "req-001",
            "synthetic-verification-proof",
            "000000001001",
            "000000002002",
            amount,
        ),
    )

    assert accepted.transaction_id
    assert accepted.status == "ACCEPTED"
    assert accepted.amount == amount
    assert transfer_repository.accounts["000000001001"].balance == Decimal("374.50")
    assert transfer_repository.accounts["000000002002"].balance == Decimal("225.50")
    assert transfer_repository.find_transfer("customer-001", "req-001") == accepted


def test_transfer_equal_to_sender_balance_is_allowed(transfer_repository, verifier_factory):
    amount = Decimal("500.00")
    verifier = verifier_factory(
        customer_id="customer-001",
        request_id="req-exact-balance",
        from_account="000000001001",
        to_account="000000002002",
        amount=amount,
    )
    service = TransferService(transfer_repository, verifier)

    service.execute(
        "customer-001",
        TransferCommand(
            "req-exact-balance",
            "synthetic-verification-proof",
            "000000001001",
            "000000002002",
            amount,
        ),
    )

    assert transfer_repository.accounts["000000001001"].balance == Decimal("0.00")
    assert transfer_repository.accounts["000000002002"].balance == Decimal("600.00")
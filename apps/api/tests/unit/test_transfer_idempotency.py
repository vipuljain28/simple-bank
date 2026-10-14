from datetime import UTC, datetime
from decimal import Decimal

import pytest

from simple_bank.domain.errors import RequestIdConflict
from simple_bank.domain.transfers import TransferCommand
from simple_bank.services.transfer_service import TransferService


def test_matching_retry_returns_original_without_reverification(
    transfer_repository, verifier_factory, test_settings
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
        settings=test_settings,
        clock=lambda: datetime(2026, 10, 6, 10, tzinfo=UTC),
    )
    command = TransferCommand(
        "req-001",
        "synthetic-verification-proof",
        "000000001001",
        "000000002002",
        amount,
    )

    original = service.execute("customer-001", command)
    retry = service.execute(
        "customer-001",
        TransferCommand(
            "req-001", "expired-or-absent", "000000001001", "000000002002", amount
        ),
    )

    assert retry == original
    assert len(verifier.calls) == 1
    assert transfer_repository.accounts["000000001001"].balance == Decimal("4874.50")
    assert len(transfer_repository.transfers) == 1


def test_reusing_request_id_with_changed_details_is_rejected(
    transfer_repository, verifier_factory, test_settings
):
    amount = Decimal("125.50")
    verifier = verifier_factory(
        customer_id="customer-001",
        request_id="req-001",
        from_account="000000001001",
        to_account="000000002002",
        amount=amount,
    )
    service = TransferService(transfer_repository, verifier, settings=test_settings)
    command = TransferCommand(
        "req-001",
        "synthetic-verification-proof",
        "000000001001",
        "000000002002",
        amount,
    )
    service.execute("customer-001", command)

    with pytest.raises(RequestIdConflict):
        service.execute(
            "customer-001",
            TransferCommand(
                "req-001",
                "synthetic-verification-proof",
                "000000001001",
                "000000002002",
                Decimal("100.00"),
            ),
        )

    assert transfer_repository.accounts["000000001001"].balance == Decimal("4874.50")
    assert len(transfer_repository.transfers) == 1
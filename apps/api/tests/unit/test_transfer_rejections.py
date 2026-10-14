from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from simple_bank.domain.errors import (
    AccountInactive,
    DailyLimitExceeded,
    Forbidden,
    InsufficientBalance,
    InvalidAmount,
    MinimumBalanceRequired,
    SameAccount,
    VerificationRequired,
)
from simple_bank.domain.transfers import TransferCommand, TransferRecord
from simple_bank.services.transfer_service import TransferService


def _service(repository, verifier_factory, test_settings, amount, *, proof="synthetic-verification-proof"):
    verifier = verifier_factory(
        customer_id="customer-001",
        request_id="req-reject",
        from_account="000000001001",
        to_account="000000002002",
        amount=amount,
    )
    return TransferService(
        repository,
        verifier,
        settings=test_settings,
        clock=lambda: datetime(2026, 10, 6, 10, tzinfo=UTC),
    ), verifier, TransferCommand(
        "req-reject", proof, "000000001001", "000000002002", amount
    )


def _assert_unchanged(repository, sender_balance=Decimal("5000.00"), recipient_balance=Decimal("2000.00")):
    assert repository.accounts["000000001001"].balance == sender_balance
    assert repository.accounts["000000002002"].balance == recipient_balance
    assert repository.transfers == {}


@pytest.mark.parametrize("amount", [Decimal("0.00"), Decimal("-1.00"), Decimal("1.0")])
def test_invalid_amount_is_rejected_without_mutation(
    transfer_repository, verifier_factory, test_settings, amount
):
    service, _, command = _service(transfer_repository, verifier_factory, test_settings, amount)

    with pytest.raises(InvalidAmount):
        service.execute("customer-001", command)

    _assert_unchanged(transfer_repository)


def test_insufficient_balance_is_rejected_without_mutation(
    transfer_repository, verifier_factory, test_settings
):
    amount = Decimal("10000.00")
    service, _, command = _service(transfer_repository, verifier_factory, test_settings, amount)

    with pytest.raises(InsufficientBalance):
        service.execute("customer-001", command)

    _assert_unchanged(transfer_repository)


def test_minimum_balance_violation_is_rejected_without_mutation(
    transfer_repository, verifier_factory, test_settings
):
    amount = Decimal("4001.00")
    service, _, command = _service(transfer_repository, verifier_factory, test_settings, amount)

    with pytest.raises(MinimumBalanceRequired):
        service.execute("customer-001", command)

    _assert_unchanged(transfer_repository)


def test_daily_limit_uses_accepted_customer_transfers_for_ist_day(
    transfer_repository, verifier_factory, test_settings
):
    # Need high balance for both prior and current transfers to stay above minimum
    transfer_repository.accounts["000000001001"] = replace(
        transfer_repository.accounts["000000001001"],
        balance=Decimal("105000.00")
    )
    transfer_repository.accounts["000000002002"] = replace(
        transfer_repository.accounts["000000002002"],
        balance=Decimal("2000.00")
    )
    
    # Create a prior transfer of 2000, leaving balance at 103000
    transfer_repository.transfers[("customer-001", "prior")]=TransferRecord(
        "txn-prior",
        "customer-001",
        "prior",
        "000000001001",
        "000000002002",
        Decimal("2000.00"),
        "ACCEPTED",
        datetime(2026, 10, 6, 5, tzinfo=UTC),
    )
    # Manually adjust balance
    transfer_repository.accounts["000000001001"] = replace(
        transfer_repository.accounts["000000001001"],
        balance=Decimal("103000.00")
    )
    transfer_repository.accounts["000000002002"] = replace(
        transfer_repository.accounts["000000002002"],
        balance=Decimal("4000.00")
    )
    
    # Try transfer of 98100 making total 2000 + 98100 = 100100 > 100000 limit
    # This will be rejected for daily limit, not for minimum balance
    # (103000 - 98100 = 4900 > 1000 minimum)
    amount = Decimal("98100.00")
    verifier = verifier_factory(
        customer_id="customer-001",
        request_id="req-reject",
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
        "req-reject", "synthetic-verification-proof", "000000001001", "000000002002", amount
    )

    with pytest.raises(DailyLimitExceeded):
        service.execute("customer-001", command)

    # Balances unchanged after failed transfer
    assert transfer_repository.accounts["000000001001"].balance == Decimal("103000.00")
    assert transfer_repository.accounts["000000002002"].balance == Decimal("4000.00")
    assert len(transfer_repository.transfers) == 1


def test_exactly_reaching_daily_limit_is_allowed(transfer_repository, verifier_factory, test_settings):
    # Need high balance to support transfers + minimum balance requirement
    # Start with 105000 to support 100000 in transfers + 1000 minimum + 4000 headroom
    transfer_repository.accounts["000000001001"] = replace(
        transfer_repository.accounts["000000001001"],
        balance=Decimal("105000.00")
    )
    transfer_repository.accounts["000000002002"] = replace(
        transfer_repository.accounts["000000002002"],
        balance=Decimal("2000.00")
    )
    
    # Create a prior transfer of 2000
    transfer_repository.transfers[("customer-001", "prior")] = TransferRecord(
        "txn-prior",
        "customer-001",
        "prior",
        "000000001001",
        "000000002002",
        Decimal("2000.00"),
        "ACCEPTED",
        datetime(2026, 10, 6, 5, tzinfo=UTC),
    )
    # Manually adjust balances after prior transfer
    transfer_repository.accounts["000000001001"] = replace(
        transfer_repository.accounts["000000001001"],
        balance=Decimal("103000.00")  # 105000 - 2000
    )
    transfer_repository.accounts["000000002002"] = replace(
        transfer_repository.accounts["000000002002"],
        balance=Decimal("4000.00")  # 2000 + 2000
    )
    
    # Transfer 98000, making total 2000 + 98000 = 100000 (exactly at limit)
    amount = Decimal("98000.00")
    verifier = verifier_factory(
        customer_id="customer-001",
        request_id="req-reject",
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
        "req-reject", "synthetic-verification-proof", "000000001001", "000000002002", amount
    )

    service.execute("customer-001", command)

    assert transfer_repository.accounts["000000001001"].balance == Decimal("5000.00")  # 103000 - 98000, leaves exactly 5000 above minimum
    assert transfer_repository.accounts["000000002002"].balance == Decimal("102000.00")  # 4000 + 98000
    assert len(transfer_repository.transfers) == 2


def test_daily_limit_resets_at_ist_midnight(transfer_repository, verifier_factory, test_settings):
    transfer_repository.transfers[("customer-001", "prior")] = TransferRecord(
        "txn-prior",
        "customer-001",
        "prior",
        "000000001001",
        "000000002002",
        Decimal("99900.00"),
        "ACCEPTED",
        datetime(2026, 10, 6, 18, 29, 59, tzinfo=UTC),
    )
    amount = Decimal("200.00")
    verifier = verifier_factory(
        customer_id="customer-001",
        request_id="req-midnight",
        from_account="000000001001",
        to_account="000000002002",
        amount=amount,
    )
    service = TransferService(
        transfer_repository,
        verifier,
        settings=test_settings,
        clock=lambda: datetime(2026, 10, 6, 18, 30, tzinfo=UTC),
    )

    service.execute(
        "customer-001",
        TransferCommand(
            "req-midnight",
            "synthetic-verification-proof",
            "000000001001",
            "000000002002",
            amount,
        ),
    )

    assert transfer_repository.accounts["000000001001"].balance == Decimal("4800.00")
    assert transfer_repository.accounts["000000002002"].balance == Decimal("2200.00")
    assert len(transfer_repository.transfers) == 2


def test_same_account_is_rejected_without_mutation(transfer_repository, verifier_factory, test_settings):
    amount = Decimal("10.00")
    verifier = verifier_factory(
        customer_id="customer-001",
        request_id="req-reject",
        from_account="000000001001",
        to_account="000000001001",
        amount=amount,
    )
    service = TransferService(transfer_repository, verifier, settings=test_settings)
    command = TransferCommand(
        "req-reject", "synthetic-verification-proof", "000000001001", "000000001001", amount
    )

    with pytest.raises(SameAccount):
        service.execute("customer-001", command)

    _assert_unchanged(transfer_repository)


@pytest.mark.parametrize("which", ["sender", "recipient"])
def test_inactive_account_is_rejected_without_mutation(
    transfer_repository, verifier_factory, test_settings, which
):
    account_number = "000000001001" if which == "sender" else "000000002002"
    transfer_repository.accounts[account_number] = replace(
        transfer_repository.accounts[account_number], status="INACTIVE"
    )
    amount = Decimal("10.00")
    service, _, command = _service(transfer_repository, verifier_factory, test_settings, amount)

    with pytest.raises(AccountInactive):
        service.execute("customer-001", command)

    _assert_unchanged(transfer_repository)


@pytest.mark.parametrize(
    "customer_id, sender_type",
    [("another-customer", "SAVINGS"), ("customer-001", "CURRENT")],
)
def test_sender_ownership_and_savings_requirements_are_forbidden(
    transfer_repository, verifier_factory, test_settings, customer_id, sender_type
):
    transfer_repository.accounts["000000001001"] = replace(
        transfer_repository.accounts["000000001001"],
        customer_id=customer_id,
        account_type=sender_type,
    )
    amount = Decimal("10.00")
    service, _, command = _service(transfer_repository, verifier_factory, test_settings, amount)

    with pytest.raises(Forbidden):
        service.execute("customer-001", command)

    _assert_unchanged(transfer_repository)


def test_invalid_verification_is_rejected_without_mutation(
    transfer_repository, verifier_factory, test_settings
):
    amount = Decimal("10.00")
    service, verifier, command = _service(
        transfer_repository, verifier_factory, test_settings, amount, proof="invalid-proof"
    )

    with pytest.raises(VerificationRequired):
        service.execute("customer-001", command)

    assert verifier.calls == [
        ("customer-001", "req-reject", "000000001001", "000000002002", amount)
    ]
    _assert_unchanged(transfer_repository)
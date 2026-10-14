from dataclasses import replace

import pytest
from argon2 import PasswordHasher

from simple_bank.domain.auth import RegistrationCommand, RegistrationResult, RegisteredAccount
from simple_bank.domain.auth_errors import InvalidRegistration, RegistrationConflict
from simple_bank.services.auth_service import CustomerAuthService
from simple_bank.settings import Settings


def _command(**changes):
    command = RegistrationCommand(
        name="Synthetic Customer",
        email="Customer@Example.Test",
        mobile_number="+919876543210",
        username="Customer-Demo",
        password="long synthetic passphrase",
        account_number_suffix="0000123456",
    )
    return replace(command, **changes)


def _service(auth_repository, contact_delivery, frozen_clock):
    return CustomerAuthService(
        auth_repository,
        contact_delivery,
        settings=Settings(database_url=None),
        clock=frozen_clock,
    )


def test_registration_creates_zero_balance_account_and_hashes_password(
    auth_repository, contact_delivery, frozen_clock
):
    result = _service(auth_repository, contact_delivery, frozen_clock).register(
        _command()
    )

    assert isinstance(result, RegistrationResult)
    assert result.account == RegisteredAccount(
        account_number="19910000123456",
        account_type="SAVINGS",
        status="ACTIVE",
        balance="0.00",
    )
    profile = auth_repository.get_profile_by_id(result.customer_id)
    assert profile is not None
    assert profile.email == "customer@example.test"
    assert profile.username == "customer-demo"
    assert profile.mobile_number == "+919876543210"
    assert profile.password_hash != _command().password
    assert PasswordHasher().verify(profile.password_hash, _command().password)
    assert result.transfer_eligible is False


@pytest.mark.parametrize(
    "changes",
    [
        {"name": ""},
        {"email": "not-an-email"},
        {"mobile_number": "9876543210"},
        {"username": ""},
        {"password": "too-short"},
        {"password": "p" * 129},
        {"account_number_suffix": "123456789"},
        {"account_number_suffix": "12345678901"},
        {"account_number_suffix": "12345x7890"},
        {"account_number_suffix": "１２３４５６７８９０"},
    ],
)
def test_invalid_registration_details_are_rejected_without_writes(
    auth_repository, contact_delivery, frozen_clock, changes
):
    service = _service(auth_repository, contact_delivery, frozen_clock)

    with pytest.raises(InvalidRegistration):
        service.register(_command(**changes))

    assert auth_repository.profiles == {}
    assert auth_repository.accounts == {}


def test_registration_normalizes_unique_identity_fields(
    auth_repository, contact_delivery, frozen_clock
):
    service = _service(auth_repository, contact_delivery, frozen_clock)
    service.register(_command())

    with pytest.raises(RegistrationConflict):
        service.register(
            _command(
                username="customer-demo",
                email="different@example.test",
                account_number_suffix="0000123457",
            )
        )
    with pytest.raises(RegistrationConflict):
        service.register(
            _command(
                username="different-user",
                email="customer@example.test",
                account_number_suffix="0000123458",
            )
        )

    assert len(auth_repository.profiles) == 1
    assert len(auth_repository.accounts) == 1


def test_mobile_number_can_be_shared_but_account_number_cannot(
    auth_repository, contact_delivery, frozen_clock
):
    service = _service(auth_repository, contact_delivery, frozen_clock)
    service.register(_command())
    second = service.register(
        _command(
            name="Another Synthetic Customer",
            email="another@example.test",
            username="another-demo",
            account_number_suffix="0000123457",
        )
    )
    assert second.customer_id != next(iter(auth_repository.profiles))
    assert len(auth_repository.profiles) == 2

    with pytest.raises(RegistrationConflict):
        service.register(
            _command(
                username="third-demo",
                email="third@example.test",
            )
        )

    assert len(auth_repository.profiles) == 2
    assert len(auth_repository.accounts) == 2


def test_phone_number_is_canonicalized_to_e164(
    auth_repository, contact_delivery, frozen_clock
):
    result = _service(auth_repository, contact_delivery, frozen_clock).register(
        _command(mobile_number="+91 98765 43210")
    )

    profile = auth_repository.get_profile_by_id(result.customer_id)
    assert profile.mobile_number == "+919876543210"
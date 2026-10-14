from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace

from sqlalchemy import select

from simple_bank.domain.auth import RegistrationCommand
from simple_bank.domain.auth_errors import RegistrationConflict
from simple_bank.persistence.auth_repository import SqlAlchemyAuthRepository
from simple_bank.persistence.models import Account, CustomerProfile
from simple_bank.services.auth_service import CustomerAuthService
from simple_bank.settings import Settings


def _command(suffix: str, username: str, email: str) -> RegistrationCommand:
    return RegistrationCommand(
        name="Synthetic Customer",
        email=email,
        mobile_number="+919876543210",
        username=username,
        password="long synthetic passphrase",
        account_number_suffix=suffix,
    )


def test_registration_commits_customer_profile_and_account_together(
    postgres_session_factory, contact_delivery, frozen_clock
):
    service = CustomerAuthService(
        SqlAlchemyAuthRepository(postgres_session_factory),
        contact_delivery,
        settings=Settings(database_url=None),
        clock=frozen_clock,
    )
    result = service.register(
        _command("0000123456", "customer-demo", "customer@example.test")
    )

    with postgres_session_factory() as session:
        profile = session.get(CustomerProfile, result.customer_id)
        account = session.scalar(
            select(Account).where(Account.customer_id == result.customer_id)
        )
        assert profile is not None
        assert account is not None
        assert account.account_number == "19910000123456"
        assert account.balance == 0
        assert account.account_type == "SAVINGS"
        assert account.status == "ACTIVE"


def test_concurrent_duplicate_suffix_creates_at_most_one_account(
    postgres_session_factory, contact_delivery, frozen_clock
):
    def register(index: int):
        service = CustomerAuthService(
            SqlAlchemyAuthRepository(postgres_session_factory),
            contact_delivery,
            settings=Settings(database_url=None),
            clock=frozen_clock,
        )
        return service.register(
            _command(
                "0000123456",
                f"customer-{index}",
                f"customer-{index}@example.test",
            )
        )

    def attempt(index: int):
        try:
            return register(index)
        except RegistrationConflict:
            return None

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(attempt, (1, 2)))

    assert sum(result is not None for result in results) == 1
    with postgres_session_factory() as session:
        account = session.get(Account, "19910000123456")
        assert account is not None
        assert session.scalar(
            select(Account.account_number).where(
                Account.account_number == "19910000123456"
            )
        ) == account.account_number
import os
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import inspect
from sqlalchemy.engine import make_url

from simple_bank.persistence.database import create_database_engine, create_session_factory
from simple_bank.persistence.models import Account, Base, Customer


@pytest.fixture
def postgres_session_factory():
    database_url = os.environ.get("TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("Set TEST_DATABASE_URL to an empty local simple_bank_test database.")
    parsed_url = make_url(database_url)
    if parsed_url.host not in {"localhost", "127.0.0.1", "::1"} or parsed_url.database != "simple_bank_test":
        pytest.fail("Integration tests require localhost database simple_bank_test.")

    engine = create_database_engine(database_url)
    if inspect(engine).get_table_names():
        engine.dispose()
        pytest.skip("Integration tests require an empty simple_bank_test database.")
    Base.metadata.create_all(engine)
    yield create_session_factory(engine)
    Base.metadata.drop_all(engine)
    engine.dispose()


def seed_transfer_accounts(session_factory):
    customer_id = f"customer-{uuid4()}"
    recipient_customer_id = f"recipient-{uuid4()}"
    sender_number = f"1001{uuid4().int % 100000000:08d}"
    recipient_number = f"2002{uuid4().int % 100000000:08d}"
    with session_factory.begin() as session:
        session.add_all(
            [Customer(customer_id=customer_id), Customer(customer_id=recipient_customer_id)]
        )
        session.add_all(
            [
                Account(
                    account_number=sender_number,
                    customer_id=customer_id,
                    balance=Decimal("500.00"),
                    status="ACTIVE",
                    account_type="SAVINGS",
                ),
                Account(
                    account_number=recipient_number,
                    customer_id=recipient_customer_id,
                    balance=Decimal("100.00"),
                    status="ACTIVE",
                    account_type="CURRENT",
                ),
            ]
        )
    return customer_id, sender_number, recipient_number


@pytest.fixture
def seeded_transfer_accounts(postgres_session_factory):
    return seed_transfer_accounts(postgres_session_factory)
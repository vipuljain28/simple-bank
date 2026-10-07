from datetime import UTC, datetime
from decimal import Decimal
from time import perf_counter
from uuid import uuid4

from fastapi.testclient import TestClient

from simple_bank.api.app import create_app
from simple_bank.persistence.transfer_repository import SqlAlchemyTransferRepository
from simple_bank.security.context import AuthenticatedCustomer
from simple_bank.services.transfer_service import TransferService
class FixedCustomerContext:
    def __init__(self, customer_id: str):
        self._customer_id = customer_id

    def resolve(self, request):
        return AuthenticatedCustomer(self._customer_id)


def test_customer_receives_transfer_outcome_within_one_second(
    postgres_session_factory, verifier_factory, seeded_transfer_accounts
):
    customer_id, sender, recipient = seeded_transfer_accounts
    request_id = f"req-{uuid4()}"
    amount = Decimal("25.00")
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
        clock=lambda: datetime.now(UTC),
    )
    client = TestClient(
        create_app(
            transfer_service=service,
            customer_context_provider=FixedCustomerContext(customer_id),
        )
    )
    started = perf_counter()
    response = client.post(
        "/api/v1/transfers",
        json={
            "request_id": request_id,
            "verification_proof": "synthetic-verification-proof",
            "from_account": sender,
            "to_account": recipient,
            "amount": "25.00",
        },
    )
    elapsed = perf_counter() - started

    assert response.status_code == 201
    assert response.json()["status"] == "ACCEPTED"
    assert elapsed < 1.0
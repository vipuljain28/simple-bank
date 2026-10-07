from decimal import Decimal
from typing import Protocol


class TransferVerifier(Protocol):
    def verify(
        self,
        *,
        customer_id: str,
        request_id: str,
        from_account: str,
        to_account: str,
        amount: Decimal,
        proof: str,
    ) -> bool: ...


class RejectingTransferVerifier:
    def verify(
        self,
        *,
        customer_id: str,
        request_id: str,
        from_account: str,
        to_account: str,
        amount: Decimal,
        proof: str,
    ) -> bool:
        return False
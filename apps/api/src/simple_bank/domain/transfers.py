from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True)
class TransferCommand:
    request_id: str
    verification_proof: str
    from_account: str
    to_account: str
    amount: Decimal


@dataclass(frozen=True)
class TransferRecord:
    transaction_id: str
    customer_id: str
    request_id: str
    from_account: str
    to_account: str
    amount: Decimal
    status: str
    created_at: datetime
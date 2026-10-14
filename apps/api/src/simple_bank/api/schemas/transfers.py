import re
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


_MONEY = re.compile(r"^-?[0-9]+\.[0-9]{2}$")


class TransferRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: str = Field(min_length=1, max_length=128)
    verification_proof: str | None = Field(default=None, max_length=4096)
    from_account: str = Field(min_length=1, max_length=64)
    to_account: str = Field(min_length=1, max_length=64)
    amount: Decimal

    @field_validator("from_account", "to_account")
    @classmethod
    def validate_account_identifier(cls, value: str) -> str:
        if not value.isascii() or not value.isdigit():
            raise ValueError("Account identifiers must contain digits only.")
        return value

    @field_validator("amount", mode="before")
    @classmethod
    def parse_amount(cls, value: object) -> Decimal:
        if not isinstance(value, str) or not _MONEY.fullmatch(value):
            raise ValueError("Amount must be a decimal string with two decimal places.")
        return Decimal(value)


class TransferResponse(BaseModel):
    transaction_id: str
    request_id: str
    from_account: str
    to_account: str
    amount: str
    status: str
    created_at: datetime
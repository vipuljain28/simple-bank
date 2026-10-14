"""Response schemas for mini account statement API."""
from typing import Literal
from pydantic import BaseModel, Field, field_validator


class TransactionDetail(BaseModel):
    """A single transaction in the mini statement.
    
    Fields:
    - timestamp: ISO 8601 format with IST timezone (+05:30)
    - type: "DEBIT" (money out) or "CREDIT" (money in)
    - amount: Decimal as string with 2 places
    - balance_after: Balance after this transaction (Decimal as string, 2 places)
    - description: Human-readable transaction description
    """
    timestamp: str = Field(
        ..., 
        description="ISO 8601 timestamp with IST offset, e.g., '2026-10-14T15:30:45+05:30'"
    )
    type: Literal["DEBIT", "CREDIT"] = Field(
        ...,
        description="Transaction type: DEBIT (money out) or CREDIT (money in)"
    )
    amount: str = Field(
        ..., 
        description="Amount transferred (Decimal as string with 2 places)"
    )
    balance_after: str = Field(
        ..., 
        description="Account balance after this transaction (Decimal as string with 2 places)"
    )
    description: str = Field(
        ...,
        description="Transaction description, e.g., 'Transfer to XXXX5678'"
    )

    @field_validator("amount", "balance_after", mode="before")
    @classmethod
    def validate_decimal_format(cls, v: str) -> str:
        """Validate that amounts are strings with exactly 2 decimal places."""
        if not isinstance(v, str):
            v = str(v)
        
        # Check format: optional minus, digits, exactly one dot, exactly 2 digits
        parts = v.split(".")
        if len(parts) != 2:
            raise ValueError(f"Amount must have exactly 2 decimal places: {v}")
        
        integer_part, decimal_part = parts
        if decimal_part != "00" and len(decimal_part) != 2:
            raise ValueError(f"Decimal part must be exactly 2 digits: {v}")
        
        try:
            float(v)
        except ValueError:
            raise ValueError(f"Invalid decimal format: {v}")
        
        return v

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        """Validate transaction type is DEBIT or CREDIT."""
        if v not in ("DEBIT", "CREDIT"):
            raise ValueError(f"Type must be DEBIT or CREDIT, got: {v}")
        return v

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, v: str) -> str:
        """Validate timestamp is ISO 8601 with IST offset."""
        # Simple check: should end with +05:30
        if not v.endswith("+05:30"):
            raise ValueError(f"Timestamp must be in IST ISO 8601 format (+05:30): {v}")
        return v


class MiniStatementResponse(BaseModel):
    """Response body for the mini statement endpoint.
    
    Fields:
    - account_number: Masked format (XXXX + last 4 digits)
    - current_balance: Current account balance (Decimal as string with 2 places)
    - transactions: List of last 10 transactions (newest first)
    """
    account_number: str = Field(
        ...,
        description="Masked account number in format XXXX1234",
        pattern=r"^XXXX\d{4}$"
    )
    current_balance: str = Field(
        ...,
        description="Current account balance (Decimal as string with 2 places)"
    )
    transactions: list[TransactionDetail] = Field(
        default_factory=list,
        description="List of transactions (newest first), max 10 items"
    )

    @field_validator("account_number")
    @classmethod
    def validate_account_number(cls, v: str) -> str:
        """Validate account number is properly masked."""
        if not v.startswith("XXXX"):
            raise ValueError(f"Account number must start with XXXX: {v}")
        if len(v) != 8:
            raise ValueError(f"Account number must be 8 chars (XXXX + 4 digits): {v}")
        if not v[4:].isdigit():
            raise ValueError(f"Last 4 chars must be digits: {v}")
        return v

    @field_validator("current_balance", mode="before")
    @classmethod
    def validate_balance_format(cls, v: str) -> str:
        """Validate balance has exactly 2 decimal places."""
        if not isinstance(v, str):
            v = str(v)
        
        parts = v.split(".")
        if len(parts) != 2:
            raise ValueError(f"Balance must have exactly 2 decimal places: {v}")
        
        integer_part, decimal_part = parts
        if decimal_part != "00" and len(decimal_part) != 2:
            raise ValueError(f"Decimal part must be exactly 2 digits: {v}")
        
        return v

    @field_validator("transactions")
    @classmethod
    def validate_transaction_limit(cls, v: list) -> list:
        """Validate transaction list has max 10 items."""
        if len(v) > 10:
            raise ValueError(f"Max 10 transactions allowed, got {len(v)}")
        return v

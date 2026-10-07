from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from simple_bank.persistence.models.base import Base


class Account(Base):
    __tablename__ = "accounts"
    __table_args__ = (
        CheckConstraint("balance >= 0", name="ck_accounts_balance_nonnegative"),
        CheckConstraint("status IN ('ACTIVE', 'INACTIVE')", name="ck_accounts_status"),
    )

    account_number: Mapped[str] = mapped_column(String(64), primary_key=True)
    customer_id: Mapped[str] = mapped_column(
        String(128), ForeignKey("customers.customer_id"), nullable=False, index=True
    )
    balance: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(8), nullable=False)
    account_type: Mapped[str] = mapped_column(String(32), nullable=False)
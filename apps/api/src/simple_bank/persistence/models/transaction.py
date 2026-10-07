from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from simple_bank.persistence.models.base import Base


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        UniqueConstraint("customer_id", "request_id", name="uq_transactions_customer_request"),
        CheckConstraint("amount > 0", name="ck_transactions_amount_positive"),
        CheckConstraint("status = 'ACCEPTED'", name="ck_transactions_status_accepted"),
        CheckConstraint("from_account <> to_account", name="ck_transactions_different_accounts"),
    )

    transaction_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    customer_id: Mapped[str] = mapped_column(
        String(128), ForeignKey("customers.customer_id"), nullable=False
    )
    request_id: Mapped[str] = mapped_column(String(128), nullable=False)
    from_account: Mapped[str] = mapped_column(
        String(64), ForeignKey("accounts.account_number"), nullable=False
    )
    to_account: Mapped[str] = mapped_column(
        String(64), ForeignKey("accounts.account_number"), nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(8), nullable=False, default="ACCEPTED")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
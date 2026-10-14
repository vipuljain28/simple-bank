from datetime import UTC, datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from simple_bank.persistence.models.base import Base


class CustomerProfile(Base):
    __tablename__ = "customer_profiles"
    __table_args__ = (
        UniqueConstraint("email", name="uq_customer_profiles_email"),
        UniqueConstraint("username", name="uq_customer_profiles_username"),
        CheckConstraint("length(trim(name)) > 0", name="ck_customer_profiles_name_nonempty"),
        CheckConstraint("length(trim(email)) > 0", name="ck_customer_profiles_email_nonempty"),
        CheckConstraint("length(trim(username)) > 0", name="ck_customer_profiles_username_nonempty"),
    )

    customer_id: Mapped[str] = mapped_column(
        Text, ForeignKey("customers.customer_id", ondelete="CASCADE"), primary_key=True
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    email: Mapped[str] = mapped_column(Text, nullable=False)
    mobile_number: Mapped[str] = mapped_column(Text, nullable=False)
    username: Mapped[str] = mapped_column(Text, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    email_verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    mobile_verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
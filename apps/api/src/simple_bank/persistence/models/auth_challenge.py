from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from simple_bank.persistence.models.base import Base


class AuthChallenge(Base):
    __tablename__ = "auth_challenges"
    __table_args__ = (
        CheckConstraint(
            "purpose IN ('CONTACT_VERIFICATION', 'PASSWORD_RESET')",
            name="ck_auth_challenges_purpose",
        ),
        CheckConstraint("channel IN ('email', 'mobile')", name="ck_auth_challenges_channel"),
        CheckConstraint("attempt_count BETWEEN 0 AND 5", name="ck_auth_challenges_attempts"),
        CheckConstraint("expires_at > created_at", name="ck_auth_challenges_expiry"),
        Index("ix_auth_challenges_customer_purpose_channel", "customer_id", "purpose", "channel"),
    )

    challenge_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    customer_id: Mapped[str] = mapped_column(
        String(128), ForeignKey("customer_profiles.customer_id", ondelete="CASCADE"),
        nullable=False,
    )
    purpose: Mapped[str] = mapped_column(String(32), nullable=False)
    channel: Mapped[str] = mapped_column(String(16), nullable=False)
    token_digest: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    attempt_count: Mapped[int] = mapped_column(nullable=False, default=0)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
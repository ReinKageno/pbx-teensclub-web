
from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, func, Enum as SQLEnum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class TransactionType(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"

class TransactionStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"

class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = {"schema": "community_fund"}

    id: Mapped[int] = mapped_column(primary_key=True)

    type: Mapped[TransactionType] = mapped_column(
        SQLEnum(TransactionType)
    )

    amount: Mapped[int]

    description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )

    issuer: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )

    payment_method: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )

    status: Mapped[TransactionStatus] = mapped_column(
        SQLEnum(TransactionStatus),
        default=TransactionStatus.CONFIRMED
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

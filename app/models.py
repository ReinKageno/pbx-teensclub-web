from datetime import date, datetime
from enum import Enum
from sqlalchemy import Date, DateTime, func, Enum as SQLEnum, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class TransactionType(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"

class TransactionStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"

class GoalStatus(str, Enum):
    ACTIVE = "active"
    UPCOMING = "upcoming"
    FINISHED = "finished"

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

class Goal(Base):
    __tablename__ = "goals"
    __table_args__ = {"schema": "community_fund"}

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(
        String(100)
    )

    description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )

    target_amount: Mapped[int]

    start_date: Mapped[date] = mapped_column(
        Date,
        server_default=func.current_date()
    )

    end_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    status: Mapped[GoalStatus] = mapped_column(
        SQLEnum(GoalStatus),
        server_default=GoalStatus.UPCOMING
    )
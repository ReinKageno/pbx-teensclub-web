from datetime import date, datetime
from enum import Enum

from sqlalchemy import Date, DateTime, func, Enum as SQLEnum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class GoalStatus(str, Enum):
    ACTIVE = "active"
    UPCOMING = "upcoming"
    FINISHED = "finished"

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
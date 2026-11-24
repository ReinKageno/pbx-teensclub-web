from datetime import date, datetime
from os import environ
import secrets
import uuid

from sqlalchemy import ARRAY, CheckConstraint, Date, DateTime, Integer, String, false, func
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.models.enums import GoalStatus, NotifyLevel, TransactionStatus, TransactionIO


class Base(DeclarativeBase):
    pass

GEN_USER = environ.get("GEN_USER_ID")

class User(Base):
    __tablename__ = "user"
    __table_args__ = {"schema": "server"}

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
        default=lambda: secrets.randbelow(int(GEN_USER)),
        unique=True,
        nullable=False,
    )

    user_id: Mapped[str] = mapped_column(
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False,
    )

    username: Mapped[str] = mapped_column(
        String(40),
        unique=True,
        nullable=False,
    )

    display_name: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        unique=True,
        nullable=False,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    is_admin: Mapped[bool] = mapped_column(
        nullable=False,
        server_default=false(),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

class UserSession(Base):
    __tablename__ = "session"
    __table_args__ = {"schema": "server"}

    id: Mapped[str] = mapped_column(
        String(255),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    user_id: Mapped[int] = mapped_column(
        nullable=False,
    )

    session_id: Mapped[str] = mapped_column(
        String(128),
        unique=True,
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    last_active_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
    )

    max_expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
    )

class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = {"schema":"server"}

    id: Mapped[str] = mapped_column(
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False,
    )

    level: Mapped[NotifyLevel] = mapped_column(
        postgresql.ENUM(
            NotifyLevel,
            name="notifylevel",
            schema="server",
        ),
        
        default=NotifyLevel.SYSTEM,
        nullable=False,
    )

    message: Mapped[str] = mapped_column(
        String(2000),
    )

    link: Mapped[str] = mapped_column(
        String(200),
    )

    is_admin_only: Mapped[bool] = mapped_column(
        nullable=False,
        server_default=false(),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

class NotificationStatuses(Base):
    __tablename__ = "notification_statuses"
    __table_args__ = {"schema":"server"}

    id: Mapped[str] = mapped_column(
        primary_key=True,
        nullable=False,
    )

    notification_id: Mapped[str] = mapped_column(
        nullable=False,
    )

    user_id: Mapped[int] = mapped_column(
        nullable=False,
    )

    is_read: Mapped[bool] = mapped_column(
        default=False,
    )

class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (   
        CheckConstraint("amount >= 0", name="check_amount_min_value"),
        {"schema": "economy_donation"}
    )
    inx: Mapped[int] = mapped_column(primary_key=True)

    io: Mapped[TransactionIO] = mapped_column(
       postgresql.ENUM(
           TransactionIO,
           name="transactionio",
           schema="economy_donation"
       )
    )

    amount: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    issuer: Mapped[str | None] = mapped_column(
        String(50),
        server_default="anonymous",
        nullable=False,
    )

    payment_method: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True, # temporary
    )

    status: Mapped[TransactionStatus] = mapped_column(
        postgresql.ENUM(
            TransactionStatus,
            name="transactionstatus",
            schema="economy_donation",
        ),
        default=TransactionStatus.PENDING,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    last_modified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    last_modified_by: Mapped[str | None] = mapped_column(
        String(100),
        server_default="system",
        nullable=False,
    )

    last_modified_by_user_id: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )

class Goal(Base):
    __tablename__ = "goals"
    __table_args__ = {"schema": "economy_donation"}

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
        postgresql.ENUM(
            GoalStatus,
            name="goalstatus",
            schema="economy_donation"
        ),
        server_default=GoalStatus.UPCOMING
    )

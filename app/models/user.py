from datetime import datetime
import uuid

from sqlalchemy import ARRAY, DateTime, String, func
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class User(Base):
    __tablename__ = "user"
    __table_args__ = {"schema": "community_fund"}

    id: Mapped[int] = mapped_column(primary_key=True)

    username: Mapped[str] = mapped_column(
        String(30),
        unique=True,
        nullable=False
    )

    email: Mapped[str] = mapped_column(
        unique=True,
        nullable=False
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    is_admin: Mapped[bool] = mapped_column(
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

class Session(Base):
    __tablename__ = "session"
    __table_args__ = {"schema": "server"}

    id: Mapped[str] = mapped_column(
        String(255),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    user_id: Mapped[int] = mapped_column(
        nullable=False
    )

    session_id: Mapped[list[str]] = mapped_column(
        MutableList.as_mutable(ARRAY(String)),
        default=list
    )
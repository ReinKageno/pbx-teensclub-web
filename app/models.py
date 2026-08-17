from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class Transaction(Base):
    __tablename__ = "transactions"

    id:Mapped[int] = mapped_column(primary_key=True)
    type:Mapped[str]
    amount:Mapped[int]
    description:Mapped[str]
    donor_name:Mapped[str | None]
    status:Mapped[str]
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import TransactionStatus, TransactionIO


class TransactionBase(BaseModel):
    inx: int
    issuer: str
    amount: int
    description: str | None
    created_at: datetime

class UserTransactionCreate(BaseModel):
    issuer: str | None = Field(default=None, max_length=50)
    amount: int = Field(gt=10000)
    description: str | None = Field(default=None, max_length=500)
    payment_method: str | None = None

    @field_validator("issuer", mode="before")
    @classmethod
    def normalize_issuer(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    model_config = ConfigDict(extra="forbid")

class AdminTransactionCreate(UserTransactionCreate):
    amount: int = Field(gt=0)
    io: TransactionIO | None = TransactionIO.INCOME
    status: TransactionStatus | None = TransactionStatus.PENDING

class TransactionResponse(TransactionBase):
    issuer: str | None
    io: TransactionIO
    status: TransactionStatus

    model_config = {
        "from_attributes": True 
    }

class TransactionExpense(TransactionBase):
    pass

class TransactionRecent(BaseModel):
    recent_transactions: list[TransactionResponse]
    recent_expenses: list[TransactionExpense]

class TransactionRecentWithSum(TransactionRecent):
    income: int
    expense: int
    balance: int

class TransactionUpdate(BaseModel):
    issuer: str | None = Field(default=None, min_length=1, max_length=50)
    amount: int | None = Field(default=None, gt=0)
    description: str | None = Field(default=None, max_length=500)
    payment_method: str | None = Field(default=None, max_length=50)
    status: TransactionStatus | None = None
    io: TransactionIO | None = None

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

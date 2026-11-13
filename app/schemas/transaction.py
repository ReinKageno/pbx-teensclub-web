from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import TransactionStatus, TransactionType


class TransactionBase(BaseModel):
    id: int
    issuer: str
    amount: int
    description: str | None
    created_at: datetime

class UserTransactionCreate(BaseModel):
    issuer: str | None = None
    amount: int
    description: str | None = Field(default=None, max_length=500)
    payment_method: str | None = None

    model_config = ConfigDict(extra="forbid")

class AdminTransactionCreate(UserTransactionCreate):
    type: TransactionType
    status: TransactionStatus

class TransactionResponse(TransactionBase):
    issuer: str | None
    type: TransactionType
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
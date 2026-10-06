from datetime import datetime

from pydantic import BaseModel

from app.models.transaction import TransactionStatus, TransactionType


class TransactionCreate(BaseModel):
    issuer: str | None = None
    amount: int
    type: TransactionType
    description: str | None = None
    payment_method: str | None = None

class TransactionResponse(BaseModel):
    id: int
    issuer: str | None
    amount: int
    type: TransactionType
    description: str | None
    status: TransactionStatus
    created_at: datetime

    model_config = {
        "from_attributes": True 
    }

class ExpenseResponse(BaseModel):
    id: int
    issuer: str
    amount: int
    description: str | None
    created_at: datetime

class TransactionSummaryResponse(BaseModel):
    income: int
    expense: int
    balance: int
    recent_transactions: list[TransactionResponse]
    recent_expenses: list[ExpenseResponse]
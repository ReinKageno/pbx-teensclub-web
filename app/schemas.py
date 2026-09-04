from datetime import date, datetime

from app.models import GoalStatus, Transaction, TransactionType, TransactionStatus
from pydantic import BaseModel

class TransactionCreate(BaseModel):
    type: TransactionType
    amount: int
    description: str | None = None
    issuer: str | None = None
    payment_method: str | None = None

class TransactionResponse(BaseModel):
    id: int
    type: TransactionType
    amount: int
    description: str | None
    issuer: str | None
    status: TransactionStatus
    created_at: datetime

    model_config = {
        "from_attributes": True 
    }

class GoalCreate(BaseModel):
    name: str
    description: str | None = None
    target_amount: int
    start_date: date
    end_date: date | None = None
    status: GoalStatus

class GoalResponse(BaseModel):
    id: int
    name: str
    description: str | None
    target_amount: int
    start_date: date
    end_date: date | None
    created_at: datetime
    status: GoalStatus

    model_config = {
        "from_attributes": True
    }

class EconomyResponse(BaseModel):
    income: int
    expense: int
    balance: int

class ExpenseResponse(BaseModel):
    id: int
    issuer: str
    amount: int
    description: str | None
    created_at: datetime

class TransactionSummaryResponse(BaseModel):
    recent_transactions: list[TransactionResponse]
    recent_expenses: list[ExpenseResponse]
    deposit: EconomyResponse
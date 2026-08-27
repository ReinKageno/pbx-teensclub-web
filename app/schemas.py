from datetime import date, datetime

from app.models import GoalStatus, TransactionType, TransactionStatus
from pydantic import BaseModel

class TransactionCreate(BaseModel):
    type: TransactionType
    amount: int
    description: str | None = None
    donor_name: str | None = None
    payment_method: str | None = None

class TransactionResponse(BaseModel):
    id: int
    type: TransactionType
    amount: int
    description: str | None
    donor_name: str | None
    status: TransactionStatus
    created_at: datetime

    model_config = {
        "from_attributes": True 
    }

class GoalCreate(BaseModel):
    name: str
    description: str | None = None
    target_amount: int
    target_date: date | None = None
    start_date: date
    goal_status: GoalStatus

class GoalResponse(BaseModel):
    id: int
    name: str
    description: str | None
    target_amount: int
    target_date: date | None
    start_date: date
    created_at: datetime
    goal_status: GoalStatus

    model_config = {
        "from_attributes": True
    }

class TransactionSummaryResponse(BaseModel):
    income: int
    expense: int
    balance: int
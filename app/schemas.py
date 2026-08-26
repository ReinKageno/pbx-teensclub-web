from datetime import datetime

from app.models import TransactionType, TransactionStatus
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
    target_date: datetime | None = None
    start_date: datetime

class GoalResponse(BaseModel):
    id: int
    name: str
    description: str | None
    target_amount: int
    target_date: datetime | None
    start_date: datetime
    created_at: datetime

    model_config = {
        "from_attributes": True
    }
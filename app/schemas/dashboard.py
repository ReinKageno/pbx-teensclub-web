from pydantic import BaseModel

from .transaction import TransactionResponse


class DashboardGoalResponse(BaseModel):
    goal: str
    goal_id: int
    current_amount: int
    target_amount: int
    progress: float
    status: str

class DashboardResponse(BaseModel):
    income: int
    expense: int
    balance: int
    goal: list[DashboardGoalResponse]
    recent_transactions: list[TransactionResponse]
    recent_expenses: list[TransactionResponse]
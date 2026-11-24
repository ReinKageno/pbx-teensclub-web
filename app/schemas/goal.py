
from datetime import date, datetime

from pydantic import BaseModel

from app.models.enums import GoalStatus


class GoalBase(BaseModel):
    name: str
    description: str | None = None
    target_amount: int
    start_date: date
    end_date: date | None = None

class GoalCreate(GoalBase):
    pass

class GoalResponse(GoalBase):
    GoalBase
    created_at: datetime
    status: GoalStatus
    id: int

    model_config = {
        "from_attributes": True
    }

class GoalProgressResponse(GoalResponse):
    current_amount: int
    progress: float


from datetime import date, datetime

from pydantic import BaseModel

from app.models.goal import GoalStatus


class GoalCreate(BaseModel):
    name: str
    description: str | None = None
    target_amount: int
    start_date: date
    end_date: date | None = None

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

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import common_id_limit_parameters
from app.function import get_current_admin
from app.function.donation_services import goal_calculator
from app.models import Goal, User
from app.schemas.goal import GoalCreate, GoalProgressResponse, GoalResponse


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/goals",
    tags=["Donation"]
)


@router.post("", response_model=GoalResponse)
def create_goal(goal: GoalCreate, db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    db_goal = Goal(
        name=goal.name,
        description=goal.description,
        target_amount=goal.target_amount,
        start_date=goal.start_date,
        end_date=goal.end_date,
    )

    db.add(db_goal)
    db.commit()
    db.refresh(db_goal)

    return db_goal


@router.get("", response_model=list[GoalProgressResponse] | GoalProgressResponse)
def get_goals(commons: Annotated[dict, Depends(common_id_limit_parameters)], db: Session = Depends(get_db)):
    goals = goal_calculator(db, extract_history=True)
    target_id = commons["target_id"]
    if target_id is not None:
        goal = next((item for item in goals if item["goal_id"] == target_id), None)
        if goal is None:
            raise HTTPException(status_code=404, detail="Goal not found")
        return goal

    goals = goals[:commons["limit"]]
    if not goals:
        raise HTTPException(
            status_code=404,
            detail="No goals found"
        )

    return goals

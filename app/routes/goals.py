from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.commons import common_limit_parameters
from app.models.goal import Goal
from app.schemas.goal import GoalCreate, GoalResponse

router = APIRouter(
    prefix="/goals"
)


@router.post("", response_model=GoalResponse)
def create_goal(
    goal: GoalCreate,
    db: Session = Depends(get_db),
):
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

@router.get("", response_model=list[GoalResponse]|GoalResponse)
def get_goals(
        commons: Annotated[dict, Depends(common_limit_parameters)],
        db: Session = Depends(get_db)
    ):
    if commons["target_id"] is not None:
        goal = db.query(Goal).filter(Goal.id == commons["target_id"]).first()
    else:
        goal = db.query(Goal).limit(limit=commons["limit"]).all()

    if not goal:
        raise HTTPException(
            status_code=404,
            detail="Goal not found"
        )

    return goal
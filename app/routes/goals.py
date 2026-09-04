from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Goal
from app.schemas import GoalCreate, GoalResponse

router = APIRouter(
    prefix="/goals"
)


async def goal_parameters(id: int | None = None, limit: int | None = 100):
    if 1 <= limit <= 100:
        _limit = limit
    else:
        raise HTTPException(
            status_code=422,
            detail=f"'limit' parameter out of range: {limit}"
        )


    return {"goal_id": id, "limit": _limit}

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
        commons: Annotated[dict, Depends(goal_parameters)],
        db: Session = Depends(get_db)
    ):
    if not commons["goal_id"]:
        goal = db.query(Goal).limit(limit=commons['limit']).all()
    else:
        goal = db.query(Goal).filter(Goal.id == commons['goal_id']).first()

    if goal is None:
        raise HTTPException(
            status_code=404,
            detail="Goal not found"
        )

    return goal
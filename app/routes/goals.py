from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Goal
from app.schemas import GoalCreate, GoalResponse

router = APIRouter(
    prefix="/goals"
)


@router.post("/", response_model=GoalResponse)
def create_goal(
    goal: GoalCreate,
    db: Session = Depends(get_db),
):
    db_goal = Goal(
        name=goal.name,
        description=goal.description,
        target_amount=goal.target_amount,
        target_date=goal.target_date,
        start_date=goal.start_date,
    )

    db.add(db_goal)
    db.commit()
    db.refresh(db_goal)

    return db_goal

@router.get("/", response_model=list[GoalResponse])
def get_goals(db: Session = Depends(get_db)):
    goals = db.query(Goal).all()

    return goals

@router.get("/{goal_id}", response_model=GoalResponse)
def get_goal(
    goal_id: int,
    db: Session = Depends(get_db),
):
    goal = db.query(Goal).filter(Goal.id == goal_id).first()

    if goal is None:
        raise HTTPException(
            status_code=404,
            detail="Goal not found"
        )

    return goal
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Goal, GoalStatus, Transaction, TransactionStatus, TransactionType

router = APIRouter(
    prefix="/dashboard"
)

@router.get("")
def get_dashboard(db: Session = Depends(get_db)):
    income, expense, balance = calculate_balance(db)

    goal_progress = goal_calculator(db)

    recent_transactions = (
        db.query(Transaction)
        .filter(Transaction.type == TransactionType.INCOME)
        .order_by(Transaction.created_at.desc())
        .limit(10)
        .all()
    )

    recent_expenses = (
        db.query(Transaction)
        .filter(Transaction.type == TransactionType.EXPENSE)
        .order_by(Transaction.created_at.desc())
        .limit(10)
        .all()
    )

    return {
        "income": income,
        "expense": expense,
        "balance": balance,
        "goal": goal_progress,
        "recent_transactions": recent_transactions,
        "recent_expenses": recent_expenses,
    }

def calculate_balance(transactions: Session):
    income = transactions.scalar(
        select(func.coalesce(func.sum(Transaction.amount), 0))
        .where(Transaction.status == TransactionStatus.CONFIRMED, Transaction.type == TransactionType.INCOME)
    )

    expense = transactions.scalar(
        select(func.coalesce(func.sum(Transaction.amount), 0))
        .where(Transaction.status == TransactionStatus.CONFIRMED, Transaction.type == TransactionType.EXPENSE)
    )

    balance = income - expense

    return income, expense, balance

def goal_calculator(db: Session, extract_history: bool = False) -> list:
    goals: list[Goal] = []

    if extract_history:
        history = db.scalars(select(Goal)
            .where(Goal.status == GoalStatus.FINISHED)
            .limit(10)
        ).all()

        goals.extend(history)

    active_goal = db.scalars(
        select(Goal)
        .where(Goal.status == GoalStatus.ACTIVE)
    ).first()

    if active_goal is not None:
        goals.append(active_goal)

    print(goals)

    def calc_goal(database: Goal):
        return db.scalar(
            select(func.coalesce(func.sum(Transaction.amount), 0))
            .where(
                Transaction.status == TransactionStatus.CONFIRMED,
                func.date(Transaction.created_at) >= database.start_date,
                func.date(Transaction.created_at) <= database.end_date
            )
        )
    
    result = []

    for goal in goals:
        current_amount = calc_goal(goal)
        progress = (current_amount / goal.target_amount) * 100

        result.append({
            "goal": goal.name,
            "goal_id": goal.id,
            "current_amount": current_amount,
            "target_amount": goal.target_amount,
            "progress": progress,
            "status": goal.status,
        })

    return result
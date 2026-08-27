from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Goal, Transaction, TransactionStatus, TransactionType

router = APIRouter(
    prefix="/dashboard"
)

@router.get("/")
def get_dashboard(
    db: Session = Depends(get_db)
):
    transactions = db.query(Transaction).all()
    goals = db.query(Goal).all()
    # current_goal = db.query(Goal).filter(func.date(Goal.start_date) >= func.current_date()).first()

    income, expense = calculate_balance(transactions)
    balance = income - expense

    goal_progress = []

    for goal in goals:
        goal_progress.append(goal_calculator(transactions, goal))

    recent_transactions = (
        db.query(Transaction)
        .order_by(Transaction.created_at.desc())
        .limit(10)
        .all()
    )

    return {
        "income": income,
        "expense": expense,
        "balance": balance,
        "goals": goal_progress,
        "recent_transactions": recent_transactions,
    }

def calculate_balance(transactions):
    income = 0
    expense = 0

    for transaction in transactions:
        if transaction.type == TransactionType.INCOME:
            income += transaction.amount
        elif transaction.type == TransactionType.EXPENSE:
            expense += transaction.amount

    return income, expense

def goal_calculator(transactions, goal):
    current_amount = 0

    for transaction in transactions:
        if transaction.type != TransactionType.INCOME:
            continue

        if transaction.status != TransactionStatus.CONFIRMED:
            continue

        created_date = transaction.created_at.date()

        if created_date < goal.start_date:
            continue

        if goal.target_date and created_date > goal.target_date:
            continue

        current_amount += transaction.amount

    progress = (
        current_amount / goal.target_amount
    ) * 100

    return {
        "current_amount": current_amount,
        "target_amount": goal.target_amount,
        "progress": progress,
    }
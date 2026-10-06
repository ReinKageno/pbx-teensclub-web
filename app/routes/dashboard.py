from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.transaction import Transaction, TransactionType
from app.models.user import User
from app.schemas.dashboard import DashboardResponse
from app.services.goal_service import goal_calculator
from app.services.transaction_service import calculate_balance

router = APIRouter()

@router.get("/dashboard", response_model=DashboardResponse)
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
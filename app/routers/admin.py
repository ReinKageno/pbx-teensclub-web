from fastapi import APIRouter, Depends, Request, logger
from sqlalchemy.orm import Session

from app import templates
from app.database.session import get_db
from app.function.transaction_services import query_transactions
from app.function.donation_services import sum_total_donation
from app.function.user_services import get_current_admin
from app.models import Transaction, User

router = APIRouter(
    prefix="/admin",
    tags=["Admin","Dashboard"],
)

@router.get("/donation/activity")
def get_recent(request: Request, _: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    transactions = (
        db.query(Transaction)
        .order_by(Transaction.created_at.desc())
        .all()
    )

    return templates.TemplateResponse(
        request=request,
        name="donation/activity.html",
        context={
            "transactions": transactions,
        },
    )


@router.get("/dashboard")
def dashboard(request: Request, user: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    transactions_error = False

    try:
        transactions = query_transactions(db=db)  # Fetch recent transactions from the database
    except Exception:
        logger.exception("Failed to fetch dashboard transactions.")
        transactions = []
        transactions_error = True

    total_incomes, total_expenses, balance = sum_total_donation(db)
    
    summary = {
        "total_income": total_incomes,
        "total_expenses": total_expenses,
        "balance": balance,
        "confirmed_donations": None,
    }

    return templates.TemplateResponse(
        request=request,
        name="dashboard/dashboard.html",
        context={
            "summary": summary,
            "transactions": transactions,
            "transactions_error": transactions_error,
            "current_user": {"display_name": user.username, "role": "Administrator"},
            "chart_data": [],  # Optional; see below
            "expense_categories": [],  # Optional
            "activities": [],  # Optional
            "current_year": 2026,
        },
    )
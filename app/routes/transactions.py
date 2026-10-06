
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.commons import common_limit_parameters
from app.models.transaction import Transaction, TransactionType
from app.schemas.transaction import TransactionCreate, TransactionResponse, TransactionSummaryResponse
from app.services.transaction_service import calculate_recent_balance

router = APIRouter(
    prefix="/transactions"
)


@router.post("", response_model=TransactionResponse)
def create_transaction(
    transaction: TransactionCreate,
    db: Session = Depends(get_db),
):
    db_transaction = Transaction(
        type=transaction.type,
        amount=transaction.amount,
        description=transaction.description,
        issuer=transaction.issuer,
        payment_method=transaction.payment_method,
        status="confirmed",
    )

    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)

    return db_transaction

@router.get("", response_model=list[TransactionResponse]|TransactionResponse)
def get_transactions(
    commons: Annotated[dict, Depends(common_limit_parameters)],
    db: Session = Depends(get_db),
):
    if commons["target_id"] is not None:
        transactions = db.query(Transaction).filter(Transaction.id == commons["target_id"]).first()
    else:
        transactions = db.query(Transaction).limit(limit=commons["limit"]).all()

    if not transactions:
        raise HTTPException(
            status_code=404,
            detail="No transactions found"
        )

    return transactions

@router.get("/summary", response_model=TransactionSummaryResponse)
def get_summary(transactions: Session = Depends(get_db)):
    income, expense, net_balance = calculate_recent_balance(transactions)

    recent_transactions:list[Transaction] = (
        transactions.query(Transaction)
        .filter(Transaction.type == TransactionType.INCOME)
        .order_by(Transaction.created_at.desc())
        .limit(10)
        .all()
    )

    recent_expenses:list[Transaction] = (
        transactions.query(Transaction)
        .filter(Transaction.type == TransactionType.EXPENSE)
        .order_by(Transaction.created_at.desc())
        .limit(10)
        .all()
    )

    return {
        "income": income,
        "expense": expense,
        "balance": net_balance,
        "recent_transactions": recent_transactions,
        "recent_expenses": recent_expenses,
    }
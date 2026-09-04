from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Transaction, TransactionStatus, TransactionType
from app.schemas import TransactionCreate, TransactionResponse, TransactionSummaryResponse

router = APIRouter(
    prefix="/transactions"
)


async def transaction_parameters(id: int | None = None, limit: int | None = 100):
    if 1 <= limit <= 100:
        _limit = limit
    else:
        raise HTTPException(
            status_code=422,
            detail=f"'limit' parameter out of range: {limit}"
        )

    return {"transaction_id": id, "limit": _limit}

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
    commons: Annotated[dict, Depends(transaction_parameters)],
    db: Session = Depends(get_db),
):
    if commons["transaction_id"]:
        transactions = db.query(Transaction).filter(Transaction.id == commons["transaction_id"]).first()
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
    income, expense, net_balance = calculate_balance(transactions)

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
        "recent_transactions": recent_transactions,
        "recent_expenses": recent_expenses,
        "deposit": {
            "income": income,
            "expense": expense,
            "balance": net_balance,
        },
    }

def calculate_balance(db: Session, confirmed_only: bool = False, limit: int = 365):
    if not (1 <= limit <= 365):
        limit = 1 if limit < 1 else 365

    if confirmed_only:
        income = db.scalar(
            select(func.coalesce(func.sum(Transaction.amount), 0))
            .where(Transaction.status == TransactionStatus.CONFIRMED, Transaction.type == TransactionType.INCOME)
            .limit(limit=limit)
        )
    
        expense = db.scalar(
            select(func.coalesce(func.sum(Transaction.amount), 0))
            .where(Transaction.status == TransactionStatus.CONFIRMED, Transaction.type == TransactionType.EXPENSE)
            .limit(limit=limit)
        )

    else:
        income = db.scalar(
            select(func.coalesce(func.sum(Transaction.amount), 0))
            .where(Transaction.type == TransactionType.INCOME)
            .limit(limit=limit)
        )

        expense = db.scalar(
            select(func.coalesce(func.sum(Transaction.amount), 0))
            .where(Transaction.type == TransactionType.EXPENSE)
            .limit(limit=limit)
        )

    if not income:
        income = 0

    if not expense:
        expense = 0

    balance = income - expense

    return income, expense, balance
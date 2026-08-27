from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Transaction, TransactionType
from app.schemas import TransactionCreate, TransactionResponse, TransactionSummaryResponse

router = APIRouter(
    prefix="/transactions"
)


@router.post("/", response_model=TransactionResponse)
def create_transaction(
    transaction: TransactionCreate,
    db: Session = Depends(get_db),
):
    db_transaction = Transaction(
        type=transaction.type,
        amount=transaction.amount,
        description=transaction.description,
        donor_name=transaction.donor_name,
        payment_method=transaction.payment_method,
        status="confirmed",
    )

    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)

    return db_transaction

@router.get("/", response_model=list[TransactionResponse])
def get_transactions(
    limit: int = Query(default=1, ge=1, le=100),
    db: Session = Depends(get_db)
):
    transactions = db.query(Transaction).limit(limit=limit).all()

    return transactions

@router.get("/summary", response_model=TransactionSummaryResponse)
def calculate_balance(transactions: Session = Depends(get_db)):
    transaction = transactions.query(Transaction).all()
    income = 0
    expense = 0

    for transaction in transactions:
        if transaction.type == TransactionType.INCOME:
            income += transaction.amount

        elif transaction.type == TransactionType.EXPENSE:
            expense += transaction.amount

    return {
        "income": income,
        "expense": expense,
        "balance": income - expense
    }
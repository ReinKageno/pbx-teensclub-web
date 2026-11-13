
from fastapi import Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models import Transaction
from app.models.enums import TransactionType
from app.services.exceptions import ResourceNotFoundError


def query_transactions(limit: int = 10, db: Session = Depends(get_db)):
    transactions:list[Transaction] = (
        db.query(Transaction)
        .order_by(Transaction.created_at.desc())
        .limit(limit)
        .all()
    )

    return transactions

def query_recent_incomes(limit: int = 10, db: Session = Depends(get_db)):
    recent_incomes:list[Transaction] = (
        db.query(Transaction)
        .filter(Transaction.type == TransactionType.INCOME)
        .order_by(Transaction.created_at.desc())
        .limit(limit)
        .all()
    )

    if not recent_incomes:
        raise ResourceNotFoundError("Transaction not found.")

    return recent_incomes
    
def query_recent_expenses(limit: int = 10, db: Session = Depends(get_db)):
    recent_expenses:list[Transaction] = (
        db.query(Transaction)
        .filter(Transaction.type == TransactionType.EXPENSE)
        .order_by(Transaction.created_at.desc())
        .limit(limit)
        .all()
    )

    if not recent_expenses:
        raise ResourceNotFoundError("Transaction not found.")
    
    return recent_expenses

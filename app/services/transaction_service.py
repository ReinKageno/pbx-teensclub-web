
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.transaction import Transaction, TransactionStatus, TransactionType


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


def calculate_recent_balance(db: Session, confirmed_only: bool = False, limit: int = 365):
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
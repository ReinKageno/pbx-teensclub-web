
from datetime import date, datetime
import asyncio

from fastapi import Depends
from sqlalchemy import func, select, case
from sqlalchemy.orm import Session

from app.database import SessionLocal, get_db
from app.models.enums import GoalStatus, TransactionStatus, TransactionIO
from app.models import Transaction, Goal


def sum_total_donation(
    db: Session = Depends(get_db),
):
    stmt = select(
        func.coalesce(
            func.sum(case(
                (Transaction.io == TransactionIO.INCOME, Transaction.amount),
                else_=0,
            )),
        0,).label("income"),
        func.coalesce(
            func.sum(case(
                (Transaction.io == TransactionIO.EXPENSE, Transaction.amount),
                else_=0,
            )),0,).label("expense"),
    ).where(Transaction.status == TransactionStatus.CONFIRMED,)

    result = db.execute(stmt).one()

    balance = result.income - result.expense

    return result.income, result.expense, balance

def sum_recent_donation(
    confirmed_only: bool = False,
    limit: int = 365,
    db: Session = Depends(get_db),
):
    if not (1 <= limit <= 365):
        limit = 1 if limit < 1 else 365

    if confirmed_only:
        income = db.scalar(
            select(func.coalesce(func.sum(Transaction.amount), 0))
            .where(Transaction.status == TransactionStatus.CONFIRMED, Transaction.io == TransactionIO.INCOME)
            .limit(limit=limit)
        )
    
        expense = db.scalar(
            select(func.coalesce(func.sum(Transaction.amount), 0))
            .where(Transaction.status == TransactionStatus.CONFIRMED, Transaction.io == TransactionIO.EXPENSE)
            .limit(limit=limit)
        )

    else:
        income = db.scalar(
            select(func.coalesce(func.sum(Transaction.amount), 0))
            .where(Transaction.io == TransactionIO.INCOME)
            .limit(limit=limit)
        )

        expense = db.scalar(
            select(func.coalesce(func.sum(Transaction.amount), 0))
            .where(Transaction.io == TransactionIO.EXPENSE)
            .limit(limit=limit)
        )

    if not income:
        income = 0

    if not expense:
        expense = 0

    balance = income - expense

    return income, expense, balance


def update_goal_status() -> list:
    db: Session = SessionLocal()
    try:
        now = date.today()

        update_upcoming = (
            db.query(Goal)
            .filter(
                Goal.status == GoalStatus.UPCOMING,
                Goal.start_date <= now,
                Goal.end_date > now,
            )
            .update(
                {Goal.status:GoalStatus.ACTIVE},
                synchronize_session=False
            )
        )

        update_skipped = (
            db.query(Goal)
            .filter(
                GoalStatus == GoalStatus.UPCOMING,
                Goal.end_date < now,
            )
            .update(
                {Goal.status:GoalStatus.FINISHED},
                synchronize_session=False
            )
        )

        update_active = (
            db.query(Goal)
            .filter(
                Goal.status == GoalStatus.ACTIVE,
                Goal.end_date < now,
            )
            .update(
                {Goal.status:GoalStatus.FINISHED},
                synchronize_session=False
            )
        )

        db.commit()

        return update_upcoming + update_skipped + update_active
    except Exception:
        db.rollback()
        raise

    finally:
        db.close()

async def schedule_update_goal(interval_minutes: int, stop_event: asyncio.Event):
    """Refresh goal statuses periodically until the application shuts down."""
    interval_seconds = interval_minutes * 60
    print(f"Starting updater every {interval_minutes} minutes...")

    while not stop_event.is_set():
        try:
            count = await asyncio.to_thread(update_goal_status)
            if count:
                print(f"{datetime.now().replace(microsecond=0)} Updated {count} goals.")
            else:
                print(f"{datetime.now().replace(microsecond=0)} No goals updated.")
        except Exception as e:
            print(f"Error during update: {e}")

        try:
            await asyncio.wait_for(stop_event.wait(), timeout=interval_seconds)
        except asyncio.TimeoutError:
            pass

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

    def calc_goal(database: Goal):
        return db.scalar(
            select(func.coalesce(func.sum(Transaction.amount), 0))
            .where(
                Transaction.status == TransactionStatus.CONFIRMED,
                func.date(Transaction.created_at) >= database.start_date,
                func.date(Transaction.created_at) <= database.end_date,
                Transaction.io == TransactionIO.INCOME,
            )
        )
    
    result = []

    for goal in goals:
        current_amount = calc_goal(goal)
        progress = (current_amount / goal.target_amount) * 100
        progress_ = progress if progress <= 100 else 0 if progress <= 0 else 100

        result.append({
            "goal": goal.name,
            "goal_id": goal.id,
            "current_amount": current_amount,
            "target_amount": goal.target_amount,
            "progress": progress_,
            "status": goal.status,
        })

    return result

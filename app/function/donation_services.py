
from datetime import date, datetime, timedelta
import asyncio

from fastapi import Depends
from sqlalchemy import func, select, case, or_
from sqlalchemy.orm import Session

from app.database import SessionLocal, get_db
from app.models.enums import GoalStatus, TransactionStatus, TransactionIO
from app.models import Transaction, Goal


def sum_total_donation(
    db: Session,
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
                or_(Goal.end_date.is_(None), Goal.end_date > now),
            )
            .update(
                {Goal.status:GoalStatus.ACTIVE},
                synchronize_session=False
            )
        )

        update_skipped = (
            db.query(Goal)
            .filter(
                Goal.status == GoalStatus.UPCOMING,
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

def goal_calculator(
    db: Session,
    extract_history: bool = False,
    goal_id: int | None = None,
    limit: int | None = None,
) -> list:
    """Calculate milestone progress by passing one fund total through its date chain.

    Exact date-range duplicates are chained by creation order. Consecutive
    inclusive date ranges are chained when the prior end date is the day before
    the next start date. A gap intentionally starts a new fund chain.
    """
    all_goals = db.scalars(
        select(Goal).order_by(Goal.start_date, Goal.created_at, Goal.id)
    ).all()
    goals_by_id = {goal.id: goal for goal in all_goals}

    # Build one predecessor link per milestone. Duplicate periods take priority;
    # otherwise a milestone can follow one whose inclusive date range ends the
    # day before it starts.
    previous_goal: dict[int, int] = {}
    last_by_dates: dict[tuple[date, date | None], Goal] = {}
    ending_on: dict[date, list[Goal]] = {}
    for goal in all_goals:
        date_key = (goal.start_date, goal.end_date)
        exact_previous = last_by_dates.get(date_key)
        if exact_previous is not None:
            previous_goal[goal.id] = exact_previous.id
        else:
            adjacent_candidates = ending_on.get(goal.start_date - timedelta(days=1), [])
            if adjacent_candidates:
                prior = max(
                    adjacent_candidates,
                    key=lambda item: (item.start_date, item.created_at, item.id),
                )
                previous_goal[goal.id] = prior.id

        last_by_dates[date_key] = goal
        if goal.end_date is not None:
            ending_on.setdefault(goal.end_date, []).append(goal)

    if goal_id is not None:
        requested_goals = [goals_by_id[goal_id]] if goal_id in goals_by_id else []
    else:
        statuses = [GoalStatus.ACTIVE, GoalStatus.UPCOMING]
        if extract_history:
            statuses.append(GoalStatus.FINISHED)
        requested_goals = [goal for goal in all_goals if goal.status in statuses]
        if limit is not None:
            requested_goals = requested_goals[:limit]

    today = date.today()
    income_cache: dict[tuple[date, date], int] = {}
    result = []

    for goal in requested_goals:
        chain = [goal]
        seen = {goal.id}
        while chain[-1].id in previous_goal:
            prior_id = previous_goal[chain[-1].id]
            if prior_id in seen:
                break
            chain.append(goals_by_id[prior_id])
            seen.add(prior_id)

        oldest_goal = chain[-1]
        range_start = oldest_goal.start_date
        range_end = goal.end_date # min(goal.end_date or today, today) to exclude future income.
        cache_key = (range_start, range_end)

        if range_end < range_start:
            chain_income = 0
        elif cache_key not in income_cache:
            income_cache[cache_key] = db.scalar(
                select(func.coalesce(func.sum(Transaction.amount), 0)).where(
                    Transaction.io == TransactionIO.INCOME,
                    Transaction.status == TransactionStatus.CONFIRMED,
                    func.date(Transaction.created_at) >= range_start,
                    func.date(Transaction.created_at) <= range_end,
                )
            ) or 0
            chain_income = income_cache[cache_key]
        else:
            chain_income = income_cache[cache_key]

        already_allocated = sum(prior.target_amount for prior in chain[1:])
        current_amount = min(
            max(chain_income - already_allocated, 0),
            goal.target_amount,
        )
        progress = (
            current_amount / goal.target_amount * 100
            if goal.target_amount > 0
            else 0
        )

        result.append({
            "goal": goal.name,
            "goal_id": goal.id,
            "id": goal.id,
            "name": goal.name,
            "description": goal.description,
            "start_date": goal.start_date,
            "end_date": goal.end_date,
            "created_at": goal.created_at,
            "current_amount": current_amount,
            "target_amount": goal.target_amount,
            "progress": progress,
            "status": goal.status,
        })

    return result

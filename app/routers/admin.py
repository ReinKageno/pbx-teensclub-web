from datetime import date, datetime, timedelta, timezone
import re

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import false, or_
from sqlalchemy.orm import Session

from app import templates, logger
from app.database.session import get_db
from app.function.transaction_services import query_transactions
from app.function.donation_services import goal_calculator, sum_total_donation
from app.function.user_services import get_current_admin
from app.models import Transaction, User
from app.models.enums import GoalStatus, TransactionStatus, TransactionIO
from app.services.exceptions import ResourceUnderConstructionError

router = APIRouter(
    prefix="/admin",
    tags=["Admin",],
)

TRANSACTION_PAGE_SIZE = 25
CHART_MONTHS = 12
TRANSACTION_FILTER_PATTERN = re.compile(
    r"#(?P<key>name|date|type|status|sort):\s*(?P<value>.*?)(?=\s+#(?:name|date|type|status|sort):|$)",
    re.IGNORECASE,
)
TRANSACTION_SORTS = {"newest", "oldest", "amount-high", "amount-low"}


def _monthly_income_expense_chart(db: Session, month_count: int = CHART_MONTHS):
    now = datetime.now(timezone.utc)
    current_month = now.year * 12 + now.month - 1
    month_keys = []
    for offset in range(month_count - 1, -1, -1):
        year, month_index = divmod(current_month - offset, 12)
        month_keys.append((year, month_index + 1))

    first_year, first_month = month_keys[0]
    start = datetime(first_year, first_month, 1, tzinfo=timezone.utc)
    next_year, next_month_index = divmod(current_month + 1, 12)
    end = datetime(next_year, next_month_index + 1, 1, tzinfo=timezone.utc)

    monthly_totals = {key: {"income": 0, "expense": 0} for key in month_keys}
    records = (
        db.query(Transaction.created_at, Transaction.io, Transaction.amount)
        .filter(
            Transaction.status != TransactionStatus.CANCELLED,
            Transaction.created_at >= start,
            Transaction.created_at < end,
        )
        .all()
    )
    for created_at, transaction_type, amount in records:
        key = (created_at.year, created_at.month)
        type_value = transaction_type.value if hasattr(transaction_type, "value") else transaction_type
        if key in monthly_totals and type_value in monthly_totals[key]:
            monthly_totals[key][type_value] += amount or 0

    highest_total = max(
        (max(totals.values()) for totals in monthly_totals.values()),
        default=0,
    )
    chart_data = []
    for year, month in month_keys:
        totals = monthly_totals[(year, month)]
        chart_data.append({
            "label": datetime(year, month, 1).strftime("%b"),
            "income": totals["income"],
            "expense": totals["expense"],
            "income_percent": round(totals["income"] * 100 / highest_total) if highest_total else 0,
            "expense_percent": round(totals["expense"] * 100 / highest_total) if highest_total else 0,
        })
    return chart_data


def _filtered_transactions(db: Session, q: str):
    query = db.query(Transaction)
    filter_matches = list(TRANSACTION_FILTER_PATTERN.finditer(q))
    parsed_filters = {
        match.group("key").lower(): match.group("value").strip()
        for match in filter_matches
    }
    plain_query = TRANSACTION_FILTER_PATTERN.sub(" ", q).strip()
    errors = []
    for match in filter_matches:
        if not match.group("value").strip() and match.group("key").lower() != "sort":
            errors.append(f"Provide a value after #{match.group('key').lower()}:")
            query = query.filter(false())

    if plain_query:
        term = f"%{plain_query}%"
        search_conditions = [
            Transaction.description.ilike(term),
            Transaction.issuer.ilike(term),
            Transaction.payment_method.ilike(term),
        ]
        id_search = plain_query.upper().removeprefix("#TRX-")
        if id_search.isdigit():
            search_conditions.append(Transaction.inx == int(id_search))
        query = query.filter(or_(*search_conditions))

    name = parsed_filters.get("name", "")
    if name:
        query = query.filter(Transaction.issuer.ilike(f"%{name}%"))

    transaction_type = parsed_filters.get("type", "").lower()
    if transaction_type:
        if transaction_type in {item.value for item in TransactionIO}:
            query = query.filter(Transaction.io == TransactionIO(transaction_type))
        else:
            errors.append("Use income or expense for #type.")
            query = query.filter(false())

    transaction_status = parsed_filters.get("status", "").lower()
    if transaction_status:
        if transaction_status in {item.value for item in TransactionStatus}:
            query = query.filter(Transaction.status == TransactionStatus(transaction_status))
        else:
            errors.append("Use pending, confirmed, or cancelled for #status.")
            query = query.filter(false())

    date_filter = parsed_filters.get("date", "")
    if date_filter:
        date_parts = re.split(r"\s+-\s+", date_filter, maxsplit=1)
        try:
            start_date = date.fromisoformat(date_parts[0])
            end_date = date.fromisoformat(date_parts[1]) if len(date_parts) == 2 else start_date
            if start_date.isoformat() != date_parts[0] or (len(date_parts) == 2 and end_date.isoformat() != date_parts[1]):
                raise ValueError
            if end_date < start_date:
                raise ValueError
            start_at = datetime(start_date.year, start_date.month, start_date.day, tzinfo=timezone.utc)
            end_at = datetime(end_date.year, end_date.month, end_date.day, tzinfo=timezone.utc) + timedelta(days=1)
            query = query.filter(Transaction.created_at >= start_at, Transaction.created_at < end_at)
        except ValueError:
            errors.append("Use #date: YYYY-MM-DD or #date: YYYY-MM-DD - YYYY-MM-DD.")
            query = query.filter(false())

    sort = parsed_filters.get("sort", "newest").lower()
    if sort not in TRANSACTION_SORTS:
        errors.append("Use newest, oldest, amount-high, or amount-low for #sort.")
        sort = "newest"

    return query, sort, errors


def _order_transactions(query, sort: str):
    if sort == "oldest":
        return query.order_by(Transaction.created_at.asc(), Transaction.inx.asc())
    if sort == "amount-high":
        return query.order_by(Transaction.amount.desc(), Transaction.inx.desc())
    if sort == "amount-low":
        return query.order_by(Transaction.amount.asc(), Transaction.inx.asc())
    return query.order_by(Transaction.created_at.desc(), Transaction.inx.desc())


def _account_issuers(db: Session, transactions: list[Transaction]) -> set[str]:
    issuer_names = {transaction.issuer for transaction in transactions if transaction.issuer}
    if not issuer_names:
        return set()
    return {
        username
        for (username,) in db.query(User.username).filter(User.username.in_(issuer_names)).all()
    }


@router.get("/dashboard", tags=['Dashboard'])
def dashboard(request: Request, user: User = Depends(get_current_admin), db: Session = Depends(get_db)):
    transactions_error = False

    try:
        transactions = query_transactions(db=db)  # Fetch recent transactions from the database
    except Exception:
        logger.exception("Failed to fetch dashboard transactions.")
        transactions = []
        transactions_error = True

    try:
        chart_data = _monthly_income_expense_chart(db)
    except Exception:
        logger.exception("Failed to build dashboard income and expense chart.")
        chart_data = []

    try:
        account_issuers = _account_issuers(db, transactions)

        total_incomes, total_expenses, balance = sum_total_donation(db)

        summary = {
            "total_income": total_incomes,
            "total_expenses": total_expenses,
            "balance": balance,
            "confirmed_donations": None,
        }

    except:
        logger.exception("Failed to fetch total amount of transactions.")
        account_issuers = []
        total_incomes = total_expenses = balance = -1
        summary = {}

    return templates.TemplateResponse(
        request=request,
        name="dashboard/dashboard.html",
        context={
            "summary": summary,
            "transactions": transactions,
            "account_issuers": account_issuers,
            "transactions_error": transactions_error,
            "current_user": {"display_name": user.username, "role": "Administrator"},
            "chart_data": chart_data,
            "expense_categories": [],  # Optional
            "activities": [],  # Optional
            "current_year": 2026,
        },
    )


@router.get("/dashboard/transactions", response_class=HTMLResponse, tags=['Dashboard'])
def dashboard_transactions(
    request: Request,
    q: str = Query(default="", max_length=300),
    user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    query, sort, filter_errors = _filtered_transactions(db, q)
    total_transactions = query.order_by(None).count()
    transactions = (
        _order_transactions(query, sort)
        .limit(TRANSACTION_PAGE_SIZE)
        .all()
    )
    context = {
        "transactions": transactions,
        "account_issuers": _account_issuers(db, transactions),
        "total_transactions": total_transactions,
        "has_more_transactions": total_transactions > len(transactions),
        "current_user": {"display_name": user.username, "role": "Administrator"},
        "q": q,
        "filter_errors": filter_errors,
    }
    return templates.TemplateResponse(
        request=request,
        name="dashboard/transactions.html",
        context=context,
    )


@router.get("/dashboard/transactions/more", response_class=HTMLResponse, tags=['Dashboard'])
def dashboard_transactions_more(
    request: Request,
    offset: int = Query(default=25, ge=0),
    q: str = Query(default="", max_length=300),
    _: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    query, sort, _ = _filtered_transactions(db, q)
    transactions = (
        _order_transactions(query, sort)
        .offset(offset)
        .limit(TRANSACTION_PAGE_SIZE + 1)
        .all()
    )
    has_more = len(transactions) > TRANSACTION_PAGE_SIZE
    response = templates.TemplateResponse(
        request=request,
        name="dashboard/_transaction_rows.html",
        context={
            "transactions": transactions[:TRANSACTION_PAGE_SIZE],
            "account_issuers": _account_issuers(db, transactions[:TRANSACTION_PAGE_SIZE]),
        },
    )
    response.headers["X-Has-More"] = "true" if has_more else "false"
    return response


@router.get("/dashboard/goals", tags=['Dashboard'])
def dashboard_goals(
    request: Request,
    user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    goals = goal_calculator(db, extract_history=True)
    active_goals = sorted(
        (goal for goal in goals if goal["status"] == GoalStatus.ACTIVE),
        key=lambda goal: (goal["start_date"], goal["id"]),
    )
    history_goals = sorted(
        (goal for goal in goals if goal["status"] == GoalStatus.FINISHED),
        key=lambda goal: (goal["end_date"] or goal["start_date"], goal["id"]),
        reverse=True,
    )

    return templates.TemplateResponse(
        request=request,
        name="dashboard/goals.html",
        context={
            "current_user": {"display_name": user.username, "role": "Administrator"},
            "current_year": datetime.now(timezone.utc).year,
            "current_goal": active_goals[0] if active_goals else None,
            "secondary_goals": active_goals[1:],
            "history_goals": history_goals,
        },
    )


@router.get("/users", tags=['User'])
def page_community(request: Request):
    logger.info("'users' page is unvailable")
    raise ResourceUnderConstructionError()


@router.get("/dashboard/report", tags=['Dashboard'])
def page_community(request: Request):
    logger.info("'dashboard/report' page is unvailable")
    raise ResourceUnderConstructionError()


@router.get("/dashboard/settings", tags=['Dashboard'])
def page_community(request: Request):
    logger.info("'dashboard/settings' page is unvailable")
    raise ResourceUnderConstructionError()

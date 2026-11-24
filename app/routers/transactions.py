
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app import templates, logger
from app.database.session import get_db
from app.function import AppSystem
from app.function.user_services import get_current_admin, get_optional_user
from app.models import Transaction, User
from app.models.enums import TransactionType, TransactionStatus
from app.schemas.transaction import AdminTransactionCreate, TransactionResponse, TransactionUpdate, UserTransactionCreate


router = APIRouter(
    prefix="/donation",
    tags=["Transactions", "Donation"],
)

# Register a donation request
@router.post("/new", response_model=TransactionResponse)
async def create_transaction(request: Request, user: User | None = Depends(get_optional_user), db: Session = Depends(get_db)):
    is_admin = user is not None and user.is_admin

    model = (
        AdminTransactionCreate
        if is_admin
        else UserTransactionCreate
    )

    form_data = await request.form()
    payload = dict(form_data)

    try:
        data = model.model_validate(payload)
    except ValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail=exc.errors(include_url=False)
        ) from exc

    if is_admin:
        # Admins can optionally attribute the transaction to someone else.
        data.issuer = data.issuer or user.username
    elif user is not None:
        # Regular users cannot submit a different issuer through the form.
        data.issuer = user.username
    else:
        data.issuer = data.issuer or "Anonymous"

    if is_admin:
        transaction_type = data.type
        transaction_status = data.status
    else:
        transaction_type = TransactionType.INCOME
        transaction_status = TransactionStatus.PENDING

    now = datetime.now(timezone.utc)

    db_transaction = Transaction(
        type=transaction_type,
        amount=data.amount,
        description=data.description,
        issuer=data.issuer,
        payment_method=data.payment_method,
        status=transaction_status,
        last_modified_at=now,
        last_modified_by=(
            str(user.user_id)
            if is_admin
            else AppSystem.NAME
        ),
    )

    try:
        db.add(db_transaction)
        db.commit()
        db.refresh(db_transaction)
    except SQLAlchemyError:
        db.rollback()
        logger.exception("Failed to create transaction")
        raise HTTPException(
            status_code=500,
            detail="Unable to create transaction",
        ) from None

    return db_transaction

# Donation form
@router.get("/new", response_class=HTMLResponse)
def new_transaction_page(
    request: Request,
    user: User | None = Depends(get_optional_user)
):
    return templates.TemplateResponse(
        request=request,
        name="donation/new.html",
        context={
            "user": user,
            "is_logged_in": user is not None,
            "is_admin": (
                user is not None
                and user.is_admin == True
            ),
            "transaction_types": list(TransactionType),
            "transaction_statuses": list(TransactionStatus),
        },
    )

@router.patch("/{transaction_id}", response_model=TransactionResponse)
def edit_transaction(
    transaction_id: int,
    changes: TransactionUpdate,
    user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    transaction = db.get(Transaction, transaction_id)
    if transaction is None:
        raise HTTPException(status_code=404, detail="Transaction not found")

    updates = changes.model_dump(exclude_unset=True, exclude_none=True)
    if not updates:
        raise HTTPException(status_code=422, detail="Provide at least one field to update")

    new_issuer = updates.get("issuer")
    if new_issuer is not None and new_issuer != transaction.issuer and transaction.issuer:
        linked_account = db.query(User.id).filter(User.username == transaction.issuer).first()
        if linked_account:
            raise HTTPException(
                status_code=409,
                detail="The issuer belongs to a user account and cannot be changed.",
            )

    for field, value in updates.items():
        setattr(transaction, field, value)

    transaction.last_modified_at = datetime.now(timezone.utc)
    transaction.last_modified_by = str(user.user_id)

    try:
        db.commit()
        db.refresh(transaction)
    except SQLAlchemyError:
        db.rollback()
        logger.exception("Failed to update transaction %s", transaction_id)
        raise HTTPException(status_code=500, detail="Unable to update transaction") from None

    return transaction

# Public recent donation
@router.get("/recent", response_model=list[TransactionResponse]|TransactionResponse)
def get_transactions(
    page: int = Query(default=1, ge=1, le=10),
    db: Session = Depends(get_db),
):
    transactions = (
        db.query(Transaction)
        .filter(
            Transaction.flow == TransactionType.INCOME,
            Transaction.status == TransactionStatus.CONFIRMED,
        )
        .order_by(Transaction.created_at.desc(), Transaction.inx.desc())
        .limit(25)
        .offset((page - 1) * 25)
        .all()
    )

    if not transactions:
        raise HTTPException(
            status_code=404,
            detail="No transactions found"
        )

    return transactions


@router.get("/recent/data") # Public recent donation
def get_recent(id: int, request: Request, db: Session = Depends(get_db)):
    transactions = (
        db.query(Transaction)
        .filter(
            Transaction.inx == id,
            Transaction.flow == TransactionType.INCOME,
            Transaction.status == TransactionStatus.CONFIRMED,
        )
        .first()
    )

    if not transactions:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found",
        )

    return templates.TemplateResponse(
        request=request,
        name="donation/recent.html",
        context={
            "transactions": transactions,
        },
    )

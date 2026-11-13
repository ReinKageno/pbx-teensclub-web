
from datetime import datetime, timezone
import logging
from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app import templates
from app.database.session import get_db
from app.dependencies import common_id_limit_parameters
from app.function import AppSystem
from app.function.user_services import get_optional_user
from app.models import Transaction, User
from app.models.enums import TransactionType, TransactionStatus
from app.schemas.transaction import AdminTransactionCreate, TransactionResponse, UserTransactionCreate


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/donation",
    tags=["Transactions", "Donation"],
)

@router.post("/new", response_model=TransactionResponse)
def create_transaction(payload: dict = Body(...), user: User | None = Depends(get_optional_user), db: Session = Depends(get_db)):
    is_admin = user is not None and user.is_admin

    model = (
        AdminTransactionCreate
        if is_admin
        else UserTransactionCreate
    )

    try:
        data = model.model_validate(payload)
    except ValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail=exc.errors(include_url=False)
        ) from exc

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

@router.get("/new", response_class=HTMLResponse)
def new_transaction_page(
    request: Request,
    user: User | None = Depends(get_optional_user)
):
    return templates.TemplateResponse(
        request=request,
        name="transactions/new.html",
        context={
            "user": user,
            "is_logged_in": user is not None,
            "is_admin": (
                user is not None
                and user.is_admin == True
            ),
        },
    )

@router.get("/", response_model=list[TransactionResponse]|TransactionResponse)
def get_transactions(commons: Annotated[dict, Depends(common_id_limit_parameters)], db: Session = Depends(get_db)):
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


@router.get("/recent")
def get_recent(request: Request, db: Session = Depends(get_db)):
    transactions = (
        db.query(Transaction)
        .order_by(Transaction.created_at.desc())
        .all()
    )

    return templates.TemplateResponse(
        request=request,
        name="donation/recent.html",
        context={
            "transactions": transactions,
        },
    )

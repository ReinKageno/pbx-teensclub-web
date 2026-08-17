from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from app.database import engine, SessionLocal
from app.models import Base, Transaction
from app.schemas import TransactionCreate, TransactionResponse

app = FastAPI()

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()

@app.post("/transactions", response_model=TransactionResponse)
def create_transaction(
    transaction: TransactionCreate,
    db: Session = Depends(get_db),
):
    db_transaction = Transaction(
        type=transaction.type,
        amount=transaction.amount,
        description=transaction.description,
        donor_name=transaction.donor_name,
        status="confirmed",
    )

    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)

    return db_transaction

@app.get("/transactions", response_model=list[TransactionResponse])
def get_transactions(db: Session = Depends(get_db)):
    transactions = db.query(Transaction).all()

    return transactions
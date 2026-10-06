from os import environ

from dotenv import load_dotenv
from fastapi import Cookie, Depends, HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.models.user import Session as UserSession, User


load_dotenv()

DATABASE_URL = environ['DATABASE_URL']

engine = create_engine(DATABASE_URL, echo=True)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False
)

def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()

def get_current_user(
    session_id: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
):
    if session_id is None:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated"
        )
    
    session = db.querry(UserSession).filter(
        UserSession.id == session_id
    ).first()

    if session is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid session"
        )

    user = db.query(User).filter(
        User.id == session.user_id
    )

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="User not found"
        )

    return user
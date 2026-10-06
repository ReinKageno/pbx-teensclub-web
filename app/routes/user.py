import secrets
from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.user import user_login_parameters
from app.function.phash import verify_password
from app.models.user import User
from app.schemas.user import SessionLogout, TransmitSession

router = APIRouter(
    prefix="/user"
)

# @router.get("")
# def admin_hall(
#     current_user: User = Depends(get_current_user)
# ):
#     if not current_user.is_admin:
#         raise HTTPException(
#             status_code=403,
#             detail="Admin access required"
#         )

#     return

@router.post("/login", response_model=TransmitSession)
def user_login(
    response: Response,
    input: Annotated[dict, Depends(user_login_parameters)],
    db: Session = Depends(get_db),
):
    session_id = secrets.token_urlsafe(32)

    user = db.scalars(
        select(User)
        .where(
            or_(
                User.username == input["identity"],
                User.email == input["identity"],
            )
        )
    ).first()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )

    if verify_password(input["password"], user.password_hash):
        response.set_cookie(
            key="session_id",
            value=session_id,
            httponly=True,
            samesite="lax"
        )

        return {"message": "Logged in"}
    
    else:
        raise HTTPException(
            status_code=401,
            detail="Password incorrect"
        )

@router.post("/logout", response_model=SessionLogout)
def user_logout(response: Response):
    response.delete_cookie("session_id")

    return {"message": "Logged out"}
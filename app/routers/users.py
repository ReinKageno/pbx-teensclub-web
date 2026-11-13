from datetime import datetime, timedelta, timezone
import logging
import secrets
from typing import Annotated, List

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app.database.session import get_db
from app.dependencies.user import UserLoginForm, UserRegisterForm
from app.function import get_current_user, hash_password, verify_password, registration_user_exist, get_current_admin
from app.models import Notification, NotificationStatuses, User, UserSession
from app.models.enums import NotifyType
from app.schemas.notification import NotificationSchema, NotificationStatusSchema
from app.schemas.user import UserLogMessageResponse


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/user",
    tags=["User"],
)

router_notification = APIRouter(
    prefix="/notification",
    tags=["Event", "User"],
)

@router.post("/login", response_model=UserLogMessageResponse)
def user_login(response: Response, input: Annotated[UserLoginForm, Depends()], db: Session = Depends(get_db)):
    if not input.identity:
        raise HTTPException(
            status_code=411,
            detail="Username or email cannot be empty"
        )
    
    if not input.password:
        raise HTTPException(
            status_code=411,
            detail="Password cannot be empty"
        )
    
    session_id = secrets.token_urlsafe(32)
    now = datetime.now(timezone.utc)

    user = db.scalar(
        select(User)
        .where(or_(
            User.username == input.identity,
            User.email == input.identity,
        ))
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )

    if verify_password(input.password, user.password_hash):
        db_user_session = UserSession(
            user_id=user.id,
            session_id=session_id,
            last_active_at=now,
            expires_at=now + timedelta(days=7),
            max_expires_at=now + timedelta(days=30),
        )

        db.add(db_user_session)
        db.commit()

        response.set_cookie(
            key="session_id",
            value=session_id,
            httponly=True,
            # secure=True,
            samesite="lax",
            max_age=60 * 60 * 24 * 30,
        )

        return {"message": "Logged in"}
    
    else:
        raise HTTPException(
            status_code=401,
            detail="Password incorrect"
        )

@router.post("/logout", response_model=UserLogMessageResponse)
def user_logout(response: Response):
    response.delete_cookie("session_id")

    return {"message": "Logged out"}

@router.post("/register", response_model=UserLogMessageResponse)
def user_register(response: Response, usr: Annotated[UserRegisterForm, Depends()], session_id: str | None = Cookie(default=None), db: Session = Depends(get_db)):
    if session_id:
        raise HTTPException(
            status_code=409,
            detail="You already have a session",
        )

    registration_user_exist(usr, db)

    if usr.password != usr.confirm_password:
        raise HTTPException(
            status_code=400,
            detail="Password don't match",
        )

    if len(usr.password) < 8:
        raise HTTPException(
            status_code=400,
            detail="Password need at least 8 characters",
        )

    session_id = secrets.token_urlsafe(32)
    now = datetime.now(timezone.utc)

    try:
        user = User(
            username=usr.username,
            email=usr.email,
            password_hash=hash_password(usr.password),
        )

        db.add(user)
        db.flush()

        user_session = UserSession(
            user_id=user.id,
            session_id=session_id,
            last_active_at=now,
            expires_at=now + timedelta(days=7),
            max_expires_at=now + timedelta(days=30),
        )

        db.add(user_session)
        db.commit()

    except Exception as e:
        db.rollback()
        logger.exception(e)
        raise HTTPException(
            status_code=500
        )

    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        # secure=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 30,
    )

    return {"message": "Registered successfully"}

@router.get("/{user_uuid}")
def get_user_profile(user_uuid: str, session_id: str | None = Cookie(default=None), db: Session = Depends(get_db)):
    """Current user information."""

    # Not yet implemented

@router.get("", response_model=List[NotificationSchema])
def read_all_notifications(db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    """Read all notification container from database."""

    notifications_list = db.query(Notification).all()
    return notifications_list

@router_notification.get("/get", response_model=List[NotificationSchema])
def read_notification(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Read all notification from database. Login required."""

    notifications_statuses = db.scalars(
        select(NotificationStatuses)
        .filter(NotificationStatuses.user_id==user.id)
        .options(selectinload(Notification))
        .order_by(NotificationStatuses.notification.created_at)
    ).all()

    if not notifications_statuses:
        raise HTTPException(
            status_code=404,
            detail="Cannot find any notification for this user"
        )

    fetched_notification = []

    for status in notifications_statuses:
        notification_content = status.notification

        if notification_content.is_admin_only and not user.is_admin:
            continue

        fetched_notification.append(NotificationSchema(
            id=notification_content.id,
            type=notification_content.type,
            link=notification_content.link,
            message=notification_content.message,
            is_admin_only=notification_content.is_admin_only,
            created_at=notification_content.created_at,
            is_read=status.is_read,
        ))

    if not fetched_notification:
        raise HTTPException(
            status_code=404,
            detail="Cannot find any accessible notification for this user"
        )

    return fetched_notification

@router_notification.get("/{notification_id}/status", response_model=NotificationStatusSchema)
def get_notification_status(notification_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get the read status of a specific notification for a user."""

    mock_status = db.scalar(
        select(NotificationStatuses)
        .filter(
            NotificationStatuses.notification_id==notification_id,
            NotificationStatuses.user_id==user.user_id
        )
    )

    if not mock_status:
        raise HTTPException(
            status_code=404,
            detail="Cannot find any notification for this user"
        )

    notification = db.scalar(
        select(Notification)
        .filter(Notification.id==notification_id)
    )    

    if not notification:
        raise HTTPException(
            status_code=404,
            detail="Cannot find related notification"
        )
    
    if notification.is_admin_only and not user.user_admin:
        raise HTTPException(
            status_code=403,
            detail="Forbidden request, you have no access",
        )

    return NotificationStatusSchema(
        id=mock_status.id,
        is_admin_only=notification.is_admin_only,
        created_at=notification.created_at,
        is_read=mock_status.is_read,
    )

@router_notification.patch("/{notification_id}/read", response_model=NotificationSchema)
def mark_as_read(notification_id: str, user_id: int, db: Session = Depends(get_db)):
    """Mark a specific notification as read for the current user."""
    
    # Mocking update:
    updated_notification = Notification(id=notification_id, type=NotifyType.SYSTEM, message="Server maintenance tonight.", link="/", is_admin_only=False, created_at=datetime.now())

    return updated_notification
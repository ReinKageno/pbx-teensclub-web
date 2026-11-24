from datetime import datetime, timedelta, timezone
import secrets
from typing import Annotated, List

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy import delete, or_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, selectinload

from app import logger
from app.database.session import get_db
from app.dependencies.user import UserLoginForm, UserRegisterForm
from app.function import get_current_user, hash_password, verify_password, registration_user_exist, get_current_admin
from app.function.user_services import get_optional_session, get_optional_user
from app.models import Notification, NotificationStatuses, User, UserSession
from app.models.enums import NotifyLevel
from app.schemas.notification import NotificationSchema, NotificationStatusSchema
from app.schemas.user import UserLogMessageResponse
from app.services.exceptions import ResourceUnderConstructionError


router_user = APIRouter(
    prefix="/user",
    tags=["User"],
)

router_notification = APIRouter(
    prefix="/notification",
    tags=["Event", "User"],
)


@router_user.post("/login", response_model=UserLogMessageResponse)
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

        logger.info(f"UserLogger: User {user.username} was logged in. UUID: {user.user_id}")

        return {"message": "Logged in"}
    
    else:
        logger.warning(f"UserLogger: User {user.username} tried to login with wrong password. UUID: {user.user_id}")
        raise HTTPException(
            status_code=401,
            detail="Password incorrect"
        )


@router_user.post("/logout", response_model=UserLogMessageResponse)
def user_logout(response: Response, user_session: UserSession | None = Depends(get_optional_session), user: User | None = Depends(get_optional_user), db: Session = Depends(get_db)):
    response.delete_cookie("session_id")
    
    if user_session:
        try:
            stmt = delete(UserSession).where(UserSession.id == user_session.id)
            execute = db.execute(stmt)
            db.commit()
        except SQLAlchemyError:
            db.rollback()
            logger.error(f"UserLogger: Cannot remove session with id: {user_session.id}")
    else:
        logger.info("UserLogger: Cannot find the session")

    if user:
        logger.info(f"UserLogger: User {user.username} was logged out. UUID: {user.user_id}")

    return {"message": "Logged out"}


@router_user.post("/register", response_model=UserLogMessageResponse)
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
            display_name=usr.name
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
        logger.info(1, f"UserLogger: {user.user_id} was created with username {user.username}")

    except Exception as e:
        logger.error(f"UserLogger: Failed to create account for user {usr.username}")
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


@router_user.get("/profile/{user_uuid}")
def get_user_profile(user_uuid: str, session_id: str | None = Cookie(default=None), db: Session = Depends(get_db)):
    """Current user information."""

    # Not yet implemented

    logger.info("Is not implemented service: 'user_profile'")
    return RedirectResponse(url="/not-found", status_code=404)


@router_user.get("", response_model=List[NotificationSchema])
def read_all_notifications(db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    """Read all notification container from database."""

    return RedirectResponse(url="/not-found", status_code=404)

    notifications_list = db.query(Notification).all()
    return notifications_list


@router_notification.get("/get", response_model=List[NotificationSchema])
def read_notification(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Read all notification from database. Login required."""

    logger.info("Is not implemented service: 'read_notification'")
    return RedirectResponse(url="not-found", status_code=404)

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
            level=notification_content.level,
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

    logger.info("Is not implemented service: 'get_notification_status'")
    return RedirectResponse(url="not-found", status_code=404)

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
    
    logger.info("Is not implemented service: 'mark_as_red'")
    return RedirectResponse(url="not-found", status_code=404)

    # Mocking update:
    updated_notification = Notification(
        id=notification_id,
        level=NotifyLevel.SYSTEM,
        message="Server maintenance tonight.",
        link="/",
        is_admin_only=False,
        created_at=datetime.now()
    )

    return updated_notification


@router_user.get("/profile")
def get_profile(request: Request):

    logger.info("Is not implemented service: 'get_profile'")
    raise ResourceUnderConstructionError()
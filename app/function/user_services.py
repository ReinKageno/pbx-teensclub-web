from datetime import datetime, timedelta, timezone

from fastapi import Cookie, Depends, HTTPException
from sqlalchemy import Sequence, select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies.user import UserRegisterForm
from app.models import User, UserSession, Notification, NotificationStatuses
from app.schemas.notification import NotificationCreate, NotificationSchema
from app.services.exceptions import AppError


def get_optional_session(
    session_id: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
) -> UserSession | None:
    if not session_id:
        return None

    db_session = db.scalar(
        select(UserSession).where(
            UserSession.session_id == session_id
        )
    )

    if not db_session:
        return None

    now = datetime.now(timezone.utc)

    if now >= db_session.expires_at:
        return None

    return db_session

def update_session_activity(
    db_session: UserSession | None = Depends(get_optional_session),
) -> None:
    if db_session is None:
        return

    db = Session.object_session(db_session)
    if not db:
        raise AppError(detail="Cannot process user session.")

    now = datetime.now(timezone.utc)

    db_session.expires_at = min(
        now + timedelta(days=7),
        db_session.max_expires_at,
    )
    db_session.last_active_at = now

    db.commit()

def get_optional_user(
    db_session: UserSession | None = Depends(get_optional_session),
    _: None = Depends(update_session_activity),
) -> User | None:
    if db_session is None:
        return None

    db = Session.object_session(db_session)
    if not db:
        raise AppError(detail="Cannot process user session.")

    return db.scalar(
        select(User).where(
            User.id == db_session.user_id
        )
    )

def get_current_user(
    user: User | None = Depends(get_optional_user),
) -> User:
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
        )

    return user


def get_current_admin(
    user: User = Depends(get_current_user),
) -> User:
    if not user.is_admin:
        raise HTTPException(
            status_code=403,
            detail="Admin permission required",
        )

    return user

def registration_user_exist(
    usr: UserRegisterForm,
    db: Session,
) -> bool:
    if usr.username.strip().casefold() in {"system", "anonymous"}:
        raise HTTPException(
            status_code=409,
            detail="This username is reserved",
        )

    usermail_exists = db.scalar(
        select(User.email).where(User.email==usr.email)
    )

    if usermail_exists:
        raise HTTPException(
            status_code=409,
            detail="Email is already used"
        )

    username_exists = db.scalar(
        select(User.username).where(User.username==usr.username)
    )

    if username_exists:
        raise HTTPException(
            status_code=409,
            detail="Username already exists"
        )

    return True

def create_notification(
    user: User|Sequence[User]|list[User],
    notification: NotificationCreate,
    db: Session = Depends(get_db)
):
    new_notification = Notification(
        # announcement=notification.announcement,
        level=notification.level,
        message=notification.message,
        link=notification.link,
        is_admin_only=notification.is_admin_only,
    )
    
    users_to_notify = []

    # if notification.announcement:
    #     if not new_notification.is_admin_only:
    #         users_to_notify = db.scalars(select(User)).all()
    #     else:
    #         users_to_notify = db.scalars(select(User).filter(User.is_admin==True)).all()
    # else:
    #     users_to_notify = user

    if not users_to_notify:
        raise HTTPException(
            status_code=404,
            detail="Cannot find any users to notify",
        )

    statuses_to_add = []

    for u in users_to_notify:
        status = NotificationStatuses(
            notification_id=new_notification.id,
            user_id=u.id,
        )
        statuses_to_add.append(status)
    
    db.add(new_notification)
    db.add_all(statuses_to_add)
    
    db.commit()
    db.refresh(new_notification)

    return NotificationSchema.model_validate(new_notification)

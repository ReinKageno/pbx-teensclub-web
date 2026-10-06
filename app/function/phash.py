from pwdlib import PasswordHash
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.user import User

password_hash = PasswordHash.recommended()

def hash_password(password:str) -> str :
    return password_hash.hash(password)

def verify_password(password:str, hashed:str) -> bool :
    return password_hash.verify(password, hashed)
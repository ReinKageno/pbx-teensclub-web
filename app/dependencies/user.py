from pydantic import BaseModel


class UserLoginForm(BaseModel):
    identity: str
    password: str

class UserRegisterForm(BaseModel):
    email: str
    username: str
    password: str
    confirm_password: str
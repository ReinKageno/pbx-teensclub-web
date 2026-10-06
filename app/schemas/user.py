from pydantic import BaseModel


class RequestUserRegister(BaseModel):
    email: str
    username: str
    password: str
    confim_password: str

class TransmitSession(BaseModel):
    session_id: str

class SessionLogout(BaseModel):
    msg: str
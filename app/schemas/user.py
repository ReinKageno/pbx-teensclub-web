from pydantic import BaseModel


class UserRequestRegister(BaseModel):
    email: str
    username: str
    password: str

class TransmitSession(BaseModel):
    session_id: str

class UserLogMessageResponse(BaseModel):
    message: str
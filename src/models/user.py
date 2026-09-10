from pydantic import BaseModel


class User(BaseModel):
    id: int
    username: str
    email: str


class LoginResponse(BaseModel):
    token: str
    refresh: str
    user: User

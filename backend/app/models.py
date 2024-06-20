from pydantic import BaseModel

class BaseUser(BaseModel):
    username: str | None = None
    hashed_password: str | None = None
    role: str | None = None

    
class User(BaseUser):
    email: str | None = None
    disabled: bool| None = None


class Token(BaseModel):
    access_token: str | None = None
    refresh_token: str | None = None

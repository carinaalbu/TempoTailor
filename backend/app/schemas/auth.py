from pydantic import BaseModel


class UserInfo(BaseModel):
    id: str
    display_name: str | None
    email: str | None

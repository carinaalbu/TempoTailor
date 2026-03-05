from pydantic import BaseModel


class RefreshRequest(BaseModel):
    refresh_token: str


class UserInfo(BaseModel):
    id: str
    display_name: str | None
    email: str | None
    image_url: str | None = None

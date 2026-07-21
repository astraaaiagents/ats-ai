from pydantic import BaseModel


class UserCreate(BaseModel):
    email: str
    password: str
    role: str = "recruiter"


class UserInvite(BaseModel):
    email: str
    role: str = "recruiter"


class UserUpdate(BaseModel):
    email: str | None = None
    role: str | None = None
    reason: str | None = None


class UserResponse(BaseModel):
    id: str
    email: str
    role: str
    is_active: bool
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class InviteResponse(BaseModel):
    message: str
    magic_link: str
    expires_at: str

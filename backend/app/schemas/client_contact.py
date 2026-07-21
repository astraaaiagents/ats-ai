from pydantic import BaseModel


class ClientContactCreate(BaseModel):
    email: str
    first_name: str
    last_name: str
    phone: str | None = None


class ClientContactUpdate(BaseModel):
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    is_active: bool | None = None


class ClientContactResponse(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    phone: str | None
    is_active: bool
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}

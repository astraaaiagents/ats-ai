from pydantic import BaseModel


class ClientContactCreate(BaseModel):
    email: str
    first_name: str
    last_name: str
    phone: str | None = None
    organization_name: str | None = None
    title: str | None = None
    location: str | None = None
    description: str | None = None
    status: str | None = None


class ClientContactUpdate(BaseModel):
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    organization_name: str | None = None
    title: str | None = None
    location: str | None = None
    description: str | None = None
    status: str | None = None
    is_active: bool | None = None


class ClientContactResponse(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    phone: str | None
    organization_name: str | None
    title: str | None
    location: str | None
    description: str | None
    status: str | None
    is_active: bool
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}

from pydantic import BaseModel


class OrganizationCreate(BaseModel):
    name: str
    slug: str
    kms_key_id: str | None = None


class OrganizationUpdate(BaseModel):
    name: str | None = None
    slug: str | None = None
    kms_key_id: str | None = None
    is_active: bool | None = None


class OrganizationResponse(BaseModel):
    id: str
    name: str
    slug: str
    kms_key_id: str | None
    is_active: bool
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}

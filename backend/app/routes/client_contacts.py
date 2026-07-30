from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, require_role
from app.database import get_session
from app.middleware.error_handler import AppException

from app.middleware.pagination import PaginationParams, paginated_response
from app.models.client_contact import ClientContact
from app.schemas.client_contact import (
    ClientContactCreate,
    ClientContactResponse,
    ClientContactUpdate,
)

client_contacts_router = APIRouter(prefix="/client-contacts", tags=["client-contacts"])


def _safe_str(val):
    return val if isinstance(val, str) else None


def _format_client_contact_response(c) -> ClientContactResponse:
    created_at = c.created_at.isoformat() if hasattr(c.created_at, "isoformat") else str(c.created_at)
    updated_at = c.updated_at.isoformat() if hasattr(c.updated_at, "isoformat") else str(c.updated_at)

    return ClientContactResponse(
        id=str(c.id),
        email=c.email,
        first_name=c.first_name,
        last_name=c.last_name,
        phone=_safe_str(getattr(c, "phone", None)),
        organization_name=_safe_str(getattr(c, "organization_name", None)),
        title=_safe_str(getattr(c, "title", None)),
        location=_safe_str(getattr(c, "location", None)),
        description=_safe_str(getattr(c, "description", None)),
        status=_safe_str(getattr(c, "status", None)),
        is_active=bool(getattr(c, "is_active", True)),
        created_at=created_at,
        updated_at=updated_at,
    )


@client_contacts_router.get("", response_model=None)
async def list_client_contacts(
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_session),
    current_user=Depends(require_role(["admin", "manager", "recruiter"])),
):
    """List client contacts with pagination."""
    org_id = getattr(current_user, "organization_id", None)

    count_result = await db.execute(
        select(func.count()).where(
            ClientContact.organization_id == org_id,
            ClientContact.is_active == True,
        )
    )
    total = count_result.scalar() or 0

    sort_field = "created_at"
    sort_dir = "ASC"
    if pagination.sort:
        parts = pagination.sort.split(":")
        sort_field = parts[0] if parts else "created_at"
        sort_dir = parts[1] if len(parts) > 1 else "ASC"

    sort_column = getattr(ClientContact, sort_field, ClientContact.created_at)
    if sort_dir.upper() == "DESC":
        sort_column = sort_column.desc()

    query = (
        select(ClientContact)
        .where(
            ClientContact.organization_id == org_id,
            ClientContact.is_active == True,
        )
        .order_by(sort_column)
        .limit(pagination.limit + 1)
    )

    result = await db.execute(query)
    contacts = result.scalars().all()

    has_more = len(contacts) > pagination.limit
    if has_more:
        contacts = contacts[:pagination.limit]

    data = [_format_client_contact_response(c) for c in contacts]

    return paginated_response(data, total, pagination.limit, pagination.sort)


@client_contacts_router.post("", response_model=ClientContactResponse, status_code=201)
async def create_client_contact(
    body: ClientContactCreate,
    db: AsyncSession = Depends(get_session),
    current_user=Depends(require_role(["admin", "manager", "recruiter", "super_admin"])),
):
    """Create a client contact. Admin/Manager only."""
    org_id = getattr(current_user, "organization_id", None)

    # Check for duplicate email within org
    existing = await db.execute(
        select(ClientContact).where(
            ClientContact.organization_id == org_id,
            ClientContact.email == body.email,
        )
    )
    if existing.scalar_one_or_none():
        raise AppException(
            code="DUPLICATE_EMAIL",
            message="A client contact with this email already exists",
            status_code=409,
        )

    contact = ClientContact(
        organization_id=org_id,
        email=body.email,
        first_name=body.first_name,
        last_name=body.last_name,
        phone=body.phone,
        organization_name=body.organization_name,
        title=body.title,
        location=body.location,
        description=body.description,
        status=body.status or "active",
    )
    db.add(contact)
    await db.flush()
    await db.refresh(contact)

    return _format_client_contact_response(contact)


@client_contacts_router.put("/{contact_id}", response_model=ClientContactResponse)
async def update_client_contact(
    contact_id: str,
    body: ClientContactUpdate,
    db: AsyncSession = Depends(get_session),
    current_user=Depends(require_role(["admin", "manager", "recruiter", "super_admin"])),
):
    """Update client contact. Admin/Manager only."""
    org_id = getattr(current_user, "organization_id", None)

    result = await db.execute(
        select(ClientContact).where(
            ClientContact.id == UUID(contact_id),
            ClientContact.organization_id == org_id,
        )
    )
    contact = result.scalar_one_or_none()
    if not contact:
        raise AppException(
            code="NOT_FOUND",
            message="Client contact not found",
            status_code=404,
        )

    update_data = body.model_dump(exclude_unset=True)

    # Check email uniqueness if changing
    if "email" in update_data and update_data["email"] != contact.email:
        email_check = await db.execute(
            select(ClientContact).where(
                ClientContact.organization_id == org_id,
                ClientContact.email == update_data["email"],
                ClientContact.id != UUID(contact_id),
            )
        )
        if email_check.scalar_one_or_none():
            raise AppException(
                code="DUPLICATE_EMAIL",
                message="A client contact with this email already exists",
                status_code=409,
            )

    for key, value in update_data.items():
        setattr(contact, key, value)

    await db.flush()
    await db.refresh(contact)

    return _format_client_contact_response(contact)


@client_contacts_router.delete("/{contact_id}", response_model=ClientContactResponse)
async def delete_client_contact(
    contact_id: str,
    db: AsyncSession = Depends(get_session),
    current_user=Depends(require_role(["admin", "manager", "recruiter", "super_admin"])),
):
    """Soft-delete client contact (set is_active=False). Admin/Manager only."""
    org_id = getattr(current_user, "organization_id", None)

    result = await db.execute(
        select(ClientContact).where(
            ClientContact.id == UUID(contact_id),
            ClientContact.organization_id == org_id,
        )
    )
    contact = result.scalar_one_or_none()
    if not contact:
        raise AppException(
            code="NOT_FOUND",
            message="Client contact not found",
            status_code=404,
        )

    contact.is_active = False
    await db.flush()
    await db.refresh(contact)

    return _format_client_contact_response(contact)

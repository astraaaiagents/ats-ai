from fastapi import APIRouter, Depends
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import require_role
from app.database import get_session
from app.middleware.error_handler import AppException
from app.middleware.pagination import PaginationParams, paginated_response
from app.models.organization import Organization
from app.schemas.organization import (
    OrganizationCreate,
    OrganizationResponse,
    OrganizationUpdate,
)

organizations_router = APIRouter(prefix="/organizations", tags=["organizations"])


@organizations_router.post("", response_model=OrganizationResponse, status_code=201)
async def create_organization(
    body: OrganizationCreate,
    db: AsyncSession = Depends(get_session),
    _current_user=Depends(require_role(["super_admin"])),
):
    """Create a new organization. SuperAdmin only."""
    # Check for duplicate slug
    result = await db.execute(
        select(Organization).where(Organization.slug == body.slug)
    )
    if result.scalar_one_or_none():
        raise AppException(
            code="DUPLICATE_SLUG",
            message=f"Organization with slug '{body.slug}' already exists",
            status_code=409,
        )

    org = Organization(
        name=body.name,
        slug=body.slug,
        kms_key_id=body.kms_key_id,
    )
    db.add(org)
    await db.commit()
    await db.refresh(org)

    return OrganizationResponse(
        id=str(org.id),
        name=org.name,
        slug=org.slug,
        kms_key_id=org.kms_key_id,
        is_active=org.is_active,
        created_at=org.created_at.isoformat(),
        updated_at=org.updated_at.isoformat(),
    )


@organizations_router.get("/{org_id}", response_model=OrganizationResponse)
async def get_organization(
    org_id: str,
    db: AsyncSession = Depends(get_session),
    _current_user=Depends(require_role(["super_admin"])),
):
    """Get organization by ID. SuperAdmin only."""
    from uuid import UUID

    result = await db.execute(
        select(Organization).where(Organization.id == UUID(org_id))
    )
    org = result.scalar_one_or_none()
    if not org:
        raise AppException(
            code="NOT_FOUND",
            message="Organization not found",
            status_code=404,
        )

    return OrganizationResponse(
        id=str(org.id),
        name=org.name,
        slug=org.slug,
        kms_key_id=org.kms_key_id,
        is_active=org.is_active,
        created_at=org.created_at.isoformat(),
        updated_at=org.updated_at.isoformat(),
    )


@organizations_router.put("/{org_id}", response_model=OrganizationResponse)
async def update_organization(
    org_id: str,
    body: OrganizationUpdate,
    db: AsyncSession = Depends(get_session),
    _current_user=Depends(require_role(["super_admin"])),
):
    """Update organization. SuperAdmin only.

    KMS key rotation triggers re-encryption of new objects only;
    existing objects retain prior key.
    """
    from uuid import UUID

    result = await db.execute(
        select(Organization).where(Organization.id == UUID(org_id))
    )
    org = result.scalar_one_or_none()
    if not org:
        raise AppException(
            code="NOT_FOUND",
            message="Organization not found",
            status_code=404,
        )

    update_data = body.model_dump(exclude_unset=True)
    if "slug" in update_data and update_data["slug"] != org.slug:
        # Check for duplicate slug
        slug_check = await db.execute(
            select(Organization).where(
                Organization.slug == update_data["slug"],
                Organization.id != UUID(org_id),
            )
        )
        if slug_check.scalar_one_or_none():
            raise AppException(
                code="DUPLICATE_SLUG",
                message=f"Organization with slug '{update_data['slug']}' already exists",
                status_code=409,
            )

    for key, value in update_data.items():
        setattr(org, key, value)

    await db.commit()
    await db.refresh(org)

    return OrganizationResponse(
        id=str(org.id),
        name=org.name,
        slug=org.slug,
        kms_key_id=org.kms_key_id,
        is_active=org.is_active,
        created_at=org.created_at.isoformat(),
        updated_at=org.updated_at.isoformat(),
    )

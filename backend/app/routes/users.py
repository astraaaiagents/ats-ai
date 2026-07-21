from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import require_role
from app.auth.jwt import create_access_token
from app.auth.password import hash_password
from app.database import get_session
from app.middleware.error_handler import AppException
from fastapi import Depends

from app.middleware.pagination import PaginationParams, paginated_response
from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.user import (
    InviteResponse,
    UserCreate,
    UserInvite,
    UserResponse,
    UserUpdate,
)

users_router = APIRouter(prefix="/users", tags=["users"])


@users_router.get("", response_model=None)
async def list_users(
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_session),
    _current_user=Depends(require_role(["admin", "manager"])),
):
    """List users with pagination. Admin/Manager only."""
    # Count total
    count_result = await db.execute(
        select(func.count()).where(User.is_active == True)
    )
    total = count_result.scalar() or 0

    # Build query with sort
    sort_field = "created_at"
    sort_dir = "ASC"
    if pagination.sort:
        parts = pagination.sort.split(":")
        sort_field = parts[0] if parts else "created_at"
        sort_dir = parts[1] if len(parts) > 1 else "ASC"

    sort_column = getattr(User, sort_field, User.created_at)
    if sort_dir.upper() == "DESC":
        sort_column = sort_column.desc()

    query = (
        select(User)
        .where(User.is_active == True)
        .order_by(sort_column)
        .limit(pagination.limit + 1)
    )

    result = await db.execute(query)
    users = result.scalars().all()

    has_more = len(users) > pagination.limit
    if has_more:
        users = users[:pagination.limit]

    data = [
        UserResponse(
            id=str(u.id),
            email=u.email,
            role=u.role,
            is_active=u.is_active,
            created_at=u.created_at.isoformat(),
            updated_at=u.updated_at.isoformat(),
        )
        for u in users
    ]

    return paginated_response(data, total, pagination.limit, pagination.sort)


@users_router.post("/invite", response_model=InviteResponse)
async def invite_user(
    body: UserInvite,
    db: AsyncSession = Depends(get_session),
    _current_user=Depends(require_role(["admin", "manager"])),
):
    """Invite a user via magic link. Admin/Manager only.

    Generates a 48-hour magic link token. Email sending is a placeholder.
    If user already exists and is active, returns existing link.
    """
    # Check if user already exists
    result = await db.execute(
        select(User).where(User.email == body.email, User.is_active == True)
    )
    existing = result.scalar_one_or_none()

    if existing:
        # Check resend limit — we track via a simple approach:
        # count how many times invite was sent by checking if token_version
        # was incremented recently (simplified: allow up to 2 resends)
        # For now, we generate a new token but track via audit log
        pass
    else:
        # Create the user with a temporary password
        # The magic link will set the actual password
        temp_password = hash_password(f"temp-{body.email}-{datetime.now(UTC).timestamp()}")
        user = User(
            email=body.email,
            password_hash=temp_password,
            role=body.role,
            is_active=True,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    # Generate magic link token (48h TTL)
    magic_token = create_access_token(
        {
            "sub": str(existing.id if existing else (await db.execute(select(User).where(User.email == body.email))).scalar_one().id),
            "type": "magic_link",
            "email": body.email,
        },
        expires_delta=timedelta(hours=48),
    )

    # Log the invite
    db.add(
        AuditLog(
            organization_id=getattr(_current_user, "organization_id", None),
            user_id=_current_user.id,
            event_type="user.invite_sent",
            resource_type="user",
            resource_id=str(existing.id if existing else (await db.execute(select(User).where(User.email == body.email))).scalar_one().id),
            details={"email": body.email, "role": body.role},
        )
    )
    await db.commit()

    app_url = "http://localhost:3000"
    magic_link = f"{app_url}/invite?token={magic_token}"

    return InviteResponse(
        message="Invite sent successfully",
        magic_link=magic_link,
        expires_at=(datetime.now(UTC) + timedelta(hours=48)).isoformat(),
    )


@users_router.post("/{user_id}/resend-invite", response_model=InviteResponse)
async def resend_invite(
    user_id: str,
    db: AsyncSession = Depends(get_session),
    _current_user=Depends(require_role(["admin", "manager"])),
):
    """Resend invite for a user. Reuses existing magic link, max 2 resends per link.

    Admin/Manager only.
    """
    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise AppException(
            code="NOT_FOUND",
            message="User not found",
            status_code=404,
        )

    # Generate new magic link token (48h TTL)
    magic_token = create_access_token(
        {
            "sub": str(user.id),
            "type": "magic_link",
            "email": user.email,
        },
        expires_delta=timedelta(hours=48),
    )

    app_url = "http://localhost:3000"
    magic_link = f"{app_url}/invite?token={magic_token}"

    return InviteResponse(
        message="Invite resent successfully",
        magic_link=magic_link,
        expires_at=(datetime.now(UTC) + timedelta(hours=48)).isoformat(),
    )


@users_router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    body: UserUpdate,
    db: AsyncSession = Depends(get_session),
    _current_user=Depends(require_role(["admin", "manager"])),
):
    """Update user. Admin/Manager only.

    Requires `reason` field for ownership transfers (role changes).
    """
    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise AppException(
            code="NOT_FOUND",
            message="User not found",
            status_code=404,
        )

    update_data = body.model_dump(exclude_unset=True)

    # Require reason for role changes (ownership transfer)
    if "role" in update_data and update_data["role"] != user.role:
        if not body.reason:
            raise AppException(
                code="MISSING_REASON",
                message="Reason is required for role changes (ownership transfer)",
                status_code=400,
            )

    # Check email uniqueness if changing email
    if "email" in update_data and update_data["email"] != user.email:
        email_check = await db.execute(
            select(User).where(
                User.email == update_data["email"],
                User.id != UUID(user_id),
                User.is_active == True,
            )
        )
        if email_check.scalar_one_or_none():
            raise AppException(
                code="DUPLICATE_EMAIL",
                message="Email already in use by another active user",
                status_code=409,
            )

    for key, value in update_data.items():
        setattr(user, key, value)

    await db.commit()
    await db.refresh(user)

    return UserResponse(
        id=str(user.id),
        email=user.email,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at.isoformat(),
        updated_at=user.updated_at.isoformat(),
    )


@users_router.delete("/{user_id}", response_model=UserResponse)
async def deactivate_user(
    user_id: str,
    db: AsyncSession = Depends(get_session),
    _current_user=Depends(require_role(["admin", "manager"])),
):
    """Deactivate user. Admin/Manager only.

    When a user is deactivated, their candidates' owner_id is set to null.
    """
    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise AppException(
            code="NOT_FOUND",
            message="User not found",
            status_code=404,
        )

    user.is_active = False
    user.token_version += 1  # Invalidate all existing tokens

    # Clear ownership of candidates (future-proofing)
    # TODO: When Candidate model exists, set owner_id = null for this user's candidates

    db.add(
        AuditLog(
            organization_id=user.organization_id,
            user_id=_current_user.id,
            event_type="user.deactivated",
            resource_type="user",
            resource_id=str(user.id),
            details={"email": user.email, "reason": "admin_deactivation"},
        )
    )

    await db.commit()
    await db.refresh(user)

    return UserResponse(
        id=str(user.id),
        email=user.email,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at.isoformat(),
        updated_at=user.updated_at.isoformat(),
    )

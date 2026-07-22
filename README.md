# Core Features - ATS Backend

⏺ Task 1.3 Complete — Organization, User & Client Contact Management

  What was implemented

  New Routes:

  ┌─────────────────────────────┬────────┬───────────────┬────────────────────────────────────────────────┐
  │          Endpoint           │ Method │    Access     │                  Description                   │
  ├─────────────────────────────┼────────┼───────────────┼────────────────────────────────────────────────┤
  │ /api/v1/organizations       │ POST   │ SuperAdmin    │ Create organization (duplicate slug check)     │
  ├─────────────────────────────┼────────┼───────────────┼────────────────────────────────────────────────┤
  │ /api/v1/organizations/:id   │ GET    │ SuperAdmin    │ Get organization by ID                         │
  ├─────────────────────────────┼────────┼───────────────┼────────────────────────────────────────────────┤
  │ /api/v1/organizations/:id   │ PUT    │ SuperAdmin    │ Update organization (KMS key rotation note)    │
  ├─────────────────────────────┼────────┼───────────────┼────────────────────────────────────────────────┤
  │ /api/v1/users               │ GET    │ Admin/Manager │ List users with cursor pagination              │
  ├─────────────────────────────┼────────┼───────────────┼────────────────────────────────────────────────┤
  │ /api/v1/users/invite        │ POST   │ Admin/Manager │ Invite user via 48h magic link                 │
  ├─────────────────────────────┼────────┼───────────────┼────────────────────────────────────────────────┤
  │ /api/v1/users/:id           │ PUT    │ Admin/Manager │ Update user (reason required for role changes) │
  ├─────────────────────────────┼────────┼───────────────┼────────────────────────────────────────────────┤
  │ /api/v1/users/:id           │ DELETE │ Admin/Manager │ Deactivate user (increments token_version)     │
  ├─────────────────────────────┼────────┼───────────────┼────────────────────────────────────────────────┤
  │ /api/v1/client-contacts     │ GET    │ Admin/Manager │ List client contacts with pagination           │
  ├─────────────────────────────┼────────┼───────────────┼────────────────────────────────────────────────┤
  │ /api/v1/client-contacts     │ POST   │ Admin/Manager │ Create client contact (duplicate email check)  │
  ├─────────────────────────────┼────────┼───────────────┼────────────────────────────────────────────────┤
  │ /api/v1/client-contacts/:id │ PUT    │ Admin/Manager │ Update client contact                          │
  ├─────────────────────────────┼────────┼───────────────┼────────────────────────────────────────────────┤
  │ /api/v1/client-contacts/:id │ DELETE │ Admin/Manager │ Soft-delete (is_active=False)                  │
  └─────────────────────────────┴────────┴───────────────┴────────────────────────────────────────────────┘

  Key behaviors:
  - Role-based access control via require_role(["super_admin"]) / require_role(["admin", "manager"])
  - Tenant isolation via SET LOCAL app.organization_id from JWT org_id claim
  - Magic link tokens with 48h TTL for user invites
  - reason field required for role changes (ownership transfer)
  - User deactivation increments token_version, revoking all existing tokens
  - Soft-delete for client contacts and users (via is_active)
  - Cursor-based pagination (default 25, max 100)

  27 integration tests covering:
  - All CRUD operations with success/error paths
  - Role enforcement (recruiter blocked from admin endpoints)
  - Auth enforcement (unauthenticated requests rejected)
  - Duplicate slug/email validation (409 conflicts)
  - Tenant isolation (different org tokens produce different org_id)
  - Token revocation on deactivation
  - Refresh token rejection on protected endpoints
  - Password reset token expiry

  Test results

  68 passed, 5 warnings (41 existing + 27 new)
  
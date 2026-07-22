# ATS AI — Agent Guide

## Commands (run from `backend/`)

| Action | Command |
|--------|---------|
| Run all tests | `pytest` |
| Run single test | `pytest tests/test_file.py::test_name -v` |
| Run app | `uvicorn app.main:app` (or `docker compose up` from repo root) |
| Database migrations | `alembic -c db/alembic.ini upgrade head` |
| Bootstrap first superadmin | `python -m scripts.bootstrap` |
| Enable RLS policies | `python -m scripts.setup_rls` |

## Architecture

- **FastAPI** async app with `create_app()` factory (`app/main.py:39`). Module-level `app = create_app()` at bottom.
- **SQLAlchemy 2.0+ async** via `async_sessionmaker`. Session management in `app/database.py` (`get_session` yields, auto-commits/rollbacks).
- **PostgreSQL + Redis** required for full stack (Docker Compose provides both).
- **Multi-tenant**: Tenant isolation via `SET LOCAL app.organization_id` in tenant middleware + PostgreSQL RLS.
- **Auth**: JWT (access + refresh) via `python-jose`, bcrypt passwords, Bearer token `HTTPBearer`.
- **Route pattern**: Each domain has a router file in `app/routes/`, schema in `app/schemas/`, model in `app/models/`, optionally service in `app/services/`.
- **Migrations**: Raw Alembic Python files in `backend/db/versions/` (not auto-generated). Add new files as `NNN_description.py`.
- **Error handling**: Custom `AppException(code, message, status_code)` in `app/middleware/error_handler.py`. Returns `{"error": {"code": ..., "message": ..., "details": [...]}}`.
- **Pagination**: Cursor-based, `PaginationParams` dependency, `paginated_response()` helper (`app/middleware/pagination.py`). Default 25, max 100.

## Testing

- **No external services needed**: Tests mock Redis rate limiter via `mock_redis` fixture in `conftest.py`. Use `httpx.ASGITransport` (no real server).
- **Fixtures**: `app` calls `create_app()`, `client` provides `AsyncClient`. Tests create their own DB sessions via mock overrides.
- **Token helper pattern**: `_make_user_token(org_id, role, user_id)` generates JWTs inline for test auth.
- No pytest config found — runs with defaults.

## Conventions

- **Branch naming**: `task-X.Y-description` (e.g., `task-1.3-add-org-mgmt`)
- **Commit messages**: `task-X.Y: description` format
- **Style**: Type hints everywhere, no linter/typechecker config in repo (Python 3.14). No ruff, no mypy, no pre-commit.
- **`.env`**: Required for local runs. Copy `.env.example` from repo root, adjust as needed.
- **Docker**: Single `Dockerfile` in `backend/`. `docker-compose.yml` at repo root with api + postgres + redis.
- **Worktrees**: Active development uses `.claude/worktrees/` with git worktrees (e.g., `worktree-task-2-candidate-management`).

## Key Gotchas

- Session `get_session` commits on success, rolls back on exception — don't commit manually inside route handlers.
- Rate limiter uses Redis — skipped in tests via the `mock_redis` fixture.
- RLS policies and bootstrap are manual scripts, not part of migration. Run after `alembic upgrade head`.

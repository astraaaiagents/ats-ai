from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import async_session_factory
from app.middleware.error_handler import register_error_handlers
from app.middleware.rate_limit import close_redis_client
from app.middleware.request_id import RequestIDMiddleware
from app.middleware.tenant import TenantMiddleware
from app.routes.agent import agent_router
from app.routes.auth import auth_router
from app.routes.candidates import candidates_router
from app.routes.client_contacts import client_contacts_router
from app.routes.organizations import organizations_router
from app.routes.users import users_router


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    # Ensure dev user exists in DB when auth is bypassed
    if settings.bypass_auth:
        try:
            async with async_session_factory() as db:
                from app.auth.dependencies import ensure_dev_user
                await ensure_dev_user(db)
        except Exception:
            # Silently skip if DB is unavailable (e.g. tests)
            pass

    # Start the proactive monitor (sourcing pulse scheduler)
    from app.services.proactive_monitor import start_monitor
    start_monitor()

    yield

    # Stop the proactive monitor on shutdown
    from app.services.proactive_monitor import stop_monitor
    stop_monitor()
    await close_redis_client()


api_router = APIRouter(prefix="/api/v1")


@api_router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}

api_router.include_router(auth_router)
api_router.include_router(candidates_router)
api_router.include_router(organizations_router)
api_router.include_router(users_router)
api_router.include_router(client_contacts_router)
api_router.include_router(agent_router)


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(TenantMiddleware)

    register_error_handlers(app)

    app.include_router(api_router)

    return app


app = create_app()

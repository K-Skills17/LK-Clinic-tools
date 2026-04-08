"""
LK Clinic Tools - FastAPI Application
Main entry point for the backend API.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import traceback
import sys

try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.errors import RateLimitExceeded
    from slowapi.middleware import SlowAPIMiddleware
    from slowapi.util import get_remote_address
except Exception as e:
    print(f"STARTUP ERROR importing slowapi: {e}", flush=True)
    traceback.print_exc()

try:
    from config import get_settings
except Exception as e:
    print(f"STARTUP ERROR importing config: {e}", flush=True)
    traceback.print_exc()
    sys.exit(1)

try:
    from routers import (
        agency_dashboard,
        analytics,
        appointments,
        auth,
        bot_contacts,
        bot_conversations,
        bots,
        clinics,
        google_reviews,
        knowledge_base,
        message_templates,
        negative_feedback,
        reminders,
        review_requests,
        review_responses,
        seo_alerts,
        seo_monitor,
        waitlist,
        webhooks,
    )
except Exception as e:
    print(f"STARTUP ERROR importing routers: {e}", flush=True)
    traceback.print_exc()
    sys.exit(1)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    # Startup
    settings = get_settings()
    print(f"LK Clinic Tools starting in {settings.app_env} mode")
    yield
    # Shutdown
    print("LK Clinic Tools shutting down")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="LK Clinic Tools API",
        description="Plataforma de automação para clínicas - LK Digital",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
    )

    # --- Rate Limiting (added BEFORE CORS so CORS runs first) ---
    limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])
    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # --- CORS (added LAST = runs FIRST in middleware chain) ---
    print(f"CORS origins: {settings.cors_origins}", flush=True)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Routers ---
    api_prefix = "/api"

    app.include_router(auth.router, prefix=f"{api_prefix}/auth", tags=["Auth"])
    app.include_router(clinics.router, prefix=f"{api_prefix}/clinics", tags=["Clínicas"])
    app.include_router(
        agency_dashboard.router,
        prefix=f"{api_prefix}/agency",
        tags=["Agência"],
    )

    # Module 1: Appointments
    app.include_router(
        appointments.router,
        prefix=f"{api_prefix}/clinics/{{clinic_id}}/appointments",
        tags=["Consultas"],
    )
    app.include_router(
        reminders.router,
        prefix=f"{api_prefix}/clinics/{{clinic_id}}/reminders",
        tags=["Lembretes"],
    )
    app.include_router(
        waitlist.router,
        prefix=f"{api_prefix}/clinics/{{clinic_id}}/waitlist",
        tags=["Lista de Espera"],
    )

    # Module 2: Reviews
    app.include_router(
        review_requests.router,
        prefix=f"{api_prefix}/clinics/{{clinic_id}}/review-requests",
        tags=["Solicitações de Avaliação"],
    )
    app.include_router(
        google_reviews.router,
        prefix=f"{api_prefix}/clinics/{{clinic_id}}/google-reviews",
        tags=["Avaliações Google"],
    )
    app.include_router(
        review_responses.router,
        prefix=f"{api_prefix}/clinics/{{clinic_id}}/review-responses",
        tags=["Respostas de Avaliação"],
    )
    app.include_router(
        negative_feedback.router,
        prefix=f"{api_prefix}/clinics/{{clinic_id}}/feedback",
        tags=["Feedback Negativo"],
    )

    # Module 3: Chatbot
    app.include_router(
        bots.router,
        prefix=f"{api_prefix}/clinics/{{clinic_id}}/bots",
        tags=["Chatbots"],
    )
    app.include_router(
        knowledge_base.router,
        prefix=f"{api_prefix}/clinics/{{clinic_id}}/knowledge-base",
        tags=["Base de Conhecimento"],
    )
    app.include_router(
        bot_conversations.router,
        prefix=f"{api_prefix}/clinics/{{clinic_id}}/conversations",
        tags=["Conversas"],
    )
    app.include_router(
        bot_contacts.router,
        prefix=f"{api_prefix}/clinics/{{clinic_id}}/contacts",
        tags=["Contatos"],
    )

    # Module 4: SEO
    app.include_router(
        seo_monitor.router,
        prefix=f"{api_prefix}/clinics/{{clinic_id}}/seo",
        tags=["SEO Monitor"],
    )
    app.include_router(
        seo_alerts.router,
        prefix=f"{api_prefix}/clinics/{{clinic_id}}/seo-alerts",
        tags=["Alertas SEO"],
    )

    # Shared
    app.include_router(
        analytics.router,
        prefix=f"{api_prefix}/clinics/{{clinic_id}}/analytics",
        tags=["Analytics"],
    )
    app.include_router(
        message_templates.router,
        prefix=f"{api_prefix}/clinics/{{clinic_id}}/templates",
        tags=["Templates de Mensagem"],
    )

    # Webhooks (external)
    app.include_router(
        webhooks.router,
        prefix=f"{api_prefix}/webhooks",
        tags=["Webhooks"],
    )

    # --- Health Check ---
    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "service": "lk-clinic-tools"}

    return app


try:
    app = create_app()
    print("APP CREATED SUCCESSFULLY", flush=True)
except Exception as e:
    print(f"FATAL: Failed to create app: {e}", flush=True)
    traceback.print_exc()
    # Create a minimal app that just shows the error
    app = FastAPI()
    error_msg = str(e)
    @app.get("/health")
    async def health_error():
        return {"status": "error", "detail": error_msg}
    @app.get("/")
    async def root_error():
        return {"status": "error", "detail": error_msg}

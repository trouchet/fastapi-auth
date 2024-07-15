from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .logging import RequestLoggingMiddleware
from backend.app.middlewares.throttling import RateLimitMiddleware
from backend.app.middlewares.validation import RouteValidationMiddleware
from backend.app.base.auth import get_current_user
from backend.app.base.config import settings

def add_middlewares(app: FastAPI):
    # Add middlewares
    app.add_middleware(RouteValidationMiddleware)
    app.add_middleware(RequestLoggingMiddleware, identifier_callable=get_current_user)
    app.add_middleware(RateLimitMiddleware, identifier_callable=get_current_user)

    # Add CORS middleware
    if settings.BACKEND_CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[
                str(origin).strip("/") 
                for origin in settings.BACKEND_CORS_ORIGINS
            ],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )


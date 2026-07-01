from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import AppException
from app.integrations.flights.factory import flight_provider_label


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.services.airport_catalog import get_airport_catalog

    catalog = get_airport_catalog()
    app.state.airport_catalog_size = len(catalog.airports)
    app.state.flight_provider = flight_provider_label()
    app.state.flight_provider_ready = bool(
        settings.should_use_db_prices()
        or settings.SERPAPI_API_KEY
        or (settings.AMADEUS_CLIENT_ID and settings.AMADEUS_CLIENT_SECRET)
    )
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "Family Trip Planner — intelligent travel planning platform for families. "
            "Provides destination recommendations, budget optimization, itinerary generation, "
            "and child-friendly activity suggestions using a hybrid rule-based + LLM engine."
        ),
        lifespan=lifespan,
    )

    origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})

    app.include_router(api_router)

    @app.get("/health", tags=["Health"])
    async def health(request: Request):
        ready = getattr(request.app.state, "flight_provider_ready", False)
        provider = getattr(request.app.state, "flight_provider", "unknown")
        hint = None
        if not ready:
            hint = (
                "Add SERPAPI_API_KEY, AMADEUS credentials, or set USE_DB_PRICES=true for cached DB prices — "
                "SerpAPI: https://serpapi.com/manage-api-key | Amadeus: https://developers.amadeus.com"
            )
        elif provider == "amadeus" and not settings.AMADEUS_CLIENT_ID:
            hint = "Amadeus selected but credentials missing"
        return {
            "status": "ok",
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "airport_catalog_size": getattr(request.app.state, "airport_catalog_size", 0),
            "flight_provider": provider,
            "flight_provider_ready": ready,
            "flight_provider_hint": hint,
        }

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )

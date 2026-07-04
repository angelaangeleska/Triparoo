from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="..env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "Family Trip Planner"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/family_trip_planner"
    SECRET_KEY: str = "change-me-to-a-long-random-secret-key"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"

    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/google/callback"

    # TODO: get a free key at https://console.groq.com/keys. Powers real AI-generated
    # recommendation explanations (app/services/groq_service.py), itinerary narratives,
    # and the AI Trip Guide (app/services/ai_trip_guide_service.py). Falls back to
    # deterministic rule-based text when unset — never crashes without it.
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    # TODO: enable "Places API (New)" in Google Cloud Console and get a self-serve key —
    # https://developers.google.com/maps/documentation/places/web-service/get-api-key.
    # Substitutes for the TripAdvisor Content API, which requires a partner agreement
    # with no public signup. Powers app/integrations/places (attractions, restaurants,
    # landmarks, reviews, ratings, photos). Empty = feature disabled, no crash.
    GOOGLE_PLACES_API_KEY: str = ""

    # TODO: professor will supply real Amadeus for Developers credentials —
    # https://developers.amadeus.com/my-apps. Amadeus is the sole flight and
    # hotel provider (see app/integrations/flights/factory.py and
    # app/integrations/accommodations/factory.py).
    AMADEUS_CLIENT_ID: str = ""
    AMADEUS_CLIENT_SECRET: str = ""
    AMADEUS_BASE_URL: str = "https://test.api.amadeus.com"

    # Rule engine weights (sum used for normalization)
    WEIGHT_CHILD_AGE: float = 0.20
    WEIGHT_BUDGET: float = 0.20
    WEIGHT_SEASON: float = 0.15
    WEIGHT_POPULARITY: float = 0.10
    WEIGHT_FAMILY_FRIENDLY: float = 0.15
    WEIGHT_ACTIVITY: float = 0.10
    WEIGHT_WEATHER: float = 0.10

    HYBRID_RULE_WEIGHT: float = 0.7
    HYBRID_LLM_WEIGHT: float = 0.3

    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173"


settings = Settings()

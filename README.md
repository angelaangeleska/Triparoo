# Family Trip Planner

An intelligent travel planning platform for families, built with **FastAPI**, **PostgreSQL**, and a **hybrid recommendation engine** (rule-based scoring + LLM reasoning abstraction).

## Features

- **Family destination recommendations** — ranked destinations with score breakdowns and child-friendly attractions
- **Cheapest destination search** — find affordable destinations for your dates and budget
- **Cheapest dates search** — discover the best periods to visit a destination
- **AI itinerary generation** — day-by-day travel plans tailored to your family
- **Child-friendly activity recommendations** — matched by age, interests, and gender
- **Budget optimization** — compare alternatives for dates, accommodations, and destinations
- **Flight & accommodation search** — provider abstraction with mock implementations
- **Authentication** — JWT access/refresh tokens, register/login, Google OAuth

## Architecture

Clean architecture with layered separation:

```
api/ → services/ → repositories/ → models/
                ↘ recommendation/ + integrations/
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed design documentation.

## Quick Start (Docker)

```bash
docker compose up --build
```

- API: http://localhost:8000
- **Frontend:** http://localhost:5173
- OpenAPI docs: http://localhost:8000/docs
- Demo user: `demo@familytrip.com` / `DemoPass123!`

## Frontend

A React + TypeScript + Tailwind CSS web app lives in [`frontend/`](frontend/).

### Run locally

```bash
# Terminal 1 — backend (see below)
uvicorn app.main:app --reload

# Terminal 2 — frontend
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 — the Vite dev server proxies `/api` to the backend.

### Pages

| Page | Description |
|------|-------------|
| `/` | Landing page with hero, features, and CTA |
| `/planner` | Family trip recommendation wizard |
| `/destinations` | Browse all destinations |
| `/destinations/:id` | Detail with itinerary, kids activities, dates, budget tabs |
| `/login` | Sign in (demo credentials pre-filled) |

## Local Development

### Prerequisites

- Python 3.12+
- PostgreSQL 16

### Setup

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
cp .env.example .env          # edit DATABASE_URL if needed
alembic upgrade head
python -m app.utils.seed
uvicorn app.main:app --reload
```

## API Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register a new user |
| POST | `/api/v1/auth/login/json` | Login and receive JWT tokens |
| POST | `/api/v1/auth/refresh` | Refresh access token |
| GET | `/api/v1/auth/google/login` | Get Google OAuth URL |
| POST | `/api/v1/trip-planner/recommend` | Get destination recommendations |
| POST | `/api/v1/trip-planner/cheapest-destinations` | Find cheapest destinations |
| POST | `/api/v1/trip-planner/cheapest-dates` | Find cheapest travel periods |
| POST | `/api/v1/trip-planner/itinerary` | Generate day-by-day itinerary |
| POST | `/api/v1/trip-planner/child-activities` | Child-friendly activity suggestions |
| POST | `/api/v1/trip-planner/budget-optimize` | Budget optimization suggestions |
| GET | `/api/v1/destinations` | List all destinations |
| GET | `/api/v1/activities` | List activities |
| GET | `/api/v1/flights` | Search flights |
| GET | `/api/v1/accommodations` | List accommodations |

### Example: Family Recommendation

```bash
# Login
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login/json \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@familytrip.com","password":"DemoPass123!"}' \
  | jq -r .access_token)

# Get recommendations
curl -X POST http://localhost:8000/api/v1/trip-planner/recommend \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "members": [
      {"age": 35},
      {"age": 33},
      {"age": 11, "gender": "female", "interests": ["disney", "science"]}
    ],
    "budget": 1500,
    "preferred_month": 8
  }'
```

## Testing

```bash
pytest
```

## Project Structure

```
app/
├── api/              # FastAPI routers and dependencies
├── auth/             # OAuth integrations
├── core/             # Config, security, exceptions
├── db/               # Database engine and session
├── integrations/     # Flight & accommodation providers
├── models/           # SQLAlchemy ORM models
├── recommendation/   # Hybrid recommendation engine
├── repositories/     # Data access layer
├── schemas/          # Pydantic request/response DTOs
├── services/         # Business logic
├── tests/            # Unit and integration tests
└── utils/            # Seed data and utilities
```

## Extensibility

Provider interfaces allow swapping implementations without changing business logic:

- `RecommendationProvider` → OpenAI, Gemini, Claude
- `FlightProvider` → Amadeus, Kiwi, Skyscanner
- `AccommodationProvider` → Booking.com, Airbnb, Expedia

Configure via environment variables: `RECOMMENDATION_PROVIDER`, `FLIGHT_PROVIDER`, `ACCOMMODATION_PROVIDER`.

## License

University project — for educational purposes.

# Triparoo — Family Trip Planner

An intelligent travel planning platform for families, built with **FastAPI**, **PostgreSQL**, and a **hybrid
recommendation engine** (rule-based scoring + real Groq AI reasoning). The frontend is a **React + TypeScript**
SPA styled with **Tailwind CSS** and Radix-based UI primitives, with bilingual (EN/MK) and dark/light support.

## Features

- **Family destination recommendations** — ranked destinations with score breakdowns and a real AI-generated
  explanation + highlights per pick (falls back to deterministic text if no AI key is configured)
- **Saved family profile** — ages, genders, and interests are entered once and reused everywhere (Trip Planner,
  Kids Activities, itinerary, budget) — no re-entering the same information twice
- **Trip history** — every search is recorded and browsable on the "My Trips" page
- **Cheapest destination / cheapest dates search** — find affordable destinations and travel periods
- **AI itinerary generation** — day-by-day travel plans with a short AI-written narrative per day
- **Child-friendly activity recommendations** — matched by age and interests, auto-loaded per saved child
- **AI Trip Guide** — AI-generated restaurants, hidden gems, local tips, and transportation advice, grounded with
  live Google Places data when configured
- **Budget optimization** — compare alternatives for dates, accommodations, and destinations
- **Flight & accommodation search** — live prices via Amadeus (sole provider for both)
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
- Demo user: `demo@familytrip.com` / `DemoPass123!` (seeded with a starter family: 2 adults, 1 child)

## Required API keys

None of these are required for the app to run — every integration fails soft (falls back to rule-based text, or
returns empty results) when its key is missing. See `.env.example` for the exact variables.

| Service | Purpose | Get a key |
|---|---|---|
| **Amadeus** | Sole flight & hotel provider | Free test credentials at https://developers.amadeus.com/my-apps |
| **Groq** | Real AI recommendation explanations, itinerary narratives, AI Trip Guide | Free key at https://console.groq.com/keys |
| **Google Places (New)** | Attractions/restaurants/landmarks/reviews/ratings/photos — self-serve substitute for the TripAdvisor Content API, which requires a partner agreement with no public signup | Google Cloud Console — enable "Places API (New)" |
| **Google OAuth** | "Sign in with Google" | Google Cloud Console OAuth client |

## Frontend

A React + TypeScript + Vite + Tailwind CSS web app lives in [`frontend/`](frontend/).

- **UI kit**: Radix primitives + Tailwind + class-variance-authority (no MUI/Chakra runtime overhead)
- **Data fetching**: `@tanstack/react-query` (caching, loading states, mutation-driven cache invalidation)
- **Forms**: `react-hook-form` + `zod`
- **i18n**: `react-i18next`, English default, Macedonian toggle, persisted to `localStorage`
- **Theme**: dark/light mode, persisted, defaults to system preference
- **Testing**: Vitest + React Testing Library

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
| `/login`, `/register` | Auth (demo credentials pre-filled on login) |
| `/planner` *(auth required)* | Family trip recommendation wizard — loads/syncs your saved family profile |
| `/family` *(auth required)* | Manage your saved family members |
| `/trips` *(auth required)* | Browse your trip search history |
| `/destinations` | Browse all destinations |
| `/destinations/:id` | Overview, itinerary, Kids activities, AI Trip Guide, best dates, and budget tabs |

## Local Development

### Prerequisites

- Python 3.12+
- PostgreSQL 16
- Node 20+

### Setup

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
cp .env.example .env          # edit DATABASE_URL and add API keys as you get them
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
| GET/POST | `/api/v1/family-members` | List / add saved family members |
| PUT/DELETE | `/api/v1/family-members/{id}` | Update / remove a saved family member |
| POST | `/api/v1/trip-planner/recommend` | Get destination recommendations (records trip history) |
| POST | `/api/v1/trip-planner/cheapest-destinations` | Find cheapest destinations |
| POST | `/api/v1/trip-planner/cheapest-dates` | Find cheapest travel periods |
| POST | `/api/v1/trip-planner/itinerary` | Generate day-by-day itinerary |
| POST | `/api/v1/trip-planner/child-activities` | Child-friendly activity suggestions |
| POST | `/api/v1/trip-planner/budget-optimize` | Budget optimization suggestions |
| POST | `/api/v1/trip-planner/ai-guide` | AI-generated restaurants, hidden gems, local tips |
| GET | `/api/v1/trip-history` | List your past trip searches |
| GET | `/api/v1/trip-history/{id}` | Trip search detail |
| GET | `/api/v1/destinations` | List all destinations |
| GET | `/api/v1/destinations/{id}/places` | Live Google Places results for a destination |
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
# Backend
pytest

# Frontend
cd frontend
npm run test
```

## Project Structure

```
app/
├── api/              # FastAPI routers and dependencies
├── auth/             # OAuth integrations
├── core/             # Config, security, exceptions
├── db/               # Database engine and session
├── integrations/     # Flight, accommodation & places providers (Amadeus, Google Places)
├── models/           # SQLAlchemy ORM models
├── recommendation/   # Hybrid recommendation engine (rule-based + Groq)
├── repositories/     # Data access layer
├── schemas/          # Pydantic request/response DTOs
├── services/         # Business logic
├── tests/            # Unit and integration tests
└── utils/            # Seed data and utilities

frontend/src/
├── api/              # Fetch client + react-query hooks
├── components/       # ui/ (primitives), layout/, planner/, family/, destinations/
├── context/          # Auth, theme
├── locales/          # en.json, mk.json
├── pages/            # Route-level pages (+ *.test.tsx)
└── test/             # Vitest setup
```

## Extensibility

Provider interfaces allow swapping implementations without changing business logic:

- `RecommendationProvider` → currently Groq; swapping to OpenAI/Gemini/Claude is a one-file change
  (`app/services/groq_service.py` + `app/recommendation/factory.py`)
- `FlightProvider` / `AccommodationProvider` → currently Amadeus only
- `PlacesProvider` → currently Google Places; swap for the official TripAdvisor Content API once a partner
  agreement is in place

## License

University project — for educational purposes.

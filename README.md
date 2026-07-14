# Veloura

**AI-powered fashion e-commerce for men and women.** Browse a curated catalog, build a cart,
check out, and chat with an AI stylist that builds complete outfits exclusively from products
that are actually in stock — never invented.

> **Screenshots:** add screenshots of the home page, shop page, product detail, and AI stylist
> here before sharing this README externally (e.g. `docs/screenshots/home.png`).

## Features

- **Browse & discover** — editorial home page, men's/women's/unisex catalog, search, category
  / size / color / price filters, sorting, pagination.
- **Product detail** — image gallery, color and size selection, live inventory state, related
  products.
- **Cart & wishlist** — add/update/remove, quantity limited by real inventory, guest-safe cart
  drawer, save-for-later wishlist.
- **Simulated checkout** — shipping address form, transparent subtotal/shipping/tax/total
  breakdown, inventory-safe order creation, order history and detail pages.
- **AI Stylist** — describe an occasion, mood, colors, or budget in plain English; get back a
  complete outfit built only from real, in-stock catalog items, with per-item and whole-outfit
  "add to cart," and follow-up refinement suggestions.
- **Admin panel** — product CRUD, variant/inventory management, order status updates, all behind
  role-gated auth.

## Architecture & tech stack

Modular monolith: one FastAPI service, one React SPA, one Postgres database. See
[`docs/architecture.md`](docs/architecture.md) for the full breakdown and the AI request flow.

| Layer | Stack |
|---|---|
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, React Router, TanStack Query, Zustand, React Hook Form + Zod, Framer Motion, Axios |
| Backend | Python 3.13, FastAPI, Pydantic, SQLAlchemy 2.x, Alembic, psycopg3, JWT auth, bcrypt, OpenAI SDK |
| Database | PostgreSQL + pgvector (Neon in production) |
| Infra | Docker Compose (local), GitHub Actions CI, Vercel (frontend), Render (backend) |

## Repository structure

```
veloura/
├── apps/
│   ├── api/     FastAPI backend (src/veloura_api, tests/, alembic/)
│   └── web/     React frontend (src/)
├── scripts/     seed_products.py, generate_embeddings.py
├── docs/        architecture.md, api.md, deployment.md
├── .github/workflows/ci.yml
├── docker-compose.yml
├── Makefile
└── .env.example
```

## Local setup

Prerequisites: Docker, Python 3.13, Node.js 18+ (20+ recommended).

```bash
cp .env.example .env
docker compose up -d postgres   # Postgres 16 + pgvector on localhost:5433
make install                    # backend venv + npm install
make migrate                    # apply Alembic migrations
make seed                       # 60+ products, categories, demo users, sample orders
make dev-api                    # terminal 1 — http://localhost:8000
make dev-web                    # terminal 2 — http://localhost:5173
```

> **Note:** the Postgres container is mapped to host port **5433**, not 5432, to avoid clashing
> with any Postgres already running locally. `.env.example` is already set up for this. If you
> run the full stack via `docker compose up -d` (all three services), the API and web containers
> talk to Postgres over the internal Docker network on the standard port 5432 — the 5433 mapping
> only matters when running the API directly on your host.

Alternatively, run all three services in Docker (Postgres, API, and the frontend dev server):

```bash
cp .env.example .env
docker compose up -d --build
docker compose exec api alembic upgrade head
make seed   # runs from the host against localhost:5433, which docker-compose maps to the postgres container
```

The `web` container runs the Vite dev server (hot reload) rather than a production build — see
[`docs/deployment.md`](docs/deployment.md) for how the frontend is actually built and served in
production, via Vercel.

Full command reference:

| Command | Description |
|---|---|
| `make install` | Create the backend venv, install Python deps, run `npm install` |
| `make dev-api` / `make dev-web` | Run the backend / frontend dev servers |
| `make test` | Run the backend pytest suite |
| `make lint` | Ruff (backend) + ESLint (frontend) |
| `make format` | Ruff format (backend) |
| `make migrate` | Apply Alembic migrations |
| `make migration m="add foo"` | Generate a new Alembic migration |
| `make seed` | Run `scripts/seed_products.py` (idempotent) |
| `make generate-embeddings` | Backfill pgvector embeddings (requires `OPENAI_API_KEY`) |
| `make build` | Production build of the frontend |

## Environment variables

See [`.env.example`](.env.example) for the full annotated list. Key variables:

```
DATABASE_URL=postgresql+psycopg://veloura:veloura@localhost:5433/veloura?sslmode=disable

OPENAI_API_KEY=
OPENAI_CHAT_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

JWT_SECRET_KEY=replace-with-a-long-random-secret
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440

VELOURA_CORS_ALLOWED_ORIGINS=http://localhost:5173
LOG_LEVEL=INFO

VITE_API_BASE_URL=http://localhost:8000/api
```

`OPENAI_API_KEY` is optional for local development: with no key set, the AI stylist automatically
falls back to a deterministic, rule-based preference extractor and outfit builder so the feature
is still fully functional end-to-end (see [Known MVP limitations](#known-mvp-limitations)).

## Database migrations & seed data

```bash
make migrate   # apply all Alembic migrations (creates tables + enables pgvector)
make seed      # idempotent: categories, 60+ products with variants, demo users, sample orders/outfits
make generate-embeddings   # optional: backfill pgvector embeddings for semantic AI-stylist ranking
```

## Testing

```bash
make test                                    # backend: 45 tests (pytest)
cd apps/web && npm run test && npm run typecheck && npm run lint && npm run build   # frontend
```

Backend tests cover registration/login, product listing/filtering/detail, cart (including
insufficient-inventory rejection), checkout/order creation with inventory decrement, wishlist,
admin authorization, AI preference extraction, product candidate retrieval, and — explicitly —
that hallucinated product/variant IDs are stripped before ever reaching a response. OpenAI is
never called in CI: tests run with `OPENAI_API_KEY=""`, which routes the AI stylist through its
deterministic fallback path.

## Demo credentials

| Role | Email | Password |
|---|---|---|
| Admin | `admin@veloura.com` | `AdminPass123!` |
| Customer | `customer@veloura.com` | `CustomerPass123!` |

These are development-only credentials created by `make seed` — do not reuse them in a real
deployment without changing the passwords.

## API documentation

Interactive docs: `/docs` (Swagger UI) and `/redoc` on the running API. Reference summary:
[`docs/api.md`](docs/api.md).

## Deployment

Full step-by-step instructions: [`docs/deployment.md`](docs/deployment.md).

- **Frontend → Vercel:** root directory `apps/web`, build `npm run build`, output `dist`,
  env var `VITE_API_BASE_URL=https://<render-service>.onrender.com/api`.
- **Backend → Render:** root directory `apps/api`, start command
  `uvicorn veloura_api.main:app --host 0.0.0.0 --port $PORT`, env vars as listed above with
  `VELOURA_CORS_ALLOWED_ORIGINS=https://<vercel-domain>.vercel.app`.
- **Database → Neon:** enable the `vector` extension, run `alembic upgrade head` and
  `scripts/seed_products.py` against the Neon connection string.

## Known MVP limitations

- **AI stylist fallback quality.** Without `OPENAI_API_KEY`, preference extraction and outfit
  assembly use a deterministic heuristic (keyword matching + cheapest-first, slot-aware item
  selection) rather than an LLM. It respects budget, colors, and occasion at a basic level, but
  the real OpenAI-backed path (structured outputs via `client.beta.chat.completions.parse`)
  produces materially better, more nuanced outfits and explanations. Both paths share the same
  anti-hallucination validation layer.
- **No real payments.** Checkout is simulated — no Stripe or other payment processor is
  integrated. Orders are created and inventory is decremented, but no money moves.
- **No true token streaming.** The AI stylist chat UI shows a "thinking" indicator rather than
  token-by-token SSE streaming; the spec called this out as "if practical," and request/response
  was chosen for reliability given the added complexity of streaming structured, validated JSON.
- **Seed catalog imagery.** Product photography is drawn from a curated pool of ~40 verified
  Unsplash images per category, reused across multiple SKUs (with per-product color swatches
  providing visual variety) rather than one unique photo per variant.
- **Single currency, US-only tax/shipping model.** Pricing rules are the simple, documented ones
  in the spec (flat-rate shipping threshold, flat tax rate) — no multi-region tax or carrier
  integration.
- **Admin product creation is manual per-request.** There's no bulk import/CSV upload in the
  admin UI; products are created one at a time (with initial variants) through the form.

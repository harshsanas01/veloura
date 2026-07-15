# Veloura

**AI-powered fashion e-commerce for men and women.** Browse a 600+ item catalog, build a cart,
apply coupons, check out, leave reviews, and chat with an AI stylist that builds complete outfits
exclusively from products that are actually in stock — never invented.

> **Screenshots:** add screenshots of the home page, shop page, product detail, and AI stylist
> here before sharing this README externally (e.g. `docs/screenshots/home.png`).

## Features

- **Catalog** — 608 products across 15 categories, gender-correct throughout (verified
  photography, filtering, related products, and AI retrieval all respect gender), realistic
  non-repetitive naming, 15 fictional house brands, search, brand/material/occasion/season/price
  filters, sale-only and in-stock-only toggles, active filter chips, breadcrumbs, pagination.
- **Product detail** — thumbnail gallery with fullscreen zoom, size guide modal, color/size
  selection with live inventory and low-stock warnings, material & care and shipping/returns
  accordion, customer reviews with rating distribution, "Complete the Look" and "Customers Also
  Bought" rails, recently-viewed tracking, share button.
- **Auth & accounts** — registration with a live password-strength checklist, show/hide password,
  duplicate-email protection, profile editing, password change, account deletion, saved addresses
  (separate default shipping/billing), a style profile (colors, styles, budget, brands) that
  personalizes the AI stylist.
- **Cart & wishlist** — guest cart (localStorage) that merges into the account cart on
  login/register, server-computed shipping/tax/discount/free-shipping-progress, coupon codes,
  move-to-wishlist and move-to-cart (with variant picker), sale-price badges.
- **Coupons** — percentage/fixed discounts, free-shipping override, minimum order value, maximum
  discount cap, global and per-user usage limits, category/product scoping — all validated
  server-side (the frontend only ever displays what the API computed).
- **Checkout & orders** — shipping form, order notes, coupon application, server-side inventory
  re-validation inside a DB transaction, order status timeline, customer-initiated cancellation
  (before shipping) with automatic inventory restoration, admin status updates that also restore
  inventory on cancel/return.
- **Inventory transactions** — every stock change (order placed, cancelled, returned, or manually
  adjusted by an admin with a required reason) is recorded in an immutable audit log.
- **Reviews & ratings** — one review per user per product, verified-purchase badge, fit feedback,
  edit/delete own review, helpful voting, sort by newest/highest/lowest/most-helpful, admin
  moderation (hide/show).
- **Recommendations** — deterministic (not ML) "Trending Now" (recent sales), "Customers Also
  Bought" (co-purchase), and "Complete the Look" (complementary category slots), plus
  client-tracked "Recently Viewed."
- **AI Stylist** — describe an occasion, mood, colors, or budget in plain English; get back a
  complete outfit built only from real, in-stock catalog items. Supports conversational
  refinement ("make it cheaper," "make it more formal," "change the color to X," "replace the
  shoes") as deterministic edits to the existing outfit, uses your saved style profile and current
  cart ("build an outfit around the jacket in my cart") as context, and per-item / whole-outfit
  "add to cart."
- **Admin panel** — real dashboard metrics (revenue, orders, customers, AOV, low/out-of-stock,
  best-sellers, top categories), paginated + searchable product/order/customer tables, product and
  variant CRUD, inventory adjustments with a required reason, coupon management, review
  moderation, feature/unfeature and activate/deactivate toggles, confirmation dialogs before
  destructive actions — all behind role-gated auth.

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
├── scripts/     seed_products.py, reseed_products.py, generate_embeddings.py
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
make seed                       # 608 products, categories, demo users/orders, coupons, reviews
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
| `make lint` | Ruff + mypy (backend) + ESLint (frontend) |
| `make format` | Ruff format (backend) |
| `make migrate` | Apply Alembic migrations |
| `make migration m="add foo"` | Generate a new Alembic migration |
| `make seed` | Run `scripts/seed_products.py` (idempotent — see below) |
| `make reseed-products` | Dry-run report of seed-owned products eligible for permanent deletion (see below) |
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

No new environment variables were introduced by the feature work in this repository's history —
everything (coupons, reviews, inventory transactions, recommendations, AI refinement) reuses the
existing `DATABASE_URL` / `OPENAI_API_KEY` / `JWT_SECRET_KEY` configuration.

`OPENAI_API_KEY` is optional for local development: with no key set, the AI stylist automatically
falls back to a deterministic, rule-based preference extractor and outfit builder so the feature
is still fully functional end-to-end (see [Known limitations](#known-limitations)).

**Never commit a real key into `.env.example`.** That file is a template and is tracked in git —
real secrets belong only in your local `.env` (gitignored).

## Database migrations & seed data

```bash
make migrate   # apply all Alembic migrations (creates tables + enables pgvector)
make seed      # idempotent: categories, 608 products with variants, demo users/orders/outfits,
               # demo coupons (WELCOME10, STYLE20, FREESHIP), sample reviews
make generate-embeddings   # optional: backfill pgvector embeddings for semantic AI-stylist ranking
```

`make seed` is always safe to re-run against an existing database: it matches rows by slug/email
and skips anything already present, and it never deletes real user data. If it detects products
left over from an older, narrower generation of the seed script, it **deactivates** them (so the
storefront only shows the current catalog) rather than deleting them — this preserves referential
integrity for any historical orders that reference them.

To actually purge those deactivated rows (e.g. to shrink a dev database after a catalog rewrite),
use the explicit, opt-in cleanup script:

```bash
python scripts/reseed_products.py            # dry run — reports what would be deleted
python scripts/reseed_products.py --confirm  # actually deletes inactive, seed-owned products
```

This script only ever touches products whose brand is a known Veloura seed brand and that are
already inactive; it never touches real admin-created products, and any row still referenced by
an existing order is protected at the database level (`ON DELETE RESTRICT`) and skipped with a
warning rather than breaking order history.

## Testing

```bash
make test                                    # backend: 125 tests (pytest)
cd apps/web && npm run test && npm run typecheck && npm run lint && npm run build   # frontend
```

Backend tests cover registration/password-policy/login, product listing/filtering/gender
correctness/facets, cart (guest merge, insufficient-inventory rejection), coupon validation
(min-order, max-discount, per-user/global limits, category scoping), checkout/order creation with
transactional inventory decrement, order cancellation and inventory restoration, reviews
(duplicate prevention, permissions, moderation), recommendations, wishlist (move-to-cart variant
validation), admin authorization and CRUD, AI preference extraction, product candidate retrieval,
AI refinement actions, and — explicitly — that hallucinated product/variant IDs are stripped
before ever reaching a response. OpenAI is never called in CI: tests run with
`OPENAI_API_KEY=""`, which routes the AI stylist through its deterministic fallback path.

## Demo credentials

| Role | Email | Password |
|---|---|---|
| Admin | `admin@veloura.com` | `AdminPass123!` |
| Customer | `customer@veloura.com` | `CustomerPass123!` |

These are development-only credentials created by `make seed` — do not reuse them in a real
deployment without changing the passwords.

## Demo coupons

Seeded by `make seed`:

| Code | Discount | Notes |
|---|---|---|
| `WELCOME10` | 10% off | Once per customer |
| `STYLE20` | 20% off | $150 minimum order, capped at $75 off |
| `FREESHIP` | Free shipping | $50 minimum order |

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

## Known limitations

- **AI stylist fallback quality.** Without `OPENAI_API_KEY`, preference extraction and outfit
  assembly use a deterministic heuristic (keyword matching + cheapest-first, slot-aware item
  selection) rather than an LLM. Refinement actions (cheaper/more formal/change color/replace
  item) are always deterministic regardless of the key, by design. The real OpenAI-backed path
  produces materially better, more nuanced initial outfits and explanations. Both paths share the
  same anti-hallucination validation layer.
- **No real payments.** Checkout is simulated — no Stripe or other payment processor is
  integrated. Orders are created and inventory is decremented, but no money moves.
- **No true token streaming.** The AI stylist chat UI shows a "thinking" indicator rather than
  token-by-token SSE streaming.
- **Guest checkout requires an account.** Guests can browse and build a cart (persisted in
  localStorage, merged into the account cart on login/register); placing an order still requires
  signing in. True anonymous checkout was out of scope for this pass.
- **Wishlist is a single default list.** Multiple named wishlists/collections and
  shareable/public links were not implemented (the spec explicitly allows this simplification).
- **Category taxonomy is fixed.** The 15 top-level categories are seed-managed; there is no admin
  UI to add/rename/delete categories, since the whole catalog, filter, and recommendation-slot
  logic assumes this fixed taxonomy.
- **"Best Rated" / "Most Popular" sort options are deferred.** They depend on the review and
  recommendation data introduced in this pass; `biggest_discount`, `featured`, `newest`, and both
  price sorts are implemented today. Adding the other two is a small follow-up now that the
  underlying tables exist.
- **No bulk product import.** Admin product creation is one at a time through the form; no
  CSV/bulk upload.
- **No visual/browser QA in this environment.** Changes were verified via automated tests, type
  checking, linting, production builds, and extensive live HTTP smoke tests against the running
  API and real seeded data — not a pixel-level browser walkthrough (no browser-automation tool was
  available in this session). Do a manual click-through before shipping.

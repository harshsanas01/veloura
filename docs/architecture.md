# Architecture

Veloura is a **modular monolith**: one FastAPI service, one React SPA, one Postgres database.
There are no microservices, message queues, or background workers in the MVP — every request
is handled synchronously within the API process.

## High-level diagram

```
┌─────────────────┐      HTTPS/JSON       ┌──────────────────────┐      SQL/pgvector     ┌───────────────┐
│  React (Vite)    │ ───────────────────▶ │   FastAPI (Uvicorn)   │ ─────────────────────▶ │ Postgres (Neon)│
│  apps/web         │ ◀─────────────────── │   apps/api             │ ◀───────────────────── │  + pgvector    │
└─────────────────┘                       └──────────┬───────────┘                        └───────────────┘
                                                        │
                                                        │ HTTPS
                                                        ▼
                                                ┌───────────────┐
                                                │  OpenAI API    │
                                                │ (chat + embed) │
                                                └───────────────┘
```

The frontend never talks to Postgres or OpenAI directly — every data access and every AI call is
proxied through the FastAPI backend, so credentials never reach the browser.

## Backend layout (`apps/api/src/veloura_api`)

```
main.py            FastAPI app construction, middleware, router registration
config.py          Pydantic Settings (env vars)
database.py        SQLAlchemy engine/session, declarative Base
security.py        Password hashing (bcrypt) + JWT encode/decode
dependencies.py     FastAPI dependencies: DB session, current user, admin guard
middleware/         Request-ID + structured access logging
models/             SQLAlchemy ORM models (one file per aggregate)
schemas/            Pydantic request/response models
repositories/       Query logic - the only layer that talks to SQLAlchemy directly
services/           Business logic - orchestrates repositories, enforces rules
routes/             Thin HTTP layer - parses input, calls a service, returns a schema
ai/                 OpenAI client, preference extraction, retrieval, outfit generation
```

**Layering rule:** routes never touch the database directly, and never contain business logic.
A route parses the request into a schema, calls exactly one service method, and returns the
service's result. Services own transactions and business rules (inventory checks, pricing,
anti-hallucination validation). Repositories own SQLAlchemy queries. This keeps route handlers
easy to read and business logic easy to unit test without spinning up HTTP.

## Frontend layout (`apps/web/src`)

```
main.tsx / App.tsx   Router + React Query provider bootstrap
layouts/             Route-level shells (MainLayout, AccountLayout, AdminLayout)
pages/               One component per route, composed from smaller components
components/ui/       Design-system primitives (Button, Input, Modal, Drawer, ...)
components/product/  Product-specific building blocks (ProductCard, filters, selectors)
components/ai/       Chat message + outfit card for the AI stylist
components/admin/    Admin table + product form
services/            Typed Axios wrappers, one file per REST resource
hooks/                TanStack Query hooks built on top of services/
store/                Zustand stores: auth (token/user), UI (drawers), toasts
schemas/              Zod schemas for form validation
types/                Shared TypeScript types mirroring the backend's Pydantic schemas
```

State is split deliberately:
- **Server state** (products, cart, orders, AI sessions) lives in TanStack Query and is always
  fetched from the API - there is no separate client-side cache to keep in sync.
- **Client/UI state** (is the cart drawer open, the JWT, toast queue) lives in Zustand.

## AI stylist request flow

1. `POST /api/ai-stylist/recommend` receives the user's message and optional `session_id`.
2. `extract_preferences()` turns the message into a structured `StylePreferences` object, either
   via an OpenAI structured-output call (when `OPENAI_API_KEY` is set) or a deterministic
   keyword-based heuristic (when it isn't - see [ai.md limitations](../README.md#known-mvp-limitations)).
3. `get_candidate_products()` queries Postgres for **active, in-stock** products matching gender,
   category, price, and (if embeddings exist) pgvector cosine similarity to the request. This is
   the only source of products the model is allowed to see.
4. `generate_outfits()` sends the candidate list (and only the candidate list) to OpenAI with a
   system prompt instructing it to recommend exclusively from that list, using
   `client.beta.chat.completions.parse()` with a Pydantic `response_format` for structured output.
5. **Validation layer** (`_validate_and_price`) re-checks every returned `product_id`/`variant_id`
   against the candidate set before anything is persisted or returned. Anything not in the
   candidate set is silently dropped. Prices and totals are recomputed server-side from the
   database, never trusted from the model's output.
6. The chat session, messages, outfit, and outfit items are persisted, and the validated response
   is returned to the frontend.

This means a hallucinated product ID can never reach the browser: it would have to both be chosen
by the model *and* pass a database-backed membership check against real, in-stock inventory.

## Database

See the ER-ish summary below (full detail in the Alembic migration at
`apps/api/alembic/versions/`). All tables use UUID primary keys, `created_at`/`updated_at`
timestamps, and foreign keys with explicit `ondelete` behavior.

- `users`, `addresses` - identity and shipping
- `categories`, `products`, `product_variants` - catalog (products carry a `pgvector` `embedding`
  column for semantic search)
- `carts`, `cart_items`, `wishlists`, `wishlist_items` - pre-purchase state
- `orders`, `order_items` - immutable purchase records with a JSONB shipping-address snapshot
- `style_profiles`, `chat_sessions`, `chat_messages`, `outfits`, `outfit_items`,
  `recommendation_feedback` - AI stylist state

## Why a modular monolith

At MVP scale, a single deployable service is simpler to reason about, cheaper to run, and faster
to change than a set of microservices. The `repositories/services/routes` layering gives most of
the benefit of clean boundaries (testability, swappable persistence, clear ownership) without the
operational cost of network calls between services.

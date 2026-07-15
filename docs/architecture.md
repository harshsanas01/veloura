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
   keyword-based heuristic (when it isn't - see [known limitations](../README.md#known-limitations)).
3. `_apply_user_context()` fills in gaps the message didn't specify from the user's saved
   `style_profile` (preferred/disliked colors, budget, gender presentation, preferred brands) -
   never overriding something the user explicitly said in this message. If the message mentions
   "cart," it also resolves the user's most-recently-added cart item and sets it as an
   `anchor_product_id`, which both the retrieval scorer and outfit builder treat as a
   must-include item ("build an outfit around the jacket in my cart").
4. **Refinement check:** if this is a follow-up message in an existing session with a prior
   outfit, `detect_refinement()` looks for an explicit edit command (cheaper / more formal / more
   casual / change the color / replace the &lt;category&gt;). If one is found, `apply_refinement()`
   edits the *existing* outfit deterministically (swap the most expensive item for a cheaper
   same-category alternative, swap in a style-tag match, find an in-stock variant in the requested
   color, etc.) using only real candidate products, and the flow returns early — no LLM call is
   needed for a refinement, so this path is 100% reliable even without `OPENAI_API_KEY`.
5. Otherwise, `get_candidate_products()` queries Postgres for **active, in-stock** products
   matching gender, category, price, brand preference, and (if embeddings exist) pgvector cosine
   similarity to the request. This is the only source of products the model is allowed to see; if
   an anchor product exists but didn't match the filters, it's explicitly unioned in.
6. `generate_outfits()` sends the candidate list (and only the candidate list) to OpenAI with a
   system prompt instructing it to recommend exclusively from that list (and to include the anchor
   product if one is set), using `client.beta.chat.completions.parse()` with a Pydantic
   `response_format` for structured output. Without an API key, a deterministic heuristic
   (slot-aware, cheapest-first, anchor-first) builds the outfit instead.
7. **Validation layer** (`_validate_and_price`) re-checks every returned `product_id`/`variant_id`
   against the candidate set before anything is persisted or returned. Anything not in the
   candidate set is silently dropped. Prices and totals are recomputed server-side from the
   database, never trusted from the model's output.
8. The chat session, messages, outfit, and outfit items are persisted, and the validated response
   is returned to the frontend.

This means a hallucinated product ID can never reach the browser: it would have to both be chosen
by the model *and* pass a database-backed membership check against real, in-stock inventory.

## Coupon validation

`CouponService.validate()` is the single source of truth for whether a coupon applies and how
much it discounts — the frontend never computes a discount itself, only displays what
`GET /api/cart` or `POST /api/orders` returns. It checks, in order: active flag, start/expiry
window, global usage limit, per-user usage limit, minimum order value, then computes the eligible
subtotal (the whole cart, unless `applicable_categories`/`applicable_products` restrict it to
matching line items) and applies a fixed or percentage discount capped at `max_discount`. A
`free_shipping` flag on the coupon overrides the normal shipping-threshold calculation in
`services/pricing.py`. Redemptions are only recorded at checkout (`POST /api/orders`), never when
a coupon is merely previewed on the cart.

## Inventory transactions

Every stock change writes an immutable `InventoryTransaction` row (`order_placed`,
`order_cancelled`, `return`, or `admin_adjustment`, the last requiring a free-text reason) so
inventory levels can always be reconstructed and explained. Order creation locks each affected
`product_variants` row (`SELECT ... FOR UPDATE`) inside the same DB transaction as the decrement
and the order/order-item inserts, preventing overselling under concurrent checkouts. Cancellation
(customer-initiated, before shipping, or admin-initiated at any status) restores inventory the
same way.

## Recommendations

`RecommendationService` is deliberately SQL-only, not a machine-learning system:
- **Trending Now** ranks active products by units sold in the last 30 days (falls back to
  featured/newest if there isn't enough sales data yet, e.g. a fresh dev database).
- **Customers Also Bought** finds other products that appeared in the same orders as a given
  product, ranked by co-occurrence count (falls back to same-category related products).
- **Complete the Look** picks one product per complementary "body slot" (top/bottom/layer/
  footwear/accessory, the same mapping the AI stylist's heuristic generator uses) in the same
  gender, excluding the given product's own category/slot.

## Database

See the ER-ish summary below (full detail in the Alembic migrations at
`apps/api/alembic/versions/`). All tables use UUID primary keys, `created_at`/`updated_at`
timestamps, and foreign keys with explicit `ondelete` behavior.

- `users`, `addresses` - identity and shipping (separate default-shipping/default-billing flags)
- `categories`, `products`, `product_variants` - catalog (products carry a `pgvector` `embedding`
  column for semantic search)
- `carts`, `cart_items` (cart carries an optional `coupon_code`), `wishlists`, `wishlist_items` -
  pre-purchase state
- `orders`, `order_items` - immutable purchase records with a JSONB shipping-address snapshot,
  `discount_amount`/`coupon_code`/`customer_notes`
- `order_status_history` - append-only timeline of every status an order has passed through
- `inventory_transactions` - append-only audit log of every stock change
- `coupons`, `coupon_redemptions` - promotions and per-user/global redemption tracking
- `reviews`, `review_helpfulness` - one review per user per product, helpful-vote join table
- `style_profiles`, `chat_sessions`, `chat_messages`, `outfits`, `outfit_items`,
  `recommendation_feedback` - AI stylist state

## Why a modular monolith

At MVP scale, a single deployable service is simpler to reason about, cheaper to run, and faster
to change than a set of microservices. The `repositories/services/routes` layering gives most of
the benefit of clean boundaries (testability, swappable persistence, clear ownership) without the
operational cost of network calls between services.

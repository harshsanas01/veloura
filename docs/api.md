# API Reference

Base URL: `/api` (e.g. `http://localhost:8000/api` locally).

Interactive docs (Swagger UI) are available at `/docs` and ReDoc at `/redoc` whenever the API is
running - this file is a quick-reference summary, not the source of truth.

All authenticated endpoints expect `Authorization: Bearer <jwt>`. Admin endpoints additionally
require the authenticated user to have `role: admin`.

## Health

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/health` | none | Liveness/readiness check; also verifies DB connectivity. |

## Auth

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/auth/register` | none | Create an account, returns a JWT + user. |
| POST | `/auth/login` | none | Exchange email/password for a JWT + user. |
| GET | `/auth/me` | user | Returns the current authenticated user. |

## Categories & Products

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/categories` | none | List all categories. |
| GET | `/products` | none | Paginated, filterable product list. Query params: `q`, `gender`, `category` (repeatable), `size` (repeatable), `color` (repeatable), `min_price`, `max_price`, `sort` (`newest`\|`featured`\|`price_asc`\|`price_desc`\|`name_asc`), `page`, `page_size`. |
| GET | `/products/{slug}` | none | Full product detail with variants. |
| GET | `/products/{product_id}/related` | none | Related products (same category, falls back to same gender). |

## Cart

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/cart` | user | Get (or lazily create) the current user's cart. |
| POST | `/cart/items` | user | Add a variant to the cart. `409` if requested quantity exceeds stock. |
| PATCH | `/cart/items/{item_id}` | user | Update quantity. `409` if it exceeds stock. |
| DELETE | `/cart/items/{item_id}` | user | Remove an item. |

## Wishlist

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/wishlist` | user | List saved products. |
| POST | `/wishlist/items` | user | Save a product (idempotent). |
| DELETE | `/wishlist/items/{product_id}` | user | Remove a saved product. |

## Orders

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/orders` | user | Checkout the current cart. Locks each variant row, re-validates stock, decrements inventory, clears the cart, and returns the created order. `400` on an empty cart, `409` on insufficient inventory. |
| GET | `/orders` | user | List the current user's order history (summaries). |
| GET | `/orders/{order_id}` | user | Full order detail. `404` if it doesn't belong to the caller. |

Pricing: `shipping = $0 if subtotal >= $100 else $7.99`; `tax = subtotal * 8.25%`;
`total = subtotal + shipping + tax`.

## AI Stylist

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/ai-stylist/recommend` | user | Send a styling request (`message`, optional `session_id` to continue a conversation). Returns a summary, validated outfits with real product/variant data, and follow-up suggestions. |
| GET | `/ai-stylist/sessions` | user | List the current user's chat sessions. |
| GET | `/ai-stylist/sessions/{session_id}` | user | Full session detail: messages + generated outfits. |
| POST | `/ai-stylist/feedback` | user | Record like/dislike feedback on a generated outfit. |

See [architecture.md](architecture.md#ai-stylist-request-flow) for how candidate retrieval and
hallucination prevention work.

## Admin

All admin endpoints require `role: admin`.

| Method | Path | Description |
|---|---|---|
| GET | `/admin/products` | List every product, including inactive ones. |
| POST | `/admin/products` | Create a product, optionally with initial variants. |
| PATCH | `/admin/products/{product_id}` | Partial update (any subset of fields). |
| DELETE | `/admin/products/{product_id}` | Hard-delete a product (cascades to its variants). |
| POST | `/admin/products/{product_id}/variants` | Add a variant to an existing product. |
| PATCH | `/admin/variants/{variant_id}` | Update a variant (size, color, inventory, image). |
| GET | `/admin/orders` | List all orders across all customers. |
| PATCH | `/admin/orders/{order_id}/status` | Update fulfillment status (`pending`\|`paid`\|`processing`\|`shipped`\|`delivered`\|`cancelled`). |

## Error format

Errors return a JSON body of the form `{"detail": "human readable message"}` with a standard HTTP
status code (`400`, `401`, `403`, `404`, `409`, `422` for validation errors, `500` for unexpected
failures - unexpected failures never leak internal details).

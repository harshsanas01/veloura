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
| POST | `/auth/register` | none | Create an account (`first_name`, `last_name`, `email`, `password`, `confirm_password`). Enforces the password policy (8+ chars, upper/lower/number/special, not a common password, not equal to the email) and case-insensitive duplicate-email rejection. Returns a JWT + user. |
| POST | `/auth/login` | none | Exchange email/password for a JWT + user. Email is matched case-insensitively. |
| GET | `/auth/me` | user | Returns the current authenticated user. |

## Account

| Method | Path | Auth | Description |
|---|---|---|---|
| GET / PATCH | `/account/profile` | user | View or update first/last name and email (duplicate-checked). |
| POST | `/account/password` | user | Change password; requires the current password and enforces the same policy. |
| POST | `/account/delete` | user | Permanently delete the account; requires the current password and `confirm: true`. |
| GET / POST | `/account/addresses` | user | List / create saved addresses. `is_default_shipping` and `is_default_billing` are independent flags; setting either clears it from other addresses. |
| PATCH / DELETE | `/account/addresses/{id}` | user | Update or remove a saved address. |
| GET / PUT | `/account/style-profile` | user | View (auto-created on first read) or replace the user's style profile (gender presentation, preferred/disliked colors, preferred styles, favorite occasions, preferred brands, sizes, budget range). Used by the AI stylist to fill in gaps a chat message doesn't specify. |

## Categories & Products

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/categories` | none | List all categories. |
| GET | `/products` | none | Paginated, filterable product list. Query params: `q`, `gender`, `category`/`size`/`color`/`brand`/`material`/`occasion`/`season` (all repeatable), `min_price`, `max_price`, `in_stock_only`, `sale_only`, `sort` (`newest`\|`featured`\|`price_asc`\|`price_desc`\|`biggest_discount`\|`name_asc`), `page`, `page_size`. `q` matches name, brand, description, material, and tags, plus variant color. |
| GET | `/products/facets` | none | Distinct brands/materials/occasions/seasons and the current min/max price across the active catalog — powers the filter sidebar. |
| GET | `/products/{slug}` | none | Full product detail with variants. |
| GET | `/products/{product_id}/related` | none | Related products: same category + compatible gender first, then same gender any category, then same category any gender as a last resort — an opposite-gender item is never surfaced unless every gender-safe option is exhausted. |
| GET | `/products/{product_id}/also-bought` | none | "Customers Also Bought" — products frequently co-purchased with this one. |
| GET | `/products/{product_id}/complete-the-look` | none | One product per complementary category slot (top/bottom/layer/footwear/accessory), same gender. |
| GET | `/recommendations/trending` | none | "Trending Now" — products ranked by units sold in the last 30 days. Query params: `gender`, `limit`. |

## Reviews

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/products/{product_id}/reviews` | none | List reviews for a product. Query param `sort` (`newest`\|`highest`\|`lowest`\|`most_helpful`). Returns items, total, average rating, and a 1-5 star distribution. |
| POST | `/products/{product_id}/reviews` | user | Create a review (`rating` 1-5, `title`, `body`, optional `fit_feedback`, `size_purchased`). `409` if the user already reviewed this product. `is_verified_purchase` is set automatically based on non-cancelled order history. |
| PATCH / DELETE | `/reviews/{id}` | user | Edit or delete your own review. `404` if it isn't yours. |
| POST | `/reviews/{id}/helpful` | user | Toggle a helpful vote on a review. |

## Cart

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/cart` | user | Get (or lazily create) the current user's cart. Response includes server-computed `discount_amount`, `shipping_estimate`, `tax_estimate`, `estimated_total`, and `free_shipping_remaining`, plus the applied `coupon_code`/`coupon_error` if any. |
| POST | `/cart/items` | user | Add a variant to the cart. `409` if requested quantity exceeds stock. |
| PATCH | `/cart/items/{item_id}` | user | Update quantity. `409` if it exceeds stock. |
| DELETE | `/cart/items/{item_id}` | user | Remove an item. |
| POST | `/cart/items/{item_id}/move-to-wishlist` | user | Move an item from the cart to the wishlist. |
| POST | `/cart/coupon` | user | Validate and apply a coupon code to the cart (persisted on the cart, re-validated on every read). `400` with a human-readable reason if invalid. |
| DELETE | `/cart/coupon` | user | Remove the applied coupon. |

## Wishlist

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/wishlist` | user | List saved products, each with `on_sale`/`base_price`/`sale_price` for a sale badge. |
| POST | `/wishlist/items` | user | Save a product (idempotent). |
| DELETE | `/wishlist/items/{product_id}` | user | Remove a saved product. |
| POST | `/wishlist/items/{product_id}/move-to-cart` | user | Move a wishlist item to the cart; requires a `variant_id` (size/color) that belongs to the product. |

## Orders

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/orders` | user | Checkout the current cart. Optional `coupon_code` (defaults to the cart's applied coupon) and `customer_notes`. Locks each variant row, re-validates stock, decrements inventory, records an `inventory_transactions` row per line, records the coupon redemption (if any), clears the cart, and returns the created order with its initial status-history entry. `400` on an empty cart or invalid coupon, `409` on insufficient inventory. |
| GET | `/orders` | user | List the current user's order history (summaries). |
| GET | `/orders/{order_id}` | user | Full order detail: items, `status_history`, `can_cancel`, discount/coupon info. `404` if it doesn't belong to the caller. |
| POST | `/orders/{order_id}/cancel` | user | Cancel an order that hasn't shipped yet (`pending`/`paid`/`processing`); restores inventory transactionally and appends a status-history entry. `409` if it's already shipped/delivered/cancelled. |

Pricing (`services/pricing.py`): `discount` from an applied coupon is subtracted from the subtotal
first; `shipping = $0 if (subtotal - discount) >= $100 or the coupon grants free shipping, else
$7.99`; `tax = (subtotal - discount) * 8.25%`; `total = (subtotal - discount) + shipping + tax`.

## AI Stylist

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/ai-stylist/recommend` | user | Send a styling request (`message`, optional `session_id` to continue a conversation). Returns a summary, validated outfits with real product/variant data, and follow-up suggestions. Automatically merges the user's style profile and, if the message mentions "cart," anchors the outfit around their most-recently-added cart item. Follow-up messages like "make it cheaper" or "replace the shoes" are handled as deterministic edits to the previous outfit rather than a full regeneration. |
| GET | `/ai-stylist/sessions` | user | List the current user's chat sessions. |
| GET | `/ai-stylist/sessions/{session_id}` | user | Full session detail: messages + generated outfits. |
| POST | `/ai-stylist/feedback` | user | Record like/dislike feedback on a generated outfit. |

See [architecture.md](architecture.md#ai-stylist-request-flow) for how candidate retrieval,
refinement, and hallucination prevention work.

## Admin

All admin endpoints require `role: admin`.

| Method | Path | Description |
|---|---|---|
| GET | `/admin/dashboard` | Revenue, order/customer counts, average order value, low-stock/out-of-stock variant counts, best-selling products, recent orders, top categories by revenue. |
| GET | `/admin/products` | Paginated, searchable (`q` matches name/brand) product list, including inactive products. |
| POST | `/admin/products` | Create a product, optionally with initial variants. |
| PATCH | `/admin/products/{product_id}` | Partial update (any subset of fields, including `is_featured`/`is_active`). |
| DELETE | `/admin/products/{product_id}` | Hard-delete a product (cascades to its variants). |
| POST | `/admin/products/{product_id}/variants` | Add a variant to an existing product. |
| PATCH | `/admin/variants/{variant_id}` | Update a variant (size, color, inventory, image). |
| DELETE | `/admin/variants/{variant_id}` | Delete a variant. |
| POST | `/admin/variants/{variant_id}/adjust-inventory` | Manually adjust stock by a signed `delta` with a required `reason`; records an `admin_adjustment` inventory transaction. `400` if it would go negative. |
| GET | `/admin/orders` | Paginated, searchable (`q` matches order number/customer email, `order_status` filter) list of all orders. |
| PATCH | `/admin/orders/{order_id}/status` | Update fulfillment status (`pending`\|`paid`\|`processing`\|`shipped`\|`delivered`\|`cancelled`\|`returned`), optional `note`. Transitioning into `cancelled`/`returned` restores inventory transactionally. |
| GET | `/admin/customers` | Paginated, searchable list of accounts with order count and lifetime spend. |
| GET / POST | `/admin/coupons` | List all coupons, or create one. |
| PATCH / DELETE | `/admin/coupons/{id}` | Update or delete a coupon. |
| GET | `/admin/reviews` | List every review (including hidden ones). |
| PATCH | `/admin/reviews/{id}` | Moderate a review (`is_active: false` hides it from the public listing). |

## Error format

Errors return a JSON body of the form `{"detail": "human readable message"}` with a standard HTTP
status code (`400`, `401`, `403`, `404`, `409`, `422` for validation errors, `500` for unexpected
failures - unexpected failures never leak internal details).

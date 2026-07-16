"""Safe reseed for the seed-owned product catalog.

`make reseed-products` runs this with no flags, which is always non-destructive:

  1. validates the image manifest (scripts/validate_seed_images.py) and aborts
     before touching the database if it fails;
  2. re-runs the product seed, which refreshes seed-owned products' variant
     images in place from scripts/data/product_images.json (healing catalogs
     created before every product had a unique image), creates any missing
     seed products, and deactivates superseded seed rows;
  3. reports how many products would be purged and how many new products still
     need embeddings (run `make generate-embeddings` to backfill - product
     descriptions are unchanged by an image refresh, so existing embeddings
     stay valid).

Registered users, authentication data, addresses, carts, wishlists, orders,
and admin-created products are never touched.

The only destructive step - actually DELETING inactive, seed-owned products -
requires the explicit opt-in `--purge --confirm`:

  - only products whose brand is a known Veloura seed brand are eligible
    (KNOWN_SEED_BRANDS in seed_products.py); admin-created products never are;
  - only products already deactivated by the seed (i.e. superseded) qualify;
  - products referenced by an order_item are protected at the database level
    (ON DELETE RESTRICT on order_items.variant_id) and are skipped with a
    warning rather than breaking order history.

Usage:
    python scripts/reseed_products.py                    # safe reseed
    python scripts/reseed_products.py --purge            # + dry-run purge report
    python scripts/reseed_products.py --purge --confirm  # + actually delete
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps/api/src"))

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from veloura_api.database import SessionLocal
from veloura_api.models.product import Product

import seed_products  # noqa: E402
from validate_seed_images import validate as validate_manifest  # noqa: E402


def purge_inactive_seed_products(db: Session, confirm: bool) -> None:
    candidates = list(
        db.scalars(
            select(Product).where(
                Product.brand.in_(seed_products.KNOWN_SEED_BRANDS),
                Product.is_active.is_(False),
            )
        )
    )
    if not candidates:
        print("Nothing to purge - no inactive seed-owned products found.")
        return

    print(f"Found {len(candidates)} inactive seed-owned product(s) eligible for deletion.")
    if not confirm:
        for p in candidates[:20]:
            print(f"  - would delete: {p.brand} / {p.name} ({p.gender.value})")
        if len(candidates) > 20:
            print(f"  ... and {len(candidates) - 20} more.")
        print("\nWARNING: deletion is permanent. Re-run with --purge --confirm to proceed.")
        return

    deleted, skipped = 0, 0
    for product in candidates:
        try:
            db.delete(product)
            db.flush()
            deleted += 1
        except IntegrityError:
            db.rollback()
            skipped += 1
    db.commit()
    print(f"Deleted {deleted} product(s).")
    if skipped:
        print(
            f"Skipped {skipped} product(s) still referenced by existing order history "
            "(protected by ON DELETE RESTRICT)."
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--purge",
        action="store_true",
        help="Also report (or with --confirm, delete) inactive seed-owned products.",
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Required together with --purge to actually delete rows.",
    )
    args = parser.parse_args()

    print("Validating seed image manifest before touching the database...")
    errors = validate_manifest()
    if errors:
        print(f"Manifest validation FAILED with {len(errors)} error(s); aborting reseed:")
        for err in errors:
            print(f"  - {err}")
        raise SystemExit(1)
    print("  -> manifest OK: every seeded product gets a unique, gender/category-matched image.\n")

    db = SessionLocal()
    try:
        print("Reseeding products (users, carts, wishlists, and orders are preserved)...")
        products = seed_products.seed_products(db)
        print(f"  -> {len(products)} products in catalog.")

        missing_embeddings = db.scalar(
            select(Product.id).where(Product.embedding.is_(None), Product.is_active.is_(True))
        )
        if missing_embeddings:
            print("Some active products have no embedding yet - run `make generate-embeddings`.")

        purge_inactive_seed_products(db, confirm=args.purge and args.confirm)
    finally:
        db.close()

    print("Reseed complete.")


if __name__ == "__main__":
    main()

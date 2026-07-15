"""Explicit, destructive cleanup for seed-owned catalog data.

`make seed` (scripts/seed_products.py) is always safe to re-run: it only adds
missing rows and *deactivates* (never deletes) products from an older
generation of the script. This script is the opt-in follow-up that actually
DELETES those deactivated, seed-owned rows once you're sure you don't need
them - e.g. to shrink a dev database after a large catalog rewrite.

Safety rules:
  - Only ever touches products whose brand is a known Veloura seed brand
    (KNOWN_SEED_BRANDS in seed_products.py) - real admin-created products are
    never touched.
  - Only ever touches products that are already inactive (i.e. already
    superseded by scripts/seed_products.py).
  - Products referenced by an existing order_item are protected at the
    database level (ON DELETE RESTRICT on order_items.variant_id) and will be
    skipped with a warning rather than breaking order history.
  - Real users, their addresses, carts, wishlists, and orders are never
    touched by this script.

Usage:
    python scripts/reseed_products.py --confirm
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps/api/src"))

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from veloura_api.database import SessionLocal
from veloura_api.models.product import Product

from seed_products import KNOWN_SEED_BRANDS  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Required. Without this flag the script only reports what it would delete.",
    )
    args = parser.parse_args()

    db = SessionLocal()
    try:
        candidates = list(
            db.scalars(
                select(Product).where(
                    Product.brand.in_(KNOWN_SEED_BRANDS),
                    Product.is_active.is_(False),
                )
            )
        )
        if not candidates:
            print("Nothing to purge - no inactive seed-owned products found.")
            return

        print(f"Found {len(candidates)} inactive seed-owned product(s) eligible for deletion.")
        if not args.confirm:
            for p in candidates[:20]:
                print(f"  - would delete: {p.brand} / {p.name} ({p.gender.value})")
            if len(candidates) > 20:
                print(f"  ... and {len(candidates) - 20} more.")
            print("\nRe-run with --confirm to actually delete these rows.")
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
    finally:
        db.close()


if __name__ == "__main__":
    main()

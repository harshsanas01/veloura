"""Static validation for the seed image manifest and its product assignment.

Runs entirely offline (no database, no network) so it can gate CI and every
reseed. Checks, in order:

  1. manifest hygiene   - unique URLs, unique source_ids, no empty URLs, only
                          static images.unsplash.com CDN URLs (dynamic /
                          keyword endpoints like source.unsplash.com are
                          rejected), known genders and categories.
  2. gender rules       - women-only categories (Dresses, Skirts) carry only
                          women-tagged imagery; `unisex` images exist only for
                          categories that seed unisex products.
  3. coverage           - every (gender, category) pool in the manifest is at
                          least as large as the number of products the seed
                          will create for it.
  4. assignment         - building the full seed catalog in memory yields one
                          unique primary image per product, matched to the
                          product's gender and category, with no product left
                          imageless and variants sharing their product's image.

Usage:
    python scripts/validate_seed_images.py      (or `make validate-seed-images`)

Exits 0 when everything passes, 1 with a list of failures otherwise.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from seed_products import (  # noqa: E402
    CATEGORY_COUNTS,
    CATEGORY_NAMES,
    IMAGE_MANIFEST_PATH,
    UNISEX_ACCESSORY_COUNT,
    build_products,
)

STATIC_URL_PATTERN = re.compile(r"^https://images\.unsplash\.com/photo-\d{10,13}-[0-9a-f]+\?")
DYNAMIC_URL_MARKERS = ("source.unsplash.com", "picsum.photos", "/random", "loremflickr")
VALID_GENDERS = {"men", "women", "unisex"}
WOMEN_ONLY_CATEGORIES = {"Dresses", "Skirts"}


def validate() -> list[str]:
    errors: list[str] = []
    manifest = json.loads(IMAGE_MANIFEST_PATH.read_text())
    images = manifest["images"]

    # 1. manifest hygiene
    urls = [e["url"] for e in images]
    source_ids = [e["source_id"] for e in images]
    if len(urls) != len(set(urls)):
        dupes = {u for u in urls if urls.count(u) > 1}
        errors.append(f"duplicate manifest URLs: {sorted(dupes)[:5]}")
    if len(source_ids) != len(set(source_ids)):
        dupes = {s for s in source_ids if source_ids.count(s) > 1}
        errors.append(f"duplicate manifest source_ids: {sorted(dupes)[:5]}")
    valid_categories = set(CATEGORY_NAMES.values())
    for e in images:
        label = e.get("source_id", "<missing source_id>")
        if not e.get("url"):
            errors.append(f"{label}: empty url")
            continue
        if any(marker in e["url"] for marker in DYNAMIC_URL_MARKERS):
            errors.append(f"{label}: dynamic/random image endpoint is not allowed: {e['url']}")
        elif not STATIC_URL_PATTERN.match(e["url"]):
            errors.append(f"{label}: not a static Unsplash CDN URL: {e['url']}")
        if e.get("gender") not in VALID_GENDERS:
            errors.append(f"{label}: unknown gender {e.get('gender')!r}")
        if e.get("category") not in valid_categories:
            errors.append(f"{label}: unknown category {e.get('category')!r}")

    # 2. gender rules
    for e in images:
        if e["category"] in WOMEN_ONLY_CATEGORIES and e["gender"] != "women":
            errors.append(f"{e['source_id']}: {e['category']} imagery must be women-tagged")
        if e["gender"] == "unisex" and e["category"] != "Accessories":
            errors.append(f"{e['source_id']}: only Accessories seed unisex products")

    # 3. coverage per (gender, category)
    pool_sizes: dict[tuple[str, str], int] = {}
    for e in images:
        key = (e["gender"], e["category"])
        pool_sizes[key] = pool_sizes.get(key, 0) + 1
    required: dict[tuple[str, str], int] = {
        (gender, CATEGORY_NAMES[slug]): count
        for slug, gender_counts in CATEGORY_COUNTS.items()
        for gender, count in gender_counts.items()
    }
    required[("unisex", "Accessories")] = UNISEX_ACCESSORY_COUNT
    for key, need in sorted(required.items()):
        have = pool_sizes.get(key, 0)
        if have < need:
            errors.append(f"pool {key}: {have} image(s) for {need} product(s)")

    # 4. assignment over the full in-memory catalog
    try:
        products = build_products()
    except (RuntimeError, AssertionError) as exc:
        errors.append(f"building seed catalog failed: {exc}")
        return errors

    by_source = {e["source_id"]: e for e in images}
    primary_urls: list[str] = []
    for p in products:
        if not p["variants"]:
            errors.append(f"{p['name']} ({p['gender']}): no variants/images")
            continue
        primary = p["variants"][0]["image_url"]
        if not primary:
            errors.append(f"{p['name']} ({p['gender']}): empty primary image URL")
        primary_urls.append(primary)
        entry = by_source.get(p["image_source_id"])
        if entry is None:
            errors.append(f"{p['name']}: assigned unknown source {p['image_source_id']}")
            continue
        if entry["gender"] != p["gender"]:
            errors.append(
                f"{p['name']}: {p['gender']} product got {entry['gender']} image {entry['source_id']}"
            )
        if entry["category"] != p["category_name"]:
            errors.append(
                f"{p['name']}: {p['category_name']} product got {entry['category']} image {entry['source_id']}"
            )
        if {v["image_url"] for v in p["variants"]} != {primary}:
            errors.append(f"{p['name']}: variants do not share the product's image")

    assert len(primary_urls) == len(products) or errors
    if len(primary_urls) != len(set(primary_urls)):
        dupes = {u for u in primary_urls if primary_urls.count(u) > 1}
        errors.append(f"duplicate primary images across products: {sorted(dupes)[:5]}")

    return errors


def main() -> None:
    errors = validate()
    manifest_count = len(json.loads(IMAGE_MANIFEST_PATH.read_text())["images"])
    if errors:
        print(f"Seed image validation FAILED with {len(errors)} error(s):")
        for err in errors:
            print(f"  - {err}")
        raise SystemExit(1)
    print(f"Seed image validation passed: {manifest_count} unique manifest images, "
          "one unique primary image per seeded product, all gender/category-matched.")


if __name__ == "__main__":
    main()

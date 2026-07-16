"""Seed image guarantees: no two seeded products may share a primary image.

These tests exercise the seed scripts' in-memory catalog builder and the image
manifest directly - no database or network access - so they run in the normal
test suite and catch a regression before it ever reaches a reseed.
"""

import json
import re
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[2].parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from seed_products import (  # noqa: E402
    CATEGORY_COUNTS,
    CATEGORY_NAMES,
    IMAGE_MANIFEST_PATH,
    UNISEX_ACCESSORY_COUNT,
    build_products,
)
from validate_seed_images import validate as validate_manifest  # noqa: E402


@pytest.fixture(scope="module")
def manifest_images() -> list[dict]:
    return json.loads(IMAGE_MANIFEST_PATH.read_text())["images"]


@pytest.fixture(scope="module")
def products() -> list[dict]:
    return build_products()


def test_manifest_urls_and_source_ids_are_unique(manifest_images):
    urls = [e["url"] for e in manifest_images]
    assert len(urls) == len(set(urls))
    source_ids = [e["source_id"] for e in manifest_images]
    assert len(source_ids) == len(set(source_ids))


def test_manifest_urls_are_static_cdn_urls(manifest_images):
    static = re.compile(r"^https://images\.unsplash\.com/photo-\d{10,13}-[0-9a-f]+\?")
    for e in manifest_images:
        assert e["url"], f"{e['source_id']}: empty url"
        assert "source.unsplash.com" not in e["url"]
        assert static.match(e["url"]), f"{e['source_id']}: dynamic or malformed url {e['url']}"


def test_manifest_covers_every_seeded_pool(manifest_images):
    pool_sizes: dict[tuple[str, str], int] = {}
    for e in manifest_images:
        key = (e["gender"], e["category"])
        pool_sizes[key] = pool_sizes.get(key, 0) + 1
    for slug, gender_counts in CATEGORY_COUNTS.items():
        for gender, count in gender_counts.items():
            key = (gender, CATEGORY_NAMES[slug])
            assert pool_sizes.get(key, 0) >= count, f"pool {key} too small"
    assert pool_sizes.get(("unisex", "Accessories"), 0) >= UNISEX_ACCESSORY_COUNT


def test_women_only_categories_use_women_imagery(manifest_images):
    for e in manifest_images:
        if e["category"] in ("Dresses", "Skirts"):
            assert e["gender"] == "women", e["source_id"]


def test_every_product_gets_a_unique_primary_image(products):
    primary_urls = [p["variants"][0]["image_url"] for p in products]
    assert all(primary_urls), "a seeded product has an empty primary image"
    assert len(primary_urls) == len(set(primary_urls)), "primary images are reused across products"
    source_ids = [p["image_source_id"] for p in products]
    assert len(source_ids) == len(set(source_ids)), "image source_ids are reused across products"


def test_variants_share_their_products_single_image(products):
    for p in products:
        urls = {v["image_url"] for v in p["variants"]}
        assert len(urls) == 1, f"{p['name']}: variants drifted onto different images"


def test_assigned_images_match_product_gender_and_category(products, manifest_images):
    by_source = {e["source_id"]: e for e in manifest_images}
    for p in products:
        entry = by_source[p["image_source_id"]]
        assert entry["gender"] == p["gender"], p["name"]
        assert entry["category"] == p["category_name"], p["name"]


def test_full_validation_script_passes():
    assert validate_manifest() == []

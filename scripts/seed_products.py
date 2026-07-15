"""Idempotent seed script for Veloura.

Builds a realistic, gender-correct catalog of 600+ products across 15 categories,
each with multiple size/color variants, verified gender-appropriate photography,
an admin account, a sample customer account, a couple of sample orders, and a
couple of saved outfits.

Safe to run multiple times - existing rows (matched by slug/email/order number)
are left untouched. Also deactivates (never deletes) any product left over from
an older, narrower generation of this script so the storefront only shows the
current catalog; see scripts/reseed_products.py to actually purge those rows.

Usage (from apps/api's virtualenv, repo root as cwd):
    python scripts/seed_products.py
"""

from __future__ import annotations

import itertools
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps/api/src"))

import random

from sqlalchemy import select
from sqlalchemy.orm import Session
from veloura_api.database import SessionLocal
from veloura_api.models.address import Address
from veloura_api.models.cart import Cart
from veloura_api.models.category import Category
from veloura_api.models.coupon import Coupon, DiscountType
from veloura_api.models.order import Order, OrderItem, OrderStatus
from veloura_api.models.outfit import Outfit, OutfitItem
from veloura_api.models.product import Gender, Product, ProductVariant
from veloura_api.models.user import User, UserRole
from veloura_api.models.wishlist import Wishlist
from veloura_api.security import hash_password
from veloura_api.services.pricing import calculate_order_totals
from veloura_api.utils import slugify

random.seed(42)

CLOTHING_SIZES = ["XS", "S", "M", "L", "XL", "XXL"]
SHOE_SIZES = ["7", "8", "9", "10", "11", "12"]
ONE_SIZE = ["One Size"]

COLORS = [
    ("Black", "#111111"), ("White", "#FAFAFA"), ("Ivory", "#F1E9D2"), ("Navy", "#1B2A4A"),
    ("Burgundy", "#6E1835"), ("Olive", "#5C6B4A"), ("Camel", "#C19A6B"), ("Charcoal", "#36454F"),
    ("Sage", "#9CAF88"), ("Blush", "#E8C4C4"), ("Denim Blue", "#4A6FA5"), ("Rust", "#B5541A"),
    ("Grey", "#9A9A9A"), ("Cream", "#F5EFE6"), ("Red", "#B33A3A"), ("Forest Green", "#2F4A3C"),
    ("Tan", "#D2B48C"), ("Chocolate", "#4B3221"),
]

# ---------------------------------------------------------------------------
# Brands - fictional Veloura house brands with a consistent identity and price
# tier. KNOWN_SEED_BRANDS lets reseed tooling recognize (and only ever touch)
# catalog rows this script owns, never a real admin-created product.
# ---------------------------------------------------------------------------
BRANDS: dict[str, tuple[str, float]] = {
    "Maison Aster": ("premium minimalist", 1.25),
    "Linden & Co": ("premium minimalist", 1.15),
    "Calder Row": ("contemporary basics", 1.0),
    "Union Thread": ("contemporary basics", 0.95),
    "North & Ash": ("streetwear", 1.05),
    "Kestrel & Vine": ("streetwear", 0.9),
    "Solstice Denim": ("streetwear", 1.0),
    "Ferro Athletics": ("activewear", 1.0),
    "Marchetti": ("formalwear", 1.4),
    "Grayson Field": ("formalwear", 1.3),
    "Etta Moreau": ("resort wear", 1.1),
    "Nomade Atelier": ("resort wear", 1.05),
    "Birch & Bloom": ("sustainable fashion", 1.1),
    "Amaranth Studio": ("sustainable fashion", 1.15),
    "Veloura Studio": ("premium minimalist", 1.2),
}
KNOWN_SEED_BRANDS = set(BRANDS) | {"Ferro Leather", "Aubrey Lane"}  # incl. retired names

CATEGORY_BRAND_AFFINITY: dict[str, list[str]] = {
    "tshirts": ["Calder Row", "Union Thread", "North & Ash", "Birch & Bloom", "Veloura Studio"],
    "shirts": ["Maison Aster", "Linden & Co", "Marchetti", "Calder Row", "Grayson Field"],
    "hoodies": ["North & Ash", "Kestrel & Vine", "Solstice Denim", "Ferro Athletics"],
    "sweaters": ["Maison Aster", "Linden & Co", "Etta Moreau", "Birch & Bloom", "Veloura Studio"],
    "jackets": ["Solstice Denim", "North & Ash", "Kestrel & Vine", "Grayson Field", "Marchetti"],
    "coats": ["Marchetti", "Grayson Field", "Maison Aster", "Linden & Co"],
    "jeans": ["Solstice Denim", "Union Thread", "Calder Row"],
    "trousers": ["Marchetti", "Grayson Field", "Maison Aster", "Calder Row"],
    "shorts": ["Nomade Atelier", "Etta Moreau", "Union Thread", "Ferro Athletics"],
    "activewear": ["Ferro Athletics", "North & Ash", "Kestrel & Vine"],
    "swimwear": ["Nomade Atelier", "Etta Moreau"],
    "shoes": ["Veloura Studio", "North & Ash", "Marchetti", "Ferro Athletics"],
    "accessories": ["Veloura Studio", "Maison Aster", "Amaranth Studio", "Grayson Field"],
    "dresses": ["Maison Aster", "Etta Moreau", "Nomade Atelier", "Amaranth Studio", "Veloura Studio"],
    "skirts": ["Maison Aster", "Etta Moreau", "Amaranth Studio", "Calder Row"],
}

# ---------------------------------------------------------------------------
# Image bank - every ID below was pulled from a live Unsplash search result and
# gender/category-verified against its alt text before being added here, so
# women's collections only ever draw from women-verified photography and vice
# versa. IDs are grouped by (gender, category) for maintainability; formal
# menswear and extra women's knitwear pools are folded into their parent
# category below rather than becoming new top-level categories.
# ---------------------------------------------------------------------------
IMAGE_IDS: dict[tuple[str, str], list[str]] = {
    ("men", "tshirts"): [
        "1594672830234-ba4cfe1202dc", "1600603405959-6d623e92445c", "1614492683088-fbcce7d6704b", "1622377036957-4db3d2eda1a9",
        "1619604736012-58e35a563c70", "1628737490381-117c818d1ad7", "1636573563592-e9fb5bfed7ab", "1544048242-7e7ea1a1ebc2",
        "1592994238317-fcf75c5466fd", "1585336845746-8529411a57b6",
    ],
    ("women", "tshirts"): [
        "1610142991820-e02266a4a9f0", "1604342681413-6954ddca1e6f", "1610143955896-950eb5ce3790", "1593990110200-382c1a6df0ba",
        "1567181389426-28c6c17023d4", "1567181389126-5719e166d301", "1567181389445-5ca881affb77", "1567181445486-b134d37e3732",
        "1567181389434-eaf04685157c", "1567181445475-f481ca72b92d",
    ],
    ("men", "shirts"): [
        "1627686011747-74adda3d2343", "1629871870289-21efd577d820", "1761554169700-131bc3f188c3", "1761554169693-08fd975a94f8",
        "1660558455285-41b611bfb55f", "1761980958548-7babac83ef3d", "1776435303294-ae487c8c28a5", "1783899557548-72f4f8476a2f",
        "1776435303185-95be02310cff", "1763610452393-df10441c5f5d", "1761956260682-fe12109d7878",
    ],
    ("women", "shirts"): [
        "1542354531-f58491488981", "1618836067320-23bbf461df71", "1564689800749-3499d2eaa8d8", "1585473440041-0a914e4998e3",
        "1544005313-94ddf0286df2", "1470092922729-762ec45090ac", "1645389775404-3d425a17fb2b", "1597308680537-1ba44407ffc0",
        "1597308680499-b0711e0a3387", "1780488704750-5092dabdc266", "1599746146388-a7ec2004b67a",
    ],
    ("men", "hoodies"): [
        "1564557287817-3785e38ec1f5", "1596075780750-81249df16d19", "1611817757591-c3f345024273", "1554967769-1f961137e9c1",
        "1617171594207-430a01a9da3f", "1580079906050-84bb132e4c4f", "1632682582909-2b3a2581eef7", "1574948082432-ef3fc11f0f36",
        "1632073143817-8cd5b2165e20",
    ],
    ("women", "hoodies"): [
        "1508216310976-c518daae0cdc", "1526476148966-98bd039463ea", "1618924250456-0c7d405f2d53", "1578470507807-3fc541d5f544",
        "1596404129310-1ba3abeaed1e", "1577597759406-0bd867a7c07f", "1594656375376-64d56e2f3ed1", "1771685456416-3af8b8fafe7d",
        "1714730452043-279528959d56",
    ],
    ("men", "sweaters"): [
        "1608975321561-176c1b187d24", "1586020780197-b3daebd5aaa8", "1556807215-f47c31a66ac2", "1675746794758-1931890b4b45",
        "1692529487714-4e938cc6322f", "1642886512785-b5fee9faad7f", "1642886512782-937cd45bdf64", "1603691160249-7d224e090032",
    ],
    ("women", "sweaters"): [
        "1580331451062-99ff652288d7", "1587999882859-34b3f313df77", "1623092894838-4041d7acea13", "1637325261615-2966096e5366",
        "1576574273295-fec3463e112f", "1627901841291-981a5468232d", "1612872513575-7e7666b96ff3", "1622418131139-8549767c2670",
        "1553820691-51b6aa80cb7d", "1732136647953-c884a9af68d7", "1613353948391-9822c7407534", "1622925492162-98c3760a7080",
        "1613117943919-d743b983c89b", "1608893954403-6752097b5997", "1584658556169-5e2eeb66e5ab",
    ],
    ("men", "jackets"): [
        "1614208242226-6a145842a8c8", "1583158921495-5b935d960cde", "1590789188781-4c90c12f0f0b", "1619961310705-963c5356173d",
        "1617973773420-2b53c62bb64e", "1614699745279-2c61bd9d46b5", "1614693348454-1e0710d21c60", "1620834767726-61b1986287ff",
        "1614697688184-66a55d41e298", "1776054597118-eac1f833445a", "1768862211215-2c205a01e5b6", "1617127365659-c47fa864d8bc",
        "1630667208073-82d53b1db540", "1555097074-b16ec85d6b3e", "1543132220-4bf3de6e10ae", "1519085360753-af0119f7cbe7",
        "1586232902955-df204f34b36e", "1613379171002-3610ae01cf4a",
    ],
    ("women", "jackets"): [
        "1684262855364-f3ca7786c734", "1696489283182-0446be970e40", "1611232659353-97d990dd6d52", "1581274915427-76bfa7451b07",
        "1587155471946-9e8d4d1132fa", "1588371995259-c69a24964e5d", "1615233500570-c5d7576b4262", "1615397815341-bb06f6d55c94",
        "1745450071838-429aabbb9847", "1736754074555-54b6abcb2fb4",
    ],
    ("men", "coats"): [
        "1619603364937-8d7af41ef206", "1619603364904-c0498317e145", "1619208382871-96f4d45bc840", "1642886513052-d24b4f4745ea",
        "1617137977259-bb83e191f377", "1620577543518-6324d64406a3", "1638109879135-285a7b8b5924", "1644705128443-9ef786c6ffb1",
    ],
    ("women", "coats"): [
        "1541823709867-1b206113eafd", "1617391258031-f8d80b22fb35", "1640557443065-cd2b7ed858d6", "1618244985759-a8a1dc26bce3",
        "1618244965061-1d27b208d6e8", "1589400445193-c881a4b0b38a", "1678700266327-8959be9622fd", "1617639432216-592107059584",
        "1621786040662-455f23dcb6ff", "1621786037709-6c700b14ea75", "1585215173785-7f3c2252c25a", "1700748911489-0552c576f274",
        "1592423788390-2e71e064f724",
    ],
    ("men", "jeans"): [
        "1617114919297-3c8ddb01f599", "1555689502-c4b22d76c56f", "1511196044526-5cb3bcb7071b", "1674075872359-a174bc7ed420",
        "1613053342567-924891457d16", "1616002851413-ebcc9611139d", "1552252059-9d77e4059ad1", "1620228922597-cca58f177310",
        "1765449582468-1f9d941bc80d", "1762317086188-2b3763b0a041",
    ],
    ("women", "jeans"): [
        "1578693082747-50c396cacd81", "1592595293637-8557fa6d3c64", "1616003471864-9abfeee24576", "1760551600405-54c70e6d7f42",
        "1760551732366-94884b88301e", "1762343949052-c086a93fceac", "1762343941081-4b18ad4457cf", "1762343944518-bb23beeaaa8b",
        "1760551733107-25bd7b041623", "1782116674797-8d00c36ffa7f", "1779398741066-be658c5191a8",
    ],
    ("men", "trousers"): [
        "1584865288642-42078afe6942", "1615538363919-8e5724f16d20", "1636452147682-e624f9fc70c4", "1775831726936-c8fb3698645f",
        "1670855822901-5786604e9c40", "1775831726875-e3ca6f3ed2f8", "1735653193631-fd8ec61ff9db", "1742319692068-f63de5b5d4b0",
        "1618886614638-80e3c103d31a", "1617113930975-f9c7243ae527", "1546572797-e8c933a75a1f", "1642886513531-5a1cf3ba164a",
        "1748950413337-5cfdb6b59321", "1688120243155-1ffc1f965343", "1611095006346-d5e3313245e1", "1594760136382-0c07cc163715",
        "1675887924656-4f6df9eccc14",
    ],
    ("women", "trousers"): [
        "1551854838-212c50b4c184", "1580651214613-f4692d6d138f", "1584273143981-41c073dfe8f8", "1624468470821-04cfd6c26097",
        "1673180585720-ec0fc25f1d83", "1673180608353-63292b332e84", "1638396637969-956ca903df87", "1751399566412-ad1194241c5c",
        "1774850235906-f5eaafb425ac", "1774850236254-f0aa024ca20c", "1604914509756-14d03c38140f", "1626878561212-f383a914d99c",
    ],
    ("men", "shorts"): [
        "1621496503717-095a410e1566", "1771710974003-36707a93f37a", "1697319452360-ee47502e39f6", "1580821342431-85168be7339b",
        "1780336673884-051e7117261e", "1761638074635-2b1f0629dbb3", "1759495381816-9d0c04b018a3", "1658874761235-8d56cbd5da2d",
    ],
    ("women", "shorts"): [
        "1585145197082-dba095ba01ab", "1585145197502-8f36802f0a26", "1762423492557-f6014c4f1de7", "1759476531403-b1f88092f992",
        "1475180098004-ca77a66827be", "1760551600460-018b52b28045", "1630280718424-2e8b76fa4252", "1621991491674-45d3b168f40c",
        "1621991490432-d331e9ba7de9", "1527280916202-fa1f7c499a7c",
    ],
    ("men", "activewear"): [
        "1603698819488-03c6e857d280", "1614367674345-f414b2be3e5b", "1600878585887-c2b9530999a1", "1765045768265-e3eb8471fce3",
        "1575898311302-0d04de38c259", "1579758682665-53a1a614eea6", "1736264334806-b50e5ec94be1", "1704223523409-016ec3b5779f",
    ],
    ("women", "activewear"): [
        "1606902965551-dce093cda6e7", "1584863495140-a320b13a11a8", "1645810798586-08e892108d67", "1768929035644-6e146b35acd8",
        "1770026137084-bc03cad73eaf", "1768929096117-c0b04a7c8fc2", "1768929096134-f45af7839e83", "1769196716871-39a0712fb037",
        "1781191063125-5595e4e960a5",
    ],
    ("men", "swimwear"): [
        "1713349542236-30f2f7d609df", "1750879051935-4fd398c5305a", "1652025106075-ffa043d2e5d1", "1750879051867-f9825c669b32",
        "1713349542195-66353835bd69", "1652660538905-4e0e45b730aa", "1644197426647-cdc744c44048", "1663156650017-c4d7ec2d7f4d",
        "1781754053347-af4594f67a83",
    ],
    ("women", "swimwear"): [
        "1542427361-4388a46a654a", "1555617135-8724b69f766c", "1548272943-cdb9d56506f5", "1571348635303-dabc89cff3be",
        "1642472193131-add8b4bdab75", "1611274722079-920354116cbe",
    ],
    ("men", "shoes"): [
        "1706890741880-bfe6db87b326", "1577646162880-4fa9f2363036", "1521144236085-322e24bfa95a", "1642978599217-287d0345389d",
        "1560073742-bc295f81c3c0", "1559166631-ef208440c75a", "1590668228857-748e3dc9a519",
    ],
    ("women", "shoes"): [
        "1673182122218-c63ff9007fc8", "1550919559-2256f4b083a4", "1590972381247-0f65243c8192", "1677680128251-58bc3b25f9ec",
    ],
    ("men", "accessories"): [
        "1614252369475-531eba835eb1", "1782171059919-6719ba1488f7", "1768766916110-d25e72ffafc2", "1772521217009-9509490cdf3c",
        "1781040493573-7cf81186446f", "1768489039841-ef4f2d763233", "1781106476714-a06ef47ee069", "1765153417747-73d012027e36",
        "1770979820266-868f317f6e4a", "1753125319590-4670a0f1af05",
    ],
    ("women", "accessories"): [
        "1762331235358-d2df31849c3f", "1760551601203-12eddfb62216", "1735150033185-aad608b9686b", "1740032004036-8fa4a7f51360",
        "1627403776952-8a808982443f", "1762331224828-8bead4d3a50b", "1679466061812-211a6b737175", "1553843807-abcd02401fea",
        "1783916813147-da9b9323f3df",
    ],
    ("unisex", "accessories"): [
        "1706892807280-f8648dda29ef", "1774653273863-a689ee748eee", "1724318496828-3438b8c7f32c", "1629139033414-76f3c0eacf84",
        "1612902457652-33aff0a641fa", "1575201046471-082b5c1a1e79", "1680690653166-1618c3bcdf51", "1752214882661-53724e1557be",
        "1568752172055-6961c4146efd", "1697335639286-345485438ca0", "1590555663282-0ca237fb63aa",
    ],
    ("women", "dresses"): [
        "1576503898993-4abc2bb3795d", "1704775989614-8435994e4e97", "1762154057377-cc9d3dd6900c", "1763637896841-cd5a1bb18208",
        "1768803968298-e31d64afee56", "1764238385987-2ffa021755a1", "1634901623150-43bcf3cced26", "1563772268077-34452c8be316",
        "1612722432474-b971cdcea546", "1638620860173-d5265c2ba0b8", "1564857584869-6745ef113aba", "1576019855624-44a5251606cb",
        "1609357601502-0dae733e68c6", "1638620860101-e3187a82af7b", "1728297188853-a0eaaaa371e6", "1610290337288-93328db03bb8",
        "1638620859944-ec0ec26323a7",
    ],
    ("women", "skirts"): [
        "1708363390847-b4af54f45273", "1618244942912-7351be026e8b", "1762337679960-7aac10ef9f35", "1713355545899-6cbfb644dfb1",
        "1745315786452-6a32d8e1e48c", "1573878591960-37c788c55728", "1600681103852-5f6df72461aa", "1762343038913-2d0b726c291e",
        "1583235340050-f73f853f1b0f", "1600973964462-0cf10488d440", "1762343039071-fb52623712a5", "1590852669429-d1cd8775ea59",
        "1615898290907-0ad011905389", "1615898290837-e9e8cdc3a7fc", "1591288677690-6a29a7331f62", "1690840373418-c5d8deeba9ed",
        "1772449100716-c12cb4e1f21a",
    ],
}
FLAT_LAY_KEYS = {("unisex", "accessories")}
FALLBACK_IMAGE_ID = "1445205170230-053b83016050"


def _image_url(photo_id: str, *, flat_lay: bool = False) -> str:
    crop = "entropy" if flat_lay else "faces"
    return f"https://images.unsplash.com/photo-{photo_id}?w=900&h=1200&q=80&fit=crop&crop={crop}&auto=format"


IMAGE_BANK: dict[tuple[str, str], list[str]] = {
    key: [_image_url(pid, flat_lay=key in FLAT_LAY_KEYS) for pid in ids]
    for key, ids in IMAGE_IDS.items()
}
FALLBACK_IMAGE = _image_url(FALLBACK_IMAGE_ID)

_image_cursor: dict[tuple[str, str], int] = {}


def next_image(gender: str, category_slug: str) -> str:
    key = (gender, category_slug)
    pool = IMAGE_BANK.get(key)
    if not pool:
        return FALLBACK_IMAGE
    idx = _image_cursor.get(key, 0)
    _image_cursor[key] = idx + 1
    return pool[idx % len(pool)]


# ---------------------------------------------------------------------------
# Naming vocabulary - combined combinatorially per (category, gender) so every
# product gets a specific, realistic name (e.g. "Oversized Brushed Cotton
# Hoodie") instead of a numbered placeholder. Each category also carries
# technical material strings, a price band, and default season tags.
# ---------------------------------------------------------------------------
CATEGORY_VOCAB: dict[str, dict] = {
    "tshirts": dict(
        noun={"men": ["Tee", "T-Shirt", "Crewneck Tee"], "women": ["Tee", "T-Shirt", "Fitted Tee"]},
        fit={
            "men": ["Classic", "Slim-Fit", "Relaxed", "Oversized", "Boxy", "Regular-Fit", "Muscle-Fit"],
            "women": ["Fitted", "Cropped", "Oversized", "Relaxed", "Boxy", "Ribbed", "Baby"],
        },
        detail={
            "men": ["Cotton Jersey", "Pima Cotton", "Heavyweight Cotton", "Garment-Dyed", "Washed Cotton", "Slub Cotton", "Waffle-Knit"],
            "women": ["Cotton Jersey", "Pima Cotton", "Modal-Blend", "Ribbed", "Slub Cotton", "Washed Cotton", "Fitted Stretch"],
        },
        materials=["100% organic cotton, 180gsm jersey", "Pima cotton single jersey", "Cotton-modal blend, brushed interior", "Slub cotton jersey"],
        price=(28, 52), seasons=["summer", "spring"],
    ),
    "shirts": dict(
        noun={"men": ["Shirt", "Button-Down", "Poplin Shirt"], "women": ["Shirt", "Blouse", "Button-Down"]},
        fit={
            "men": ["Tailored", "Slim-Fit", "Relaxed", "Classic", "Oxford", "Camp-Collar", "Grandad-Collar"],
            "women": ["Tailored", "Relaxed", "Fitted", "Oversized", "Boyfriend", "Cropped", "Tie-Front"],
        },
        detail={
            "men": ["Cotton Poplin", "Brushed Flannel", "Linen-Cotton", "Oxford Cloth", "Chambray", "Seersucker", "End-on-End Cotton"],
            "women": ["Cotton Poplin", "Silky Satin", "Linen-Blend", "Chambray", "Georgette", "Crepe", "Cotton Voile"],
        },
        materials=["100% cotton poplin", "Linen-cotton blend", "Brushed flannel cotton", "Silky satin-weave polyester"],
        price=(58, 98), seasons=["spring", "summer", "fall"],
    ),
    "hoodies": dict(
        noun={"men": ["Hoodie", "Pullover Hoodie", "Zip Hoodie"], "women": ["Hoodie", "Pullover Hoodie", "Zip Hoodie"]},
        fit={
            "men": ["Heavyweight", "Relaxed", "Oversized", "Classic", "Boxy", "Regular"],
            "women": ["Cropped", "Oversized", "Relaxed", "Fitted", "Boxy"],
        },
        detail={
            "men": ["Brushed Fleece", "French Terry", "Cotton Loopback", "Garment-Dyed Fleece", "Heavyweight Cotton"],
            "women": ["Brushed Fleece", "French Terry", "Ribbed", "Cotton Loopback"],
        },
        materials=["80% cotton, 20% recycled polyester fleece", "100% organic cotton French terry", "Brushed-back cotton loopback"],
        price=(68, 110), seasons=["fall", "winter"],
    ),
    "sweaters": dict(
        noun={"men": ["Sweater", "Jumper", "Pullover"], "women": ["Sweater", "Jumper", "Pullover", "Knit"]},
        fit={
            "men": ["Fisherman", "Ribbed", "Crewneck", "Turtleneck", "Cable-Knit", "Half-Zip", "Shawl-Collar"],
            "women": ["Fine-Knit", "Cropped", "Oversized", "Turtleneck", "Cowl-Neck", "V-Neck", "Cable-Knit"],
        },
        detail={
            "men": ["Merino Wool", "Lambswool", "Cotton-Cashmere", "Chunky Wool", "Alpaca-Blend"],
            "women": ["Merino Wool", "Cashmere-Blend", "Mohair-Blend", "Cotton-Knit", "Ribbed Knit"],
        },
        materials=["100% merino wool", "Cotton-cashmere blend", "Lambswool knit", "Alpaca-blend knit"],
        price=(78, 150), seasons=["fall", "winter"],
    ),
    "jackets": dict(
        noun={"men": ["Jacket", "Blazer"], "women": ["Jacket", "Blazer"]},
        fit={
            "men": ["Bomber", "Moto", "Field", "Trucker", "Utility", "Varsity", "Tailored"],
            "women": ["Bomber", "Moto", "Cropped", "Utility", "Trucker", "Longline", "Tailored"],
        },
        detail={
            "men": ["Full-Grain Leather", "Waxed Cotton Canvas", "Recycled Nylon", "Suede", "Denim", "Wool-Blend"],
            "women": ["Faux Leather", "Waxed Cotton", "Quilted Nylon", "Suede", "Denim", "Wool-Blend"],
        },
        materials=["Full-grain leather", "Waxed cotton canvas", "Wool-blend twill", "Quilted recycled nylon"],
        price=(120, 260), seasons=["fall", "winter", "spring"],
    ),
    "coats": dict(
        noun={"men": ["Coat", "Overcoat"], "women": ["Coat", "Overcoat"]},
        fit={
            "men": ["Tailored Wool", "Long", "Storm", "Duffle", "Car Coat"],
            "women": ["Tailored", "Long", "Belted", "Wrap", "Cocoon"],
        },
        detail={
            "men": ["Wool-Blend Melton", "Waterproof Shell", "Shearling-Lined Suede", "Cotton Twill"],
            "women": ["Wool-Blend Melton", "Shearling-Lined Suede", "Waterproof Shell", "Faux Fur-Trim"],
        },
        materials=["Wool-blend melton", "Shearling-lined suede", "Technical waterproof shell", "Cotton twill"],
        price=(180, 340), seasons=["winter", "fall"],
    ),
    "jeans": dict(
        noun={"men": ["Jean", "Denim"], "women": ["Jean", "Denim"]},
        fit={
            "men": ["Slim-Fit", "Straight-Leg", "Relaxed", "Athletic-Fit", "Tapered", "Bootcut"],
            "women": ["High-Rise Skinny", "Straight-Leg", "Wide-Leg", "Mom-Fit", "Bootcut", "Slim-Straight"],
        },
        detail={
            "men": ["Stretch Selvedge Denim", "Rigid Organic Denim", "Washed Denim", "Raw Denim"],
            "women": ["Stretch Denim", "Rigid Organic Denim", "Washed Denim"],
        },
        materials=["Stretch selvedge denim", "Rigid organic cotton denim", "Washed comfort-stretch denim"],
        price=(78, 138), seasons=["fall", "spring"],
    ),
    "trousers": dict(
        noun={"men": ["Trouser", "Pant"], "women": ["Trouser", "Pant"]},
        fit={
            "men": ["Tailored", "Pleated", "Slim", "Wide-Leg", "Straight-Leg", "Suit"],
            "women": ["Tailored", "Wide-Leg", "Straight-Leg", "High-Rise", "Cigarette", "Palazzo"],
        },
        detail={
            "men": ["Italian Wool-Blend", "Stretch Cotton Twill", "Flannel Wool", "Linen-Blend"],
            "women": ["Stretch Cotton Twill", "Wool-Blend", "Linen-Blend", "Crepe"],
        },
        materials=["Italian wool-blend suiting", "Stretch cotton twill", "Flannel wool", "Linen-blend"],
        price=(68, 140), seasons=["fall", "spring"],
    ),
    "shorts": dict(
        noun={"men": ["Short", "Chino Short"], "women": ["Short", "Chino Short"]},
        fit={
            "men": ["Tailored", "Drawstring", "Classic", "Cargo", "Chino"],
            "women": ["Tailored", "High-Rise", "Bermuda", "Drawstring", "Paperbag"],
        },
        detail={
            "men": ["Cotton Twill", "Stretch Chino", "Linen-Blend"],
            "women": ["Cotton Twill", "Stretch Chino", "Linen-Blend"],
        },
        materials=["Cotton twill", "Stretch cotton chino", "Linen-blend"],
        price=(48, 82), seasons=["summer", "spring"],
    ),
    "activewear": dict(
        noun={
            "men": ["Performance Tee", "Training Tank", "Training Jogger", "Running Short", "Performance Half-Zip"],
            "women": ["Sports Bra", "Training Legging", "Studio Tank", "Training Jogger", "Performance Bra"],
        },
        fit={
            "men": ["Training", "Run", "Studio", "Performance", "Compression"],
            "women": ["Training", "Studio", "Run", "High-Support", "Seamless"],
        },
        detail={
            "men": ["Moisture-Wicking Polyester", "Brushed Technical Knit", "Recycled Performance Mesh"],
            "women": ["Moisture-Wicking Polyester", "Recycled Performance Mesh", "Ribbed Compression"],
        },
        materials=["Moisture-wicking recycled polyester", "Brushed technical knit", "Compression performance mesh"],
        price=(38, 98), seasons=["summer", "spring", "fall"],
    ),
    "swimwear": dict(
        noun={"men": ["Swim Short", "Board Short", "Swim Trunk"], "women": ["Swimsuit", "Bikini Set", "One-Piece"]},
        fit={
            "men": ["Resort", "Classic", "Printed", "Tailored"],
            "women": ["High-Waist", "Classic", "Printed", "Ruched", "Halter"],
        },
        detail={
            "men": ["Quick-Dry Recycled Nylon"],
            "women": ["Quick-Dry Recycled Nylon", "Ribbed Swim Fabric"],
        },
        materials=["Quick-dry recycled nylon-elastane", "Ribbed swim fabric"],
        price=(48, 98), seasons=["summer"],
    ),
    "shoes": dict(
        noun={"men": ["Sneaker", "Boot", "Loafer", "Derby"], "women": ["Sneaker", "Boot", "Heel", "Flat", "Mule"]},
        fit={
            "men": ["Court", "Trail", "Everyday", "Minimalist", "Leather"],
            "women": ["Court", "Everyday", "Minimalist", "Block-Heel", "Pointed-Toe"],
        },
        detail={
            "men": ["Full-Grain Leather", "Knit Mesh Upper", "Suede"],
            "women": ["Full-Grain Leather", "Knit Mesh Upper", "Suede"],
        },
        materials=["Full-grain leather", "Knit mesh upper", "Suede"],
        price=(98, 220), seasons=["fall", "spring", "summer"],
    ),
    "accessories": dict(
        noun={
            "men": ["Belt", "Wallet", "Watch", "Sunglasses", "Cap", "Crossbody Bag"],
            "women": ["Handbag", "Clutch", "Sunglasses", "Scarf", "Belt", "Jewelry Set", "Tote"],
        },
        fit={
            "men": ["Signature", "Classic", "Woven", "Minimalist"],
            "women": ["Signature", "Classic", "Woven", "Structured"],
        },
        detail={
            "men": ["Italian Leather", "Brushed Stainless Steel", "Merino Wool"],
            "women": ["Italian Leather", "Brushed Gold-Tone Metal", "Silk"],
        },
        materials=["Italian leather", "Brushed stainless steel", "Silk twill", "Merino wool"],
        price=(38, 180), seasons=["fall", "spring", "summer", "winter"],
    ),
    "dresses": dict(
        noun={"women": ["Dress"]},
        fit={
            "women": ["Wrap", "Slip", "Midi", "Off-Shoulder", "Tailored", "Bodycon", "Fit-and-Flare",
                       "Shirt", "Halter", "Cowl-Neck", "A-Line", "Faux-Wrap", "Puff-Sleeve", "Maxi", "Mini"],
        },
        detail={
            "women": ["Silk Crepe", "Cotton Poplin", "Stretch Jersey", "Satin", "Linen-Blend", "Ribbed Knit", "Georgette"],
        },
        materials=["Silk crepe", "Cotton poplin", "Stretch jersey", "Satin", "Linen-blend", "Georgette"],
        price=(88, 240), seasons=["spring", "summer", "fall"],
    ),
    "skirts": dict(
        noun={"women": ["Skirt"]},
        fit={"women": ["A-Line", "Pleated", "Midi", "Wrap", "Mini", "Maxi", "Bias-Cut", "Tiered", "Pencil"]},
        detail={"women": ["Wool-Blend", "Cotton Twill", "Satin", "Denim", "Linen-Blend"]},
        materials=["Wool-blend", "Cotton twill", "Satin", "Denim", "Linen-blend"],
        price=(68, 130), seasons=["spring", "summer", "fall"],
    ),
}

CARE_INSTRUCTIONS = {
    "tshirts": "Machine wash cold with like colors, tumble dry low, do not bleach.",
    "shirts": "Machine wash cold, hang to dry or tumble dry low, warm iron if needed.",
    "hoodies": "Machine wash cold inside out, tumble dry low, do not iron over print.",
    "sweaters": "Hand wash cold or dry clean, lay flat to dry, do not wring.",
    "jackets": "Wipe clean or spot treat; leather and suede pieces should be professionally cleaned.",
    "coats": "Dry clean only, store on a padded hanger.",
    "jeans": "Machine wash cold inside out, tumble dry low, wash sparingly to preserve color.",
    "trousers": "Dry clean or machine wash cold on a gentle cycle, hang to dry.",
    "shorts": "Machine wash cold, tumble dry low.",
    "activewear": "Machine wash cold, do not use fabric softener, hang or tumble dry low.",
    "swimwear": "Rinse in cold water after each wear, hand wash, lay flat to dry, avoid direct sun.",
    "shoes": "Wipe clean with a soft, dry cloth; treat leather with conditioner as needed.",
    "accessories": "Wipe clean with a soft cloth; store away from direct sunlight and moisture.",
    "dresses": "Dry clean or hand wash cold depending on fabric; hang to dry.",
    "skirts": "Dry clean or machine wash cold on a gentle cycle, hang to dry.",
}

OCCASIONS = ["casual", "date-night", "pool-party", "business-casual", "streetwear",
             "minimal", "all-black", "vacation", "wedding", "party", "active", "formal"]
STYLES = ["casual", "formal", "business-casual", "streetwear", "minimal"]

DESCRIPTION_TEMPLATES = [
    "Cut from {material} for a considered drape, the {name} brings {brand}'s quiet, "
    "editorial sensibility to {occasion} dressing. Finished with clean seams and a "
    "fit that layers effortlessly with the rest of your wardrobe.",
    "The {name} is built from {material} and designed to move with you - a versatile "
    "piece that reads polished for {occasion} without trying too hard. A Veloura "
    "wardrobe staple in the making.",
    "{brand} reworks a classic silhouette in {material}. The {name} balances structure "
    "and comfort, making it just as easy to dress up for {occasion} as it is to keep "
    "in weekly rotation.",
    "An essential from {brand}, the {name} takes {material} and pares it back to what "
    "matters: fit, texture, and durability. Style it for {occasion} or fold it into "
    "an everyday rotation - either way, it holds its shape wear after wear.",
    "Designed in {material}, the {name} is {brand}'s take on modern ease - considered "
    "proportions, a quietly confident finish, and enough range to move from {occasion} "
    "into whatever the rest of your day calls for.",
    "{brand}'s {name} pairs {material} with a fit that flatters without fuss, striking "
    "the balance between {occasion} polish and everyday comfort.",
]


def make_description(name: str, brand: str, material: str, occasion: str) -> str:
    template = random.choice(DESCRIPTION_TEMPLATES)
    return template.format(name=name, brand=brand, material=material, occasion=occasion)


def make_short_description(cat_name: str, material: str) -> str:
    singular = cat_name[:-1] if cat_name.endswith("s") and cat_name.lower() != "accessories" else cat_name
    return f"A refined {singular.lower()} in {material.lower()}."


def get_or_create_category(db: Session, slug: str, name: str) -> Category:
    existing = db.scalar(select(Category).where(Category.slug == slug))
    if existing:
        return existing
    category = Category(slug=slug, name=name, description=f"Shop {name.lower()} at Veloura.")
    db.add(category)
    db.flush()
    return category


CATEGORY_NAMES = {
    "tshirts": "T-Shirts", "shirts": "Shirts", "hoodies": "Hoodies", "sweaters": "Sweaters",
    "jackets": "Jackets", "coats": "Coats", "jeans": "Jeans", "trousers": "Trousers",
    "shorts": "Shorts", "activewear": "Activewear", "swimwear": "Swimwear", "shoes": "Shoes",
    "accessories": "Accessories", "dresses": "Dresses", "skirts": "Skirts",
}

# Target catalog volume: 13 shared categories get >=20 per gender (men get extra
# depth in shirts/jackets/trousers/activewear/accessories to make up for the two
# women-exclusive categories below, per spec); dresses/skirts are women-only.
CATEGORY_COUNTS: dict[str, dict[str, int]] = {
    "tshirts": {"men": 20, "women": 20},
    "shirts": {"men": 28, "women": 20},
    "hoodies": {"men": 20, "women": 20},
    "sweaters": {"men": 20, "women": 20},
    "jackets": {"men": 30, "women": 20},
    "coats": {"men": 20, "women": 20},
    "jeans": {"men": 20, "women": 20},
    "trousers": {"men": 28, "women": 20},
    "shorts": {"men": 20, "women": 20},
    "activewear": {"men": 26, "women": 20},
    "swimwear": {"men": 20, "women": 20},
    "shoes": {"men": 20, "women": 20},
    "accessories": {"men": 26, "women": 20},
    "dresses": {"women": 22},
    "skirts": {"women": 22},
}
UNISEX_ACCESSORY_COUNT = 6

UNISEX_ACCESSORY_ITEMS = [
    ("Signature Leather Belt", "Italian full-grain leather"),
    ("Classic Aviator Sunglasses", "Acetate frame, polarized lenses"),
    ("Ribbed Merino Beanie", "100% merino wool"),
    ("Structured Crossbody Bag", "Italian leather, brushed hardware"),
    ("Minimalist Field Watch", "Brushed stainless steel, sapphire crystal"),
    ("Everyday Canvas Tote", "Organic cotton canvas"),
    ("Woven Silk Scarf", "100% silk twill"),
    ("Classic Wool Cap", "Merino wool blend"),
]


def _generate_names(gender: str, vocab: dict, count: int) -> list[str]:
    fits = vocab["fit"][gender]
    details = vocab["detail"][gender]
    nouns = vocab["noun"][gender]
    combos = list(itertools.product(fits, details, nouns))
    random.shuffle(combos)

    names: list[str] = []
    seen: set[str] = set()
    pattern_cycle = itertools.cycle(["fit_noun", "fit_detail_noun", "detail_noun"])
    for fit, detail, noun in combos:
        if len(names) >= count:
            break
        pattern = next(pattern_cycle)
        if pattern == "fit_noun":
            name = f"{fit} {noun}"
        elif pattern == "detail_noun":
            name = f"{detail} {noun}"
        else:
            name = f"{fit} {detail} {noun}"
        if name in seen:
            continue
        seen.add(name)
        names.append(name)

    # Extremely small vocab spaces (shouldn't happen given the lists above) -
    # pad deterministically rather than crash.
    i = 0
    while len(names) < count:
        fit, detail, noun = combos[i % len(combos)]
        name = f"{fit} {detail} {noun} No. {i + 2}"
        if name not in seen:
            seen.add(name)
            names.append(name)
        i += 1
    return names[:count]


def build_products_for(gender: str, category_slug: str, count: int) -> list[dict]:
    vocab = CATEGORY_VOCAB[category_slug]
    cat_name = CATEGORY_NAMES[category_slug]
    names = _generate_names(gender, vocab, count)
    brand_pool = CATEGORY_BRAND_AFFINITY[category_slug]

    size_type = "shoes" if category_slug == "shoes" else ("accessory" if category_slug == "accessories" else "clothing")
    size_list = {"clothing": CLOTHING_SIZES, "shoes": SHOE_SIZES, "accessory": ONE_SIZE}[size_type]

    products = []
    for i, name in enumerate(names):
        brand = brand_pool[i % len(brand_pool)]
        direction, multiplier = BRANDS[brand]
        material = vocab["materials"][i % len(vocab["materials"])]
        occasion = random.choice(OCCASIONS)
        style = direction if direction in STYLES else random.choice(STYLES)

        low, high = vocab["price"]
        base_price = round(random.uniform(low, high) * multiplier, 2)
        on_sale = random.random() < 0.22
        sale_price = round(base_price * random.choice([0.7, 0.75, 0.8, 0.85]), 2) if on_sale else None

        season_tags = vocab["seasons"]
        occasion_tags = sorted({occasion, random.choice(OCCASIONS)})
        style_tags = sorted({style, random.choice(STYLES)})

        num_colors = 1 if size_type == "accessory" else 2
        colors = random.sample(COLORS, k=num_colors)

        variants = []
        for c_idx, (color_name, color_hex) in enumerate(colors):
            for size in size_list:
                sku = f"{category_slug[:3].upper()}-{gender[:1].upper()}{i:03d}{c_idx}-{size}".replace(" ", "")
                variants.append(dict(
                    sku=sku,
                    size=size,
                    color_name=color_name,
                    color_hex=color_hex,
                    inventory_quantity=random.choice([0, 2, 4, 8, 15, 25, 40]),
                    image_url=next_image(gender, category_slug),
                ))

        products.append(dict(
            name=name,
            brand=brand,
            gender=gender,
            category_slug=category_slug,
            category_name=cat_name,
            base_price=base_price,
            sale_price=sale_price,
            material=material.capitalize(),
            care_instructions=CARE_INSTRUCTIONS[category_slug],
            occasion_tags=occasion_tags,
            style_tags=style_tags,
            season_tags=season_tags,
            is_featured=random.random() < 0.15,
            description=make_description(name, brand, material, occasion.replace("-", " ")),
            short_description=make_short_description(cat_name, material),
            variants=variants,
        ))
    return products


def build_unisex_accessories() -> list[dict]:
    products = []
    brand_pool = CATEGORY_BRAND_AFFINITY["accessories"]
    for i, (name, material) in enumerate(UNISEX_ACCESSORY_ITEMS[:UNISEX_ACCESSORY_COUNT]):
        brand = brand_pool[i % len(brand_pool)]
        _, multiplier = BRANDS[brand]
        occasion = random.choice(OCCASIONS)
        base_price = round(random.uniform(38, 180) * multiplier, 2)
        on_sale = random.random() < 0.2
        sale_price = round(base_price * 0.8, 2) if on_sale else None
        colors = random.sample(COLORS, k=1)
        variants = []
        for c_idx, (color_name, color_hex) in enumerate(colors):
            sku = f"ACU-{i:03d}{c_idx}-OS"
            variants.append(dict(
                sku=sku, size="One Size", color_name=color_name, color_hex=color_hex,
                inventory_quantity=random.choice([0, 4, 12, 25]),
                image_url=next_image("unisex", "accessories"),
            ))
        products.append(dict(
            name=name, brand=brand, gender="unisex", category_slug="accessories",
            category_name="Accessories", base_price=base_price, sale_price=sale_price,
            material=material, care_instructions=CARE_INSTRUCTIONS["accessories"],
            occasion_tags=[occasion], style_tags=["minimal", "casual"],
            season_tags=["fall", "spring", "summer", "winter"],
            is_featured=random.random() < 0.15,
            description=make_description(name, brand, material, occasion.replace("-", " ")),
            short_description=make_short_description("Accessories", material),
            variants=variants,
        ))
    return products


def build_products() -> list[dict]:
    products: list[dict] = []
    for category_slug, gender_counts in CATEGORY_COUNTS.items():
        for gender, count in gender_counts.items():
            products.extend(build_products_for(gender, category_slug, count))
    products.extend(build_unisex_accessories())
    return products


def seed_products(db: Session) -> list[Product]:
    categories = {
        slug: get_or_create_category(db, slug, name) for slug, name in CATEGORY_NAMES.items()
    }
    db.commit()

    all_new_slugs: set[str] = set()
    created: list[Product] = []
    for data in build_products():
        base_slug = slugify(f"{data['brand']} {data['name']} {data['gender']}")
        slug = base_slug
        suffix = 2
        while slug in all_new_slugs:
            slug = f"{base_slug}-{suffix}"
            suffix += 1
        all_new_slugs.add(slug)

        existing = db.scalar(select(Product).where(Product.slug == slug))
        if existing:
            created.append(existing)
            continue

        product = Product(
            slug=slug,
            name=data["name"],
            brand=data["brand"],
            description=data["description"],
            short_description=data["short_description"],
            gender=Gender(data["gender"]),
            category_id=categories[data["category_slug"]].id,
            base_price=data["base_price"],
            sale_price=data["sale_price"],
            material=data["material"],
            care_instructions=data["care_instructions"],
            occasion_tags=data["occasion_tags"],
            style_tags=data["style_tags"],
            season_tags=data["season_tags"],
            is_featured=data["is_featured"],
            is_active=True,
        )
        for v in data["variants"]:
            product.variants.append(ProductVariant(**v))
        db.add(product)
        db.flush()
        created.append(product)
    db.commit()

    # Superseded rows from an older/narrower run of this script are deactivated
    # (never deleted - see scripts/reseed_products.py for an explicit, opt-in
    # purge) so the storefront only ever shows the current catalog.
    stale = db.scalars(
        select(Product).where(
            Product.brand.in_(KNOWN_SEED_BRANDS),
            Product.slug.not_in(all_new_slugs),
            Product.is_active.is_(True),
        )
    ).all()
    for product in stale:
        product.is_active = False
    if stale:
        db.commit()
        print(f"  -> deactivated {len(stale)} superseded product(s) from an older seed run.")

    return created


def seed_users(db: Session) -> tuple[User, User]:
    admin = db.scalar(select(User).where(User.email == "admin@veloura.com"))
    if not admin:
        admin = User(
            email="admin@veloura.com",
            hashed_password=hash_password("AdminPass123!"),
            first_name="Veloura",
            last_name="Admin",
            role=UserRole.ADMIN,
        )
        db.add(admin)
        db.flush()
        db.add(Cart(user_id=admin.id))
        db.add(Wishlist(user_id=admin.id))

    customer = db.scalar(select(User).where(User.email == "customer@veloura.com"))
    if not customer:
        customer = User(
            email="customer@veloura.com",
            hashed_password=hash_password("CustomerPass123!"),
            first_name="Ava",
            last_name="Customer",
            role=UserRole.CUSTOMER,
        )
        db.add(customer)
        db.flush()
        db.add(Cart(user_id=customer.id))
        db.add(Wishlist(user_id=customer.id))
        db.add(
            Address(
                user_id=customer.id,
                full_name="Ava Customer",
                line1="128 Rivington Street",
                line2="Apt 4B",
                city="New York",
                state="NY",
                postal_code="10002",
                country="United States",
                phone="+1 212 555 0199",
                is_default_shipping=True,
                is_default_billing=True,
            )
        )
    db.commit()
    return admin, customer


def seed_orders(db: Session, customer: User, products: list[Product]) -> None:
    existing = db.scalar(select(Order).where(Order.user_id == customer.id))
    if existing:
        return

    in_stock_variants = [
        (p, v) for p in products for v in p.variants if v.inventory_quantity > 3
    ]
    if len(in_stock_variants) < 4:
        return

    sample = random.sample(in_stock_variants, k=4)
    address = {
        "full_name": "Ava Customer",
        "line1": "128 Rivington Street",
        "line2": "Apt 4B",
        "city": "New York",
        "state": "NY",
        "postal_code": "10002",
        "country": "United States",
        "phone": "+1 212 555 0199",
    }

    for order_idx, chunk in enumerate([sample[:2], sample[2:]]):
        subtotal = sum(p.effective_price for p, _ in chunk)
        totals = calculate_order_totals(subtotal)
        order_number = f"VLR{100000 + order_idx + 1}"
        if db.scalar(select(Order).where(Order.order_number == order_number)):
            continue
        order = Order(
            user_id=customer.id,
            order_number=order_number,
            status=OrderStatus.DELIVERED if order_idx == 0 else OrderStatus.PROCESSING,
            shipping_address=address,
            **totals,
        )
        db.add(order)
        db.flush()
        for product, variant in chunk:
            db.add(
                OrderItem(
                    order_id=order.id,
                    variant_id=variant.id,
                    product_name=product.name,
                    variant_size=variant.size,
                    variant_color=variant.color_name,
                    unit_price=product.effective_price,
                    quantity=1,
                )
            )
    db.commit()


def seed_outfits(db: Session, customer: User, products: list[Product]) -> None:
    existing = db.scalar(select(Outfit).where(Outfit.user_id == customer.id))
    if existing:
        return

    by_category: dict[str, list[Product]] = {}
    for p in products:
        by_category.setdefault(p.category.slug if p.category else "", []).append(p)

    candidates = []
    for slug in ["tshirts", "trousers", "jackets"]:
        pool = [p for p in by_category.get(slug, []) if any(v.inventory_quantity > 0 for v in p.variants)]
        if pool:
            candidates.append(random.choice(pool))

    if len(candidates) < 2:
        return

    total = sum(p.effective_price for p in candidates)
    outfit = Outfit(
        session_id=None,
        user_id=customer.id,
        name="Styled by Veloura — City Weekend",
        explanation="A relaxed, editorial layering look built for a weekend in the city.",
        total_price=round(total, 2),
    )
    db.add(outfit)
    db.flush()
    for p in candidates:
        variant = next(v for v in p.variants if v.inventory_quantity > 0)
        db.add(
            OutfitItem(
                outfit_id=outfit.id,
                product_id=p.id,
                variant_id=variant.id,
                reason=f"Adds a versatile {p.category.name.lower()} layer to the look.",
            )
        )
    db.commit()


def seed_reviews(db: Session, customer: User, products: list[Product]) -> None:
    from veloura_api.models.review import Review

    existing = db.scalar(select(Review).where(Review.user_id == customer.id))
    if existing:
        return

    reviewable = [p for p in products if p.is_active][:3]
    sample_reviews = [
        (5, "Exactly as pictured", "The fit and fabric are even better in person. Ordering another color."),
        (4, "Great everyday piece", "Comfortable and holds up well after a few washes. True to size."),
        (3, "Good but runs small", "Nice material, but I'd size up if you're between sizes."),
    ]
    for product, (rating, title, body) in zip(reviewable, sample_reviews, strict=False):
        db.add(
            Review(
                product_id=product.id,
                user_id=customer.id,
                rating=rating,
                title=title,
                body=body,
                is_verified_purchase=True,
            )
        )
    db.commit()


def seed_coupons(db: Session) -> None:
    demo_coupons = [
        dict(
            code="WELCOME10",
            discount_type=DiscountType.PERCENTAGE,
            discount_value=10,
            free_shipping=False,
            min_order_value=None,
            max_discount=None,
            usage_limit=None,
            per_user_limit=1,
        ),
        dict(
            code="STYLE20",
            discount_type=DiscountType.PERCENTAGE,
            discount_value=20,
            free_shipping=False,
            min_order_value=150,
            max_discount=75,
            usage_limit=None,
            per_user_limit=None,
        ),
        dict(
            code="FREESHIP",
            discount_type=DiscountType.FIXED,
            discount_value=0,
            free_shipping=True,
            min_order_value=50,
            max_discount=None,
            usage_limit=None,
            per_user_limit=None,
        ),
    ]
    for data in demo_coupons:
        existing = db.scalar(select(Coupon).where(Coupon.code == data["code"]))
        if existing:
            continue
        db.add(Coupon(is_active=True, applicable_categories=[], applicable_products=[], **data))
    db.commit()


def main() -> None:
    db = SessionLocal()
    try:
        print("Seeding categories and products...")
        products = seed_products(db)
        print(f"  -> {len(products)} products in catalog.")

        print("Seeding users...")
        admin, customer = seed_users(db)
        print(f"  -> admin: {admin.email}, customer: {customer.email}")

        print("Seeding sample orders...")
        seed_orders(db, customer, products)

        print("Seeding sample outfits...")
        seed_outfits(db, customer, products)

        print("Seeding sample reviews...")
        seed_reviews(db, customer, products)

        print("Seeding demo coupons...")
        seed_coupons(db)

        print("Seed complete.")
    finally:
        db.close()


if __name__ == "__main__":
    main()

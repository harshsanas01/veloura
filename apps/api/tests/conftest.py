import os

os.environ["DATABASE_URL"] = "postgresql+psycopg://veloura:veloura@localhost:5433/veloura_test?sslmode=disable"
os.environ["JWT_SECRET_KEY"] = "test-secret-key"
os.environ["OPENAI_API_KEY"] = ""  # never hit the real OpenAI API in tests
os.environ["VELOURA_CORS_ALLOWED_ORIGINS"] = "http://localhost:5173"
os.environ["ENVIRONMENT"] = "test"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from veloura_api.config import get_settings
from veloura_api.database import get_db
from veloura_api.main import app
from veloura_api.models import Base  # noqa: F401 - registers all model tables

settings = get_settings()
engine = create_engine(settings.database_url, future=True)
TestingSessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    future=True,
    join_transaction_mode="create_savepoint",
)


@pytest.fixture(scope="session", autouse=True)
def _setup_database():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture()
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def register_user(client):
    def _register(email="shopper@example.com", password="TestPass123!", full_name="Test Shopper"):
        response = client.post(
            "/api/auth/register",
            json={"email": email, "password": password, "full_name": full_name},
        )
        assert response.status_code == 201, response.text
        return response.json()

    return _register


@pytest.fixture()
def auth_headers(register_user):
    data = register_user()
    return {"Authorization": f"Bearer {data['access_token']}"}, data["user"]


@pytest.fixture()
def admin_headers(client, db_session):
    from veloura_api.models.cart import Cart
    from veloura_api.models.user import User, UserRole
    from veloura_api.models.wishlist import Wishlist
    from veloura_api.security import hash_password

    admin = User(
        email="admin-test@veloura.com",
        hashed_password=hash_password("AdminPass123!"),
        full_name="Test Admin",
        role=UserRole.ADMIN,
    )
    db_session.add(admin)
    db_session.flush()
    db_session.add(Cart(user_id=admin.id))
    db_session.add(Wishlist(user_id=admin.id))
    db_session.commit()

    response = client.post(
        "/api/auth/login", json={"email": "admin-test@veloura.com", "password": "AdminPass123!"}
    )
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def seed_catalog(db_session):
    from veloura_api.models.category import Category
    from veloura_api.models.product import Gender, Product, ProductVariant

    category = Category(slug="tshirts", name="T-Shirts", description="Tees")
    db_session.add(category)
    db_session.flush()

    product = Product(
        slug="test-essential-tee",
        name="Essential Tee",
        brand="Veloura Studio",
        description="A soft, everyday tee in organic cotton, perfect for casual summer days.",
        short_description="A refined tee in organic cotton.",
        gender=Gender.UNISEX,
        category_id=category.id,
        base_price=40.00,
        sale_price=None,
        material="100% organic cotton",
        care_instructions="Machine wash cold.",
        occasion_tags=["casual", "summer"],
        style_tags=["casual", "minimal"],
        season_tags=["summer"],
        is_featured=True,
        is_active=True,
    )
    variant_in_stock = ProductVariant(
        sku="TEST-SKU-1",
        size="M",
        color_name="Black",
        color_hex="#111111",
        inventory_quantity=10,
        image_url="https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=800&q=80",
    )
    variant_out_of_stock = ProductVariant(
        sku="TEST-SKU-2",
        size="L",
        color_name="White",
        color_hex="#FAFAFA",
        inventory_quantity=0,
        image_url="https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=800&q=80",
    )
    product.variants.extend([variant_in_stock, variant_out_of_stock])
    db_session.add(product)

    inactive_product = Product(
        slug="test-inactive-item",
        name="Retired Item",
        brand="Veloura Studio",
        description="No longer sold, kept for history.",
        short_description="Retired.",
        gender=Gender.UNISEX,
        category_id=category.id,
        base_price=20.00,
        material="Cotton",
        care_instructions="Machine wash cold.",
        occasion_tags=[],
        style_tags=[],
        season_tags=[],
        is_active=False,
    )
    db_session.add(inactive_product)
    db_session.commit()

    return {
        "category": category,
        "product": product,
        "variant_in_stock": variant_in_stock,
        "variant_out_of_stock": variant_out_of_stock,
        "inactive_product": inactive_product,
    }

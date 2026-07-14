from fastapi import FastAPI, HTTPException, Request
from fastapi.exception_handlers import http_exception_handler
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from veloura_api.config import get_settings
from veloura_api.logging_config import configure_logging
from veloura_api.middleware.request_context import RequestContextMiddleware
from veloura_api.routes import (
    admin,
    ai_stylist,
    auth,
    cart,
    categories,
    health,
    orders,
    products,
    wishlist,
)

configure_logging()
settings = get_settings()

app = FastAPI(
    title="Veloura API",
    description="AI-powered fashion e-commerce platform API.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestContextMiddleware)


@app.exception_handler(HTTPException)
async def safe_http_exception_handler(request: Request, exc: HTTPException):
    return await http_exception_handler(request, exc)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=500, content={"detail": "An unexpected error occurred."})


api_router_prefix = "/api"
app.include_router(health.router, prefix=api_router_prefix)
app.include_router(auth.router, prefix=api_router_prefix)
app.include_router(categories.router, prefix=api_router_prefix)
app.include_router(products.router, prefix=api_router_prefix)
app.include_router(cart.router, prefix=api_router_prefix)
app.include_router(wishlist.router, prefix=api_router_prefix)
app.include_router(orders.router, prefix=api_router_prefix)
app.include_router(ai_stylist.router, prefix=api_router_prefix)
app.include_router(admin.router, prefix=api_router_prefix)

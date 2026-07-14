Veloura — Complete MVP

Repository: /Users/harshsanas01/Desktop/veloura (git initialized, 2 commits)

What's built and verified

- Backend (FastAPI + SQLAlchemy/Alembic + Postgres/pgvector): auth, catalog (61 seeded products across 15 categories), cart, wishlist, inventory-safe checkout, AI stylist (OpenAI structured outputs + deterministic fallback, with a validation layer that makes hallucinated product IDs structurally impossible to return), admin CRUD — all exercised via 45 passing pytest tests, clean ruff and mypy.
- Frontend (React/Vite/TS/Tailwind): every page in the spec, premium editorial design (burgundy/cream, Playfair Display + Inter), fully responsive, Zustand + TanStack Query, React Hook Form + Zod. 8 vitest tests, clean ESLint/tsc, production build succeeds (171 KB gzipped).
- Verified live in a real browser (Playwright): home, shop with filters, product detail, login, AI stylist producing budget-respecting real-product outfits, "add complete outfit to cart," wishlist, cart, admin products/orders — desktop and mobile. Found and fixed one real bug along the way (Framer Motion whileInView leaving product/section content at opacity:0).
- Docker Compose (Postgres+pgvector, API, web) built and run end-to-end — confirmed the containerized API serves the same seeded catalog.
- CI (.github/workflows/ci.yml): backend lint/typecheck/test + frontend lint/typecheck/test/build, no live OpenAI calls.
- Docs: README.md, docs/architecture.md, docs/api.md, docs/deployment.md (Vercel/Render/Neon step-by-step).

Demo credentials

- Admin: admin@veloura.com / AdminPass123!
- Customer: customer@veloura.com / CustomerPass123!

Setup

cp .env.example .env
docker compose up -d postgres
make install && make migrate && make seed
make dev-api   # http://localhost:8000
make dev-web   # http://localhost:5173

Known MVP limitations (documented in README)

No real payments (simulated checkout), no token-streaming chat (request/response with a validated JSON payload instead), AI stylist quality is materially better with OPENAI_API_KEY set than on its heuristic fallback, seed photography is reused across similar SKUs rather than one unique photo per variant, and admin product creation is one-at-a-time (no bulk import).
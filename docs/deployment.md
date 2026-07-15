# Deployment

Veloura deploys as three independent pieces: **Neon** (Postgres + pgvector), **Render** (FastAPI
API), and **Vercel** (React frontend). Deploy in that order — the frontend needs the API's URL,
and the API needs the database's connection string.

## 1. Neon (PostgreSQL)

1. Create a project at [neon.tech](https://neon.tech) and a database inside it (e.g. `veloura`).
2. Neon's Postgres includes the `vector` extension, but it must be enabled per-database. Open the
   Neon SQL editor and run:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```
   (The app's first Alembic migration also runs `CREATE EXTENSION IF NOT EXISTS vector`, so this
   is a safety net, not strictly required — but confirming it here avoids surprises.)
3. Copy the connection string from the Neon dashboard. It looks like:
   ```
   postgresql://user:password@ep-xxxx.us-east-2.aws.neon.tech/veloura?sslmode=require
   ```
   Rewrite the scheme for SQLAlchemy + psycopg3 and keep `sslmode=require`:
   ```
   postgresql+psycopg://user:password@ep-xxxx.us-east-2.aws.neon.tech/veloura?sslmode=require
   ```
   This is the value for `DATABASE_URL`.
4. Run migrations and seed data against Neon from your machine (or from a one-off Render shell —
   see step 4 below):
   ```bash
   export DATABASE_URL="postgresql+psycopg://user:password@ep-xxxx.../veloura?sslmode=require"
   cd apps/api && ../.venv/bin/alembic upgrade head
   cd ../.. && apps/api/.venv/bin/python scripts/seed_products.py
   apps/api/.venv/bin/python scripts/generate_embeddings.py  # optional, needs OPENAI_API_KEY
   ```
   `seed_products.py` is idempotent and safe to re-run against a database that already has real
   users/orders in it — it only adds missing seed rows and never deletes anything. If it detects
   products from an older seed generation, it deactivates (not deletes) them. To actually purge
   those deactivated rows, run `python scripts/reseed_products.py --confirm` separately — see the
   root [README](../README.md#database-migrations--seed-data) for details.

## 2. Render (FastAPI backend)

1. Create a new **Web Service** on [render.com](https://render.com), pointing at this repository.
2. Configuration:
   - **Root Directory:** `apps/api`
   - **Runtime:** Docker (Render will pick up `apps/api/Dockerfile`) — or, if you prefer Render's
     native Python runtime instead of Docker:
     - **Build Command:** `pip install -e .`
     - **Start Command:** `uvicorn veloura_api.main:app --host 0.0.0.0 --port $PORT`
   - If using the Docker option, Render's `$PORT` still needs to reach the container; the provided
     Dockerfile's `CMD` binds to a fixed port 8000, so either add `--port $PORT` to the Docker
     start command override in Render's dashboard, or use the native Python runtime above (simplest).
3. Environment variables (Render dashboard → Environment):
   ```
   DATABASE_URL=postgresql+psycopg://user:password@ep-xxxx.../veloura?sslmode=require
   OPENAI_API_KEY=sk-...
   OPENAI_CHAT_MODEL=gpt-4o-mini
   OPENAI_EMBEDDING_MODEL=text-embedding-3-small
   JWT_SECRET_KEY=<generate a long random value>
   JWT_ALGORITHM=HS256
   JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440
   VELOURA_CORS_ALLOWED_ORIGINS=https://<your-vercel-domain>.vercel.app
   LOG_LEVEL=INFO
   ENVIRONMENT=production
   ```
4. Run migrations against the production database once the service is configured. Easiest options:
   - Render's **Shell** tab on the service, then `cd apps/api && alembic upgrade head`.
   - Or run it locally against the Neon `DATABASE_URL` as shown in step 1.4 above.
5. Deploy. Confirm `https://<your-service>.onrender.com/api/health` returns `{"status": "ok"}`.

## 3. Vercel (React frontend)

1. Import this repository into [vercel.com](https://vercel.com).
2. Configuration:
   - **Root Directory:** `apps/web`
   - **Framework Preset:** Vite
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
3. Environment variable:
   ```
   VITE_API_BASE_URL=https://<your-render-service>.onrender.com/api
   ```
4. `apps/web/vercel.json` already configures the SPA rewrite so client-side routes (e.g.
   `/shop/men`) don't 404 on refresh:
   ```json
   { "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }] }
   ```
5. Deploy. Once live, go back to Render and update `VELOURA_CORS_ALLOWED_ORIGINS` to the final
   Vercel domain (redeploy the API for the change to take effect).

## Post-deploy checklist

- [ ] `GET https://<render-domain>/api/health` returns `200`
- [ ] Registering an account on the live frontend succeeds
- [ ] `/shop` loads real products from Neon
- [ ] `/ai-stylist` returns a recommendation (heuristic fallback works even without
      `OPENAI_API_KEY`; set the key to exercise the real OpenAI path)
- [ ] Checkout creates an order and decrements inventory
- [ ] `/admin` is reachable by the seeded admin account and blocked for customers

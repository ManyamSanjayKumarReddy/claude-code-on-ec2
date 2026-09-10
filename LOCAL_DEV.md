# Local Development

Quick reference for running this app on your own machine, independent of
the EC2 production instance. See `GUIDE.md` for the full environment
variable reference, migrations, backups, and production deployment steps —
this file only covers the local-only workflow.

**Why this differs from the full stack**: `web` (Nginx), `certbot`,
`prometheus`, and `grafana` all assume the production domain and its TLS
certs, or exist purely for production observability. None of them are
needed locally — just `db` + `backend` in Docker, and the frontend via
Vite's own dev server (it proxies `/api` to the backend, mirroring
production's proxy behavior — see `frontend/vite.config.ts` and CLAUDE.md's
architecture notes).

## One-time setup

```bash
git clone git@github.com:ManyamSanjayKumarReddy/claude-code-on-ec2.git
cd claude-code-on-ec2
cp .env.example .env
```

Edit `.env`:
- `ALLOWED_ORIGINS=http://localhost:5173`
- `SECRET_KEY` — generate with `python3 -c "import secrets; print(secrets.token_hex(32))"`
- `POSTGRES_*` / `DATABASE_URL` — fine as the example defaults (these are
  container-internal; the host port you use to reach `db` is separate, see
  below)
- `R2_*`, `LLM_*`, `GRAFANA_ADMIN_PASSWORD` — leave as placeholders, unused
  locally

Create `docker-compose.override.yml` in the repo root (git-ignored,
host-specific — Compose applies it automatically alongside
`docker-compose.yml`, no `-f` flag needed):

```yaml
services:
  backend:
    ports:
      - "5555:8000"
  db:
    ports:
      - "5556:5432"
```

These only change how you reach the containers *from your host* — the
containers still talk to each other internally via `db:5432`, unaffected
by this file.

```bash
cd frontend && npm install
```

## Starting the stack

```bash
docker compose up -d --build db backend
cd frontend && npm run dev
```

- App: http://localhost:5173/
- API health: http://localhost:5555/health
- Products API: http://localhost:5555/products

## Restarting after code changes

- Backend code changed: `docker compose up -d --build backend`
- Only `docker-compose.override.yml` changed (no code): `docker compose up -d backend`
- Crashed / want a clean restart, no rebuild: `docker compose restart backend`
- Frontend: nothing needed — Vite hot-reloads automatically

## Stopping

```bash
docker compose stop db backend
```
Stops the containers but keeps their data (the `db_data` volume survives).
Frontend: `Ctrl+C` in the terminal running `npm run dev`.

To also remove the containers (not just stop them), still keeping data:
```bash
docker compose down
```

To wipe local data too (fresh database next start) — destructive, local
data only, never run this against the production compose stack:
```bash
docker compose down -v
```

## Other useful commands

- `docker compose ps` — container status/health
- `docker compose logs -f backend` — tail backend logs
- `docker compose exec db psql -U storeapp -d storeapp` — open a psql shell
  against the local database (adjust the username if you changed
  `POSTGRES_USER`)
- `docker compose exec backend aerich migrate --name describe_the_change` /
  `aerich upgrade` — generate/apply migrations, same as production (see
  `GUIDE.md`)
- Running backend tests: see `GUIDE.md`'s "Running backend tests" section
  (uses a separate throwaway Postgres on port 5433, not this local dev `db`)

## Ports at a glance

| What | Local URL/port |
|---|---|
| Frontend (Vite dev server) | http://localhost:5173 |
| Backend (FastAPI/Uvicorn) | http://localhost:5555 (maps to container port 8000) |
| Postgres | localhost:5556 (maps to container port 5432) |

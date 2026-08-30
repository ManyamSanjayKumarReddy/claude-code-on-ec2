# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A small full-stack store app (FastAPI + Postgres backend, React frontend),
containerized with Docker Compose, deployed on a single EC2 instance behind
Nginx with a real Let's Encrypt HTTPS certificate. Live at
https://claude-on-ec2.theskilledguru.com.

**This working directory is the production server, not a separate dev
machine.** There is no staging environment yet. Changes made here and pushed
to `main` auto-deploy to the live site within seconds (see CI/CD below) —
there is currently no automated test gate in front of that (tracked as an
open item in `MAP.md`), so broken code pushed to `main` goes live immediately.

Three other docs exist and should be checked rather than duplicated here:
- `README.md` — features and tech stack (what the app does)
- `GUIDE.md` — full setup/deployment steps, environment variable reference,
  backup/restore procedure, and a troubleshooting section with real gotchas
  hit while building this (localhost/IPv6 healthcheck bug, DNS caching,
  Elastic IP checklist)
- `MAP.md` — a tracked roadmap/log of DevOps hardening work in progress.
  **Check this first** when resuming work here — it records what's done,
  what's next, and why, in order.

## Working style for this project

The user is learning DevOps deliberately through this project. For each
step of work (especially anything in `MAP.md`'s roadmap): explain what
you're about to do and why *before* doing it, then explain what actually
happened afterward. Don't just execute silently. Prefer verifying things
for real (e.g. an actual restore drill, not just "the upload succeeded")
over assuming success.

## Commands

Bring up the whole stack (from repo root):
```bash
docker compose up -d --build
```
(`db`, `backend`, `web`, `certbot` all start; only `web` is exposed on
80/443.) Note: `docker` group membership only applies to freshly-started
shell sessions — a long-lived interactive session started before the
`docker` group was granted needs `sg docker -c "..."` as a workaround.

Frontend, standalone dev server (hot reload, proxies `/api` to
`localhost:8000` — see `frontend/vite.config.ts`):
```bash
cd frontend && npm run dev
```

Frontend build/typecheck (`tsc -b && vite build`):
```bash
cd frontend && npm run build
```

Frontend lint:
```bash
cd frontend && npm run lint
```

Database migrations (Aerich) — generate after changing a model in
`backend/app/models/`, then apply:
```bash
docker compose exec backend aerich migrate --name describe_the_change
docker compose exec backend aerich upgrade
```
(Migrations also apply automatically on every backend container start via
`backend/entrypoint.sh`.)

Manual database backup (normally runs via cron daily at 03:00 UTC):
```bash
./scripts/backup-db.sh
```

There is no automated test suite yet (this is the current top item in
`MAP.md`'s roadmap) — don't assume a test command exists.

## Architecture notes that span multiple files

- **Two containers do the real work, not more**: `backend` (FastAPI) is
  never exposed directly — `web` (Nginx) is the only container with a
  published port, and it does double duty as both the static file server
  for the built React app *and* the reverse proxy to `backend` at `/api/*`.
  There is no separate "frontend" container; `frontend/Dockerfile` is a
  multi-stage build (Node build stage → Nginx runtime stage), so the final
  image contains both the built assets and the proxy config.
- **Nginx config is baked into the image at build time**
  (`frontend/nginx/` is `COPY`'d in `frontend/Dockerfile`), not
  bind-mounted — changing `frontend/nginx/conf.d/app.conf` requires
  `docker compose up -d --build web` to take effect, not just a restart.
- **The Vite dev proxy mirrors production's proxy behavior on purpose**:
  both the dev server (`frontend/vite.config.ts`) and production Nginx
  strip the `/api` prefix before forwarding to the backend, so the frontend
  code always calls `/api/...` regardless of environment — there's no
  separate dev/prod API base URL to keep in sync.
- **Tortoise ORM + Aerich share one config** (`backend/app/core/tortoise_config.py`)
  used both by the running app (via `RegisterTortoise` in `app/main.py`'s
  lifespan) and by the Aerich CLI — this is why Aerich commands must run
  inside the backend's environment (`docker compose exec backend aerich ...`),
  not from the host.
- **CI/CD**: `.github/workflows/deploy.yml` triggers on push to `main`,
  SSHs into the EC2 instance using a key that's restricted server-side (via
  a forced `command=` in `~/.ssh/authorized_keys`, not in this repo) to
  only ever run `deploy.sh` — regardless of what the workflow file asks
  for. `deploy.sh` does `git pull --ff-only` then `docker compose up -d --build`.
  Relevant secrets (`EC2_HOST`, `EC2_USER`, `EC2_SSH_KEY`) live in GitHub
  repo settings, not in this repo.
- **Backups** (`scripts/backup-db.sh`) go to Cloudflare R2 (chosen over S3
  for cost — no egress fees, non-expiring free tier), via the standard AWS
  CLI pointed at R2's S3-compatible endpoint. Credentials are in `.env`
  only (`R2_*` vars), never committed.
- **The EC2 instance has an Elastic IP attached.** If it's ever changed,
  three places need updating and none of them are obvious from grepping
  this repo alone: the DNS A record, `.env`'s `ALLOWED_ORIGINS`, and the
  `EC2_HOST` GitHub Actions secret. See `GUIDE.md`'s "Elastic IP" section.

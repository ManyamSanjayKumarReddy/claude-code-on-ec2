# Setup & Deployment Guide

## Project layout

- `backend/` — FastAPI app
  - `app/main.py` — app entrypoint, CORS, Tortoise ORM lifespan wiring
  - `app/models/product.py` — Tortoise ORM model
  - `app/schemas/product.py` — Pydantic request/response schemas
  - `app/api/products.py` — CRUD endpoints (`/products`)
  - `app/core/config.py` — environment-driven settings
  - `app/core/tortoise_config.py` — shared Tortoise config (used by both the
    app and Aerich)
  - `migrations/` — Aerich migration files (committed, applied automatically)
  - `entrypoint.sh` — runs `aerich upgrade` then starts Uvicorn
  - `Dockerfile`
- `frontend/` — React + Vite + TypeScript app
  - `src/components/products/` — `ProductForm`, `ProductCard`
  - `src/components/ui/` — shadcn/ui primitives (button, dialog, card, etc.)
  - `src/api/products.ts` — fetch client for `/api/products`
  - `nginx/` — Nginx reverse-proxy config, baked into the frontend's Docker
    image (this is also what terminates TLS in production)
  - `Dockerfile` — multi-stage: builds the Vite app, then serves it via Nginx
- `docker-compose.yml` — `db` (Postgres), `backend` (FastAPI), `web` (Nginx +
  static build), `certbot` (renews the TLS cert every 12h)
- `certbot/` — Let's Encrypt account/cert data (`conf/`) and the ACME
  HTTP-01 challenge webroot (`www/`); both are git-ignored, generated at
  runtime
- `.env` — local secrets/config, git-ignored; `.env.example` documents the
  required variables

## Environment variables

| Variable | Purpose |
|---|---|
| `ENVIRONMENT` | `development` / `production`, surfaced on `/health` |
| `ALLOWED_ORIGINS` | Comma-separated CORS origins the backend accepts |
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | Postgres credentials, used by the `db` service |
| `DATABASE_URL` | Tortoise ORM connection string, e.g. `postgres://user:pass@db:5432/dbname` |
| `R2_ENDPOINT_URL` / `R2_BUCKET` / `R2_ACCESS_KEY_ID` / `R2_SECRET_ACCESS_KEY` | Cloudflare R2 (S3-compatible) bucket used for database backups. The API token should be scoped to Object Read & Write on this one bucket only. |

## Local run

```bash
cp .env.example .env   # adjust values if needed
docker compose up -d --build
```

- App: http://localhost/
- API health: http://localhost/api/health
- Products API: http://localhost/api/products

## Database migrations

Migrations are managed with Aerich and run automatically by
`backend/entrypoint.sh` (`aerich upgrade`) every time the `backend` container
starts — you don't need to run anything by hand for the migrations already
in the repo.

When you change a model in `app/models/`, generate a new migration and commit
it:

```bash
docker compose exec backend aerich migrate --name describe_your_change
docker compose exec backend aerich upgrade
```

## Database backups

`scripts/backup-db.sh` dumps the database, compresses it, and uploads it to
a Cloudflare R2 bucket (S3-compatible, configured via the `R2_*` variables
above). It requires the AWS CLI installed locally (`aws --version`) — R2
speaks the S3 API, so the standard AWS CLI works against it via
`--endpoint-url` and `--region auto`, no R2-specific tooling needed.

Scheduled via cron, daily:
```bash
crontab -l   # check current entries
(crontab -l 2>/dev/null; echo "0 3 * * * /home/claudeuser/claude-code-on-ec2/scripts/backup-db.sh >> /home/claudeuser/backups.log 2>&1") | crontab -
```

An **object lifecycle rule** on the R2 bucket itself (Cloudflare dashboard →
bucket → Settings → Object Lifecycle Rules) auto-deletes backups older than
30 days — this isn't scriptable via the S3 API, it's a one-time dashboard
setting.

**Restoring a backup** (e.g. to verify one, or after real data loss):
```bash
aws s3 cp s3://<bucket>/<backup-file>.sql.gz /tmp/restore.sql.gz \
  --endpoint-url "$R2_ENDPOINT_URL" --region auto
docker compose exec -T db psql -U "$POSTGRES_USER" -c "CREATE DATABASE restore_test;"
gunzip -c /tmp/restore.sql.gz | docker compose exec -T db psql -U "$POSTGRES_USER" -d restore_test
```
Verify the data looks right, then either promote it (rename databases) or
drop `restore_test` if this was just a verification run.

## Deploying to a fresh EC2 instance (Ubuntu 24.04)

1. **Security group**: allow inbound 22 (SSH, ideally restricted to your IP),
   80 (HTTP), 443 (HTTPS).
2. **Install Docker**:
   ```bash
   sudo apt-get update && sudo apt-get install -y ca-certificates curl
   sudo install -m 0755 -d /etc/apt/keyrings
   sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
   sudo chmod a+r /etc/apt/keyrings/docker.asc
   echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
   sudo apt-get update
   sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
   sudo usermod -aG docker $USER   # log out/in (or `newgrp docker`) to apply
   ```
3. **Clone the repo and configure env**:
   ```bash
   git clone git@github.com:ManyamSanjayKumarReddy/claude-code-on-ec2.git
   cd claude-code-on-ec2
   cp .env.example .env
   # set ALLOWED_ORIGINS to your real domain, and a real POSTGRES_PASSWORD
   # (keep DATABASE_URL's password in sync with POSTGRES_PASSWORD)
   ```
4. **DNS**: at your registrar, add an A record for your (sub)domain pointing
   at the instance's public IPv4. Confirm it resolves before continuing
   (`dig +short A your.domain.com`).
5. **First boot over plain HTTP** (no cert yet — `frontend/nginx/conf.d/app.conf`
   should have only a `listen 80` server at this point):
   ```bash
   docker compose up -d --build
   ```
6. **Issue the certificate** (needs DNS already resolving to this instance):
   ```bash
   docker compose run --rm --entrypoint '' certbot certbot certonly \
     --webroot -w /var/www/certbot -d your.domain.com \
     --email you@example.com --agree-tos --no-eff-email --non-interactive
   ```
7. **Enable HTTPS**: add a `listen 443 ssl` server block to
   `frontend/nginx/conf.d/app.conf` referencing
   `/etc/letsencrypt/live/your.domain.com/{fullchain,privkey}.pem`, and turn
   the port-80 server into a redirect-to-https (keeping the
   `/.well-known/acme-challenge/` location for renewals). Then:
   ```bash
   docker compose up -d --build web
   ```
   The `certbot` service keeps running and renews the cert automatically
   every 12 hours.

## Troubleshooting notes

- **Healthchecks using `localhost` inside a container can fail spuriously**:
  if `/etc/hosts` resolves `localhost` to `::1` before `127.0.0.1` and the
  service only binds IPv4, a healthcheck using `http://localhost/...` gets
  "connection refused" even though the service works fine externally. Point
  healthchecks at `127.0.0.1` explicitly instead.
- **DNS changes can appear "stuck" on the machine that made them**: a
  resolver's own cache (e.g. a VPC or ISP resolver) can serve a stale answer
  for a while even after the authoritative nameservers are correct. Check
  with `dig +short A your.domain.com @8.8.8.8` (or `@1.1.1.1`) to see what
  the wider internet sees, independent of local caching.

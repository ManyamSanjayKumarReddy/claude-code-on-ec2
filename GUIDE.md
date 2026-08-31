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
  static build), `certbot` (renews the TLS cert every 12h), `prometheus`
  (scrapes `backend`'s `/metrics`), `grafana` (dashboards on top of Prometheus)
- `monitoring/` — `prometheus.yml` (scrape config) and
  `grafana/provisioning/datasources/` (auto-configures the Prometheus data
  source in Grafana on startup, no manual click-through needed)
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
| `IMAGE_TAG` | Optional; pins `backend`/`web` to a specific GHCR image tag (a git commit SHA) instead of `latest`, for rollback. Unset = `latest`. |
| `GRAFANA_ADMIN_PASSWORD` | Grafana's admin login password. See "Observability" below. |
| `LLM_BASE_URL` / `LLM_API_KEY` / `LLM_MODEL` | OpenAI-compatible endpoint for the product chat assistant (`/api/chat`). Optional — the endpoint errors until all three are set. |

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

## Running backend tests

Tests live in `backend/tests/` (pytest) and hit the real FastAPI app + a real
Postgres database — no mocking. They run automatically in CI on every push
and PR against `main` (see `.github/workflows/deploy.yml`), against a
Postgres service container, and gate the deploy job.

To run them locally, point a throwaway Postgres at them rather than the app's
real dev database, so test data never lands in the product catalog you're
looking at in the browser:

```bash
docker run --rm -d --name test-db -e POSTGRES_USER=test -e POSTGRES_PASSWORD=test \
  -e POSTGRES_DB=test -p 5433:5432 postgres:16-alpine

cd backend
pip install -r requirements.txt -r requirements-dev.txt
DATABASE_URL=postgres://test:test@localhost:5433/test aerich upgrade
DATABASE_URL=postgres://test:test@localhost:5433/test pytest

docker stop test-db
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
7 days — this isn't scriptable via the S3 API, it's a one-time dashboard
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

## Uptime monitoring

External monitoring lives in **Better Stack** (chosen over UptimeRobot
because UptimeRobot's free plan only alerts by email — Slack alerts require
their paid Team plan; Better Stack's free plan includes Slack alerts
natively, plus a faster 30s check interval vs UptimeRobot's 5min). There's
nothing to configure in this repo — it's entirely dashboard-side config on
betterstack.com, under the account that owns this project.

Two monitors watch the live site, on purpose checking different failure
modes:
- `https://claude-on-ec2.theskilledguru.com/` — catches the whole instance,
  `web` container, or Nginx being down.
- `https://claude-on-ec2.theskilledguru.com/api/health` — catches `backend`
  or `db` being down even while `web`/Nginx itself is still up and serving
  the static frontend (a failure the homepage check alone wouldn't catch).

Both alert to Slack (and email as a backup) on down/up transitions.
Reconfigure alert channels, check interval, or add more monitors from the
Better Stack dashboard directly — no deploy needed for changes there.

## Observability

Better Stack (above) answers "is the site up" from the outside. For "why is
it slow / what's actually happening," there's a second, internal layer:

- **Structured logging**: the backend emits one JSON line per log event
  (`structlog`, configured in `backend/app/core/logging.py`), instead of
  free-text lines. A middleware in `app/main.py` generates a `request_id`
  per request, binds it via `structlog.contextvars` so any log line during
  that request carries it, logs one `request_finished` line per request
  (method/path/status/duration_ms), and returns the id as an
  `X-Request-ID` response header. View it with `docker compose logs
  backend`. Uvicorn's own plain-text access log is disabled
  (`--no-access-log` in `entrypoint.sh`) to avoid duplicate lines in two
  different formats.
- **`/metrics`**: exposed by the backend via
  `prometheus-fastapi-instrumentator` — Prometheus text format, request
  counts/latency histograms per endpoint. Not proxied through Nginx, so
  it's unreachable from the public internet by construction (Nginx only
  proxies `/api/*` to the backend).
- **Prometheus**: scrapes `backend:8000/metrics` every 15s (config:
  `monitoring/prometheus.yml`), stores history in its own volume
  (`prometheus_data`).
- **Grafana**: dashboards on top of Prometheus, own volume
  (`grafana_data`). Its Prometheus data source is auto-provisioned
  (`monitoring/grafana/provisioning/datasources/prometheus.yml`) — nothing
  to click through manually after a fresh deploy.

**Both Prometheus (`:9090`) and Grafana (`:3000`) are bound to
`127.0.0.1` only** in `docker-compose.yml` — not exposed on the public
internet, unlike `web`. Neither has the kind of hardening (rate-limited
logins, etc.) that'd make sense to expose publicly on a real domain. View
them via an SSH tunnel instead:

```bash
ssh -i /path/to/your-key.pem -L 3000:localhost:3000 ubuntu@<instance-ip> -N
```

Then open `http://localhost:3000` in your own browser. `-L <local>:<dest-host>:<dest-port>`
forwards a port on *your* machine through the SSH connection to that
destination *as seen by the server* — the `localhost` after the colon
refers to the EC2 instance, not your laptop. Use whichever account/key you
already SSH into the instance with (e.g. `ubuntu` + its `.pem` key) — the
GitHub Actions deploy key can't be used for this even if you had it; it's
restricted server-side to only run `deploy.sh`, with `no-port-forwarding`
explicitly set.

Log into Grafana with `admin` / the `GRAFANA_ADMIN_PASSWORD` value from
`.env`. The Prometheus data source is already there. For dashboards,
**build your own panels rather than trusting a random imported
community dashboard ID** — several were tried and showed no data because
they expect label names (like `app_name`) that this setup doesn't emit;
our labels are `handler`/`method`/`status`/`job`/`instance`. Useful
starter queries, as **Time series** panels unless noted:
- Request rate by endpoint: `sum(rate(http_requests_total[5m])) by (handler)`
- p95 latency by endpoint: `histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, handler))`
- Total requests (as a **Stat** panel): `sum(http_requests_total)`

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

## Elastic IP

This instance has an Elastic IP attached (not just its default auto-assigned
public IP), specifically so it survives a **stop/start** — a plain public
IPv4 is only guaranteed to stay the same across a *reboot*, not a stop/start,
which would otherwise silently break DNS. Elastic IPs are free while
attached to a running instance, but AWS charges a small hourly fee while
it's attached to a *stopped* one — trivial for occasional overnight stops,
but worth knowing.

If this Elastic IP is ever released and a new one associated instead
(or if you're setting this up fresh), update it in **all** of these places
— it's easy to only remember the obvious one:
- The DNS A record at your registrar
- `.env`'s `ALLOWED_ORIGINS`
- The `EC2_HOST` GitHub Actions secret (used by the CI/CD deploy workflow) —
  easy to forget since it's not in any file in this repo

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
- **The `backend` image has no `curl`** (it's `python:3.12-slim`, kept
  minimal on purpose). To poke an endpoint from inside the container, use
  Python instead: `docker compose exec backend python3 -c "import
  urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8000/metrics').read().decode())"`.

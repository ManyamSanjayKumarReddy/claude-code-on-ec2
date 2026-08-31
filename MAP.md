# DevOps Learning Roadmap

A tracked log of the steps taken to mature this project from "it works" to
"it works reliably." Each item gets checked off with a short writeup of what
was actually done and why, once it's complete — this file is a learning
journal, not just a checklist.

## Tier 1 — Safety nets

These close real risks that exist *right now* in the current setup.

- [x] **1. Automated Postgres backups** — see log below.
- [x] **2. Tests running in CI before deploy** — see log below.
- [x] **3. Basic uptime monitoring/alerting** — see log below.

## Tier 2 — CI/CD maturity

- [x] **4. Build-once image registry + versioned deploys** — see log below.
- [ ] **5. A staging environment** — a second, smaller deployment that gets
      updates first, so changes can be sanity-checked before hitting the
      real production site.

## Tier 3 — Infrastructure & hardening

- [ ] **6. Infrastructure as Code (Terraform)** — the EC2 instance, security
      group, etc. currently exist only because of manual AWS console
      clicks. Codifying them means the *entire environment*, not just the
      app, is reproducible from files in git.
- [ ] **7. Server hardening** — automatic security patches, `fail2ban`
      against SSH brute-forcing, tighter access rules.

## Tier 4 — Scaling (later, only if this needs to handle real traffic)

- [ ] **8. Moving beyond a single instance** — a load balancer with multiple
      instances, or a managed platform (ECS/Kubernetes).

## Tier 5 — E-commerce depth (build before Tier 6)

The product catalog + chat assistant work surfaced a real problem: there's
not enough *substance* under the AI layer to justify the harder GenAI
patterns. Search-and-answer over a bare product table doesn't need an
agent — a single retrieve-then-generate call handles it fine. Real
orders/carts/returns give agents actual actions with consequences, not
just lookups, which is what makes Tier 6's agent/multi-agent work a real
exercise instead of a decorative one. No payment integration — that's a
deliberate scope cut, not a gap; the goal is state and workflow depth for
the AI layer to work against, not a real checkout.

- [ ] **9. User accounts** — registration/login, so orders/carts/returns
      have someone to belong to.
- [ ] **10. Shopping cart** — add/remove/update items, persisted per user.
- [ ] **11. Checkout & shipping flow (no payment)** — address, shipping
      method, order creation from a cart.
- [ ] **12. Order management** — a real lifecycle (placed → confirmed →
      shipped → delivered), not just a row that exists or doesn't.
- [ ] **13. Returns & refunds workflow** — stateful and multi-step (request
      → validate eligibility → approve/reject → process) — the shape of
      thing that actually needs an agent, unlike a plain product lookup.

## Tier 6 — AI/GenAI production curriculum (staged, builds on Tier 5)

Treating this as a deliberate learning progression, not a feature list —
each stage should be done at production depth, not the simplified/toy
version. Sequenced in order; later stages depend on earlier ones.

- [ ] **14. Stage 1 — harden the existing chat assistant.** What exists
      (`/api/chat`, retrieve-then-generate against the real LLM endpoint) is
      the toy version. Production-grade needs: timeouts + retry/backoff on
      the LLM call itself (currently a hang on their end just hangs us),
      token usage tracking (no cost visibility today), prompt management
      (system prompt is a hardcoded string, not versioned/tested like
      code), and streaming responses (users wait ~6s staring at "Thinking...").
- [ ] **15. Stage 2 — real RAG.** Current "RAG" is keyword-match-then-inject
      — a toy. Real RAG needs: a proper chunking strategy (matters once
      policy docs from Tier 5 exist), embeddings + `pgvector` (same
      Postgres, no new infra), hybrid retrieval (keyword + vector via
      reciprocal rank fusion — production RAG is rarely vector-only),
      re-ranking as a second pass, answer attribution/citations, and actual
      retrieval-quality evaluation instead of eyeballing replies.
- [ ] **16. Stage 3 — agents (LangChain/LangGraph), for real.** Blocked on
      a real constraint: the current LLM gateway (`gpt-oss-20b` via
      `llm-dev.vivaquest.in`) crashes on tool-call output — a Harmony-format
      parsing bug on their end, diagnosed via direct curl isolation (see
      the observability aside below this section once written up). Doing
      this stage properly needs either that gateway's tool-call parser
      fixed, or a different endpoint confirmed to support function-calling
      reliably. Once unblocked: multi-step reasoning, proper tool schemas
      against Tier 5's real actions (place an order, check status, start a
      return), conditional routing via LangGraph's graph (not a flat
      ReAct loop), and conversation memory (today every message is
      stateless — no follow-up context at all).
- [ ] **17. Stage 4 — multi-agent + MCP.** A supervisor/router agent
      dispatching to specialized sub-agents (ProductAgent, OrderAgent,
      PolicyAgent) — only meaningfully different from one big prompt once
      Tier 5 gives each agent genuinely distinct responsibilities and real
      data to act on. Also: exposing the tools (`search_products`, order
      lookup, policy search) as a real MCP server, not just in-process
      LangChain tools. Depends on Stage 3's tool-calling blocker being
      resolved first.
- [ ] **18. Stage 5 — LLM-specific observability.** The Prometheus/Grafana
      work (see the observability aside) covers *app* health, not
      *LLM/agent* health. Needs: per-call tracing (prompt, model, latency,
      tokens, cost), agent trace visualization (the actual sequence of
      reasoning/tool-call steps per request — what Langfuse/LangSmith are
      for), automated eval pipelines (golden datasets, LLM-as-judge,
      retrieval metrics — not manual spot-checks), and production LLM-ops:
      rate limiting on `/chat` (flagged as urgent — it's live on a public
      domain, costs money per call, and has zero abuse protection right
      now), cost budgets/alerts, fallback behavior if the LLM is down.

---

## Log

### 1. Automated Postgres backups (done)

**Storage: Cloudflare R2**, not AWS S3 — chosen for cost: R2 has no egress
fees and a free tier (10GB storage, generous request limits) that doesn't
expire after 12 months like S3's does. For this project's data volume, R2
should stay free indefinitely.

**How it works:**
- `scripts/backup-db.sh` — dumps the `products` table (and everything else
  in the database) with `pg_dump` inside the running `db` container,
  compresses it, and uploads it to the R2 bucket via the AWS CLI (R2 is
  S3-API-compatible, so the standard `aws s3 cp --endpoint-url ...` works
  against it directly — no R2-specific tooling needed).
- Credentials live in `.env` (`R2_ENDPOINT_URL`, `R2_BUCKET`,
  `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`) — gitignored, never committed.
  The R2 API token is scoped to Object Read & Write on this one bucket only,
  not full Cloudflare account access.
- A cron job (`crontab -l` on the `claudeuser` account) runs the script
  daily at 03:00 UTC, logging to `~/backups.log`.
- A **lifecycle rule** on the R2 bucket itself (set once, in the Cloudflare
  dashboard — not scriptable via the S3 API) auto-deletes backups older
  than 7 days, so storage cost never grows unbounded.

**Verified, not just assumed:** ran the script manually, confirmed the
object landed in R2, then did a full restore drill — downloaded that exact
backup, restored it into a scratch `restore_test` database, and confirmed
its row count matched the live database exactly before dropping the scratch
db. A backup that's never been test-restored isn't a verified backup.

**Key lesson:** a backup stored on the same disk as the thing it's backing
up protects against nothing — it has to live somewhere else entirely. Object
storage (S3/R2) plus a scoped, least-privilege credential is the standard
pattern for exactly this.

### 2. Tests running in CI before deploy (done)

**The gap:** `deploy.yml` triggered on every push to `main` and SSH'd
straight into the EC2 instance with no verification step at all — a typo, a
broken migration, or a crashing endpoint would go live within seconds of
being pushed.

**Backend tests:** `backend/tests/` (pytest + FastAPI's `TestClient`) hits
the real app and a real Postgres database — no mocking — covering the
product CRUD endpoints and their 404/validation cases. Kept as real
integration tests rather than mocked unit tests, same reasoning as the
backup restore drill: a test that never talks to the actual database can
pass while the actual database interaction is broken.
`backend/requirements-dev.txt` keeps `pytest`/`httpx` out of the production
image — only installed in CI (and optionally by hand for local runs, see
GUIDE.md's "Running backend tests").

**Frontend:** no test framework exists yet (tracked as a possible future
step, not done here) — CI enforces the checks that already existed but
weren't gated on anything: `npm run build` (includes the `tsc -b`
typecheck) and `npm run lint`.

**CI wiring:** `.github/workflows/deploy.yml` is now three jobs:
`backend-tests` (spins up a `postgres:16-alpine` GitHub Actions service
container — same image as prod — runs the real Aerich migrations against
it, then pytest), `frontend-checks` (build + lint), and `deploy`, which
declares `needs: [backend-tests, frontend-checks]` — if either check job
fails, `deploy` never runs. The workflow now also triggers on
`pull_request` against `main` (not just `push`), so a PR shows red/green
before merge; `deploy` itself is additionally gated with
`if: github.event_name == 'push'` so PRs never trigger a deploy.

**Verified, not just assumed:** ran the full suite locally against a
throwaway Postgres container (`ci-test-db`, separate from the live `db`
container — never pointed tests at real data) before writing any CI YAML,
confirmed all 10 backend tests pass and migrations apply cleanly on a fresh
database, and ran `npm run build`/`npm run lint` locally too.

### 3. Basic uptime monitoring/alerting (done)

**The gap:** no way to find out the site was down other than checking it by
hand.

**Service: Better Stack**, not UptimeRobot — UptimeRobot's free plan only
supports email alerts; Slack alerts require their paid Team plan
($29/month). Better Stack's free plan includes Slack alerts natively (and a
faster 30s check interval vs UptimeRobot's 5min free tier), which is exactly
what was needed. This lives entirely outside the repo — no code or config
files here, it's dashboard-configured on betterstack.com. See GUIDE.md's
"Uptime monitoring" section.

**Two monitors, deliberately checking different failure modes:**
- The homepage (`/`) — catches the instance/`web` container/Nginx being down.
- `/api/health` — catches `backend`/`db` failing even while Nginx itself is
  still up and serving the static frontend, which the homepage check alone
  wouldn't catch.

Both alert to Slack + email.

**Verified, not just assumed:** deliberately stopped the `web` container
(confirmed both the homepage and `/api/health` genuinely stopped responding
— connection failures, not just slow responses) for about 75 seconds, then
restarted it. The Slack alert landed. First attempt at this drill was a
false start: it happened to overlap with an unrelated CI/CD deploy (from a
docs-only push made moments earlier) that ran `docker compose up -d
--build` mid-drill and silently brought `web` back up before the outage
could be detected — worth remembering that a deploy in flight can mask a
monitoring test like this. Re-ran it once no deploy was pending and got a
clean result.

### 4. Build-once image registry + versioned deploys (done)

**The gap:** `deploy.sh` did `git pull` then `docker compose up -d --build`
— every deploy compiled the frontend (`npm run build`/Vite) and installed
backend dependencies **on the production EC2 instance itself**. CI only
ever checked the code (tests, lint, a separate `npm run build` inside
GitHub's own environment); it never produced the actual artifact that went
live. Two independent builds of "the same" code, in two different
environments, is exactly the kind of drift that can make something pass CI
and still break in prod.

**Registry: GitHub Container Registry (GHCR)**, not Docker Hub or ECR —
GitHub Actions already hands every workflow run a `GITHUB_TOKEN` scoped to
push to `ghcr.io`, so no new secret or account had to be created just to
push images. The two packages (`claude-code-on-ec2-backend`,
`claude-code-on-ec2-web`) were set to public after confirming neither
Dockerfile bakes in any `.env` secret at build time — secrets are only
injected at container *runtime* via `env_file:`, never as build args — so
production can `docker pull` them with no stored credential at all.

**How it works now:**
- A new `build-and-push` job in `.github/workflows/deploy.yml`, gated on
  `needs: [backend-tests, frontend-checks]` (only tested code ever becomes
  an image), builds the `backend` and `web` images and pushes each with two
  tags: the git commit SHA (precise, for rollback) and `latest` (what
  production tracks). `deploy` now also `needs: build-and-push`.
- `docker-compose.yml` keeps `build: ./backend` / `build: ./frontend` (so
  local dev can still `docker compose up -d --build`), but `image:` on both
  services now points at
  `ghcr.io/manyamsanjaykumarreddy/claude-code-on-ec2-{backend,web}:${IMAGE_TAG:-latest}`.
  Compose only builds when explicitly told to (`--build`); otherwise it
  pulls whatever `image:` resolves to — that split is what lets local dev
  and production use the same file with opposite behavior.
- `deploy.sh` no longer builds anything: `git pull` → `docker compose pull
  backend web` → `docker compose up -d`.
- Rollback capability (not yet exercised for a real incident): set
  `IMAGE_TAG=<git-sha>` in `.env` on the server and redeploy to pin an
  exact previous image instead of `latest`.

**Bug hit along the way:** the first CI run failed with `invalid tag ...
repository name must be lowercase`. Cause: `github.repository_owner`
evaluates to the GitHub username's original case
(`ManyamSanjayKumarReddy`), but container registry paths must be all
lowercase, and GitHub Actions expressions have no built-in lowercase
function. Fixed by hardcoding the lowercase owner
(`manyamsanjaykumarreddy`) directly in the tag strings instead of
interpolating it.

**Verified, not just assumed:** after the full pipeline went green, checked
the *actual running containers* on the server rather than trusting the
green checkmark — `docker compose ps` showed `backend`/`web` tagged
`ghcr.io/manyamsanjaykumarreddy/claude-code-on-ec2-{backend,web}:latest`
(pulled images, not locally-built ones), both `healthy`, and the live site
still returned `200` on both `/` and `/api/health` afterward. The old
locally-built images (`claude-code-on-ec2-backend`/`-web`, un-namespaced)
were left orphaned on disk and removed with `docker image prune`.

**Key lesson:** "CI passed" and "the right thing is running in production"
are two different claims — the pipeline going green only proves the deploy
*step* succeeded, not that the server ended up running the image you think
it did. Checking the actual container image tag on the box is what closes
that gap.

### Aside: Elastic IP (not on the original roadmap, but done in between)

Needed so the instance's address survives a stop/start, not just a reboot.
Allocated and associated in the AWS console, then updated in three places —
the DNS A record, `.env`'s `ALLOWED_ORIGINS`, and the `EC2_HOST` GitHub
Actions secret. That last one is easy to miss since it isn't in any file in
the repo at all — worth remembering next time an IP changes. See GUIDE.md's
"Elastic IP" section for the full checklist.

### Aside: Skip CI/CD on docs-only changes (not on the original roadmap, but done in between)

Noticed while closing item 4: the workflow trigger had no path filtering,
so a commit that only touched `README.md`/`MAP.md` still ran the full
pipeline — tests, an image rebuild/push to GHCR, and a real restart of the
live `backend`/`web` containers, for zero code change. Fixed with
`paths-ignore: ['**.md']` on both the `push` and `pull_request` triggers in
`.github/workflows/deploy.yml` — a push where every changed file is
markdown now skips the pipeline entirely; a push that touches both docs
and code still runs normally.

### Aside: Observability — structured logging + Prometheus/Grafana (not on the original roadmap, but done in between)

Grew out of a separate, parallel learning track (system-design/MLOps
concepts) rather than a gap this file had flagged — but it's real,
running infrastructure now, so it belongs here too. Better Stack (item 3)
answers "is the site up"; this answers "why, and how much." See GUIDE.md's
"Observability" section for the full how-to, including the SSH tunnel
command.

**Three layers, built in order:**
1. **Structured JSON logging** (`structlog`) — one JSON line per log
   event instead of free text, with a per-request `request_id` (generated
   in `app/main.py`'s middleware, bound via `structlog.contextvars` so any
   log line during that request carries it automatically) also returned as
   an `X-Request-ID` response header. Uvicorn's own plain-text access log
   is disabled to avoid duplicate lines in two formats.
2. **`/metrics`** — `prometheus-fastapi-instrumentator` adds a standard
   Prometheus-format endpoint (request counts, latency histograms by
   handler). Not proxied through Nginx, so it's unreachable from the
   public internet by construction, same as the backend itself already was.
3. **Prometheus + Grafana** — Prometheus scrapes `/metrics` every 15s and
   stores history in its own volume; Grafana queries Prometheus live and
   is pre-provisioned with it as a data source (no manual click-through).
   Both bound to `127.0.0.1` only in `docker-compose.yml`, viewed via an
   SSH tunnel — same trust boundary as SSH itself, deliberately not on the
   same public-internet footing as `web`.

**Verified, not just assumed:** confirmed Prometheus's own target list
showed `backend:8000` as `up`, queried it directly and got real counts
back (not just "the pipeline looks green"), confirmed from outside the
instance that hitting the public domain on `:3000`/`:9090` gets nothing,
and — while setting up tunnel access — discovered `claudeuser` had no
personal SSH key at all (only the GitHub Actions deploy key, which is
`no-port-forwarding` and forced to only run `deploy.sh` anyway), so
tunnel access actually goes through the `ubuntu` account's existing key
instead.

**Key lesson:** a green pipeline / a "success" API response isn't the same
claim as "this is actually usable" — the GHCR pull step going green
earlier didn't prove the running container was the pulled image (item 4's
own lesson), and here, `/metrics` returning real Prometheus text didn't
mean a random imported community dashboard (ID 14282) would show anything
— it expected a label (`app_name`) this setup doesn't emit. Building 2-3
panels by hand with known-good queries against data already confirmed to
exist was more reliable than trusting someone else's dashboard's assumed
label schema.

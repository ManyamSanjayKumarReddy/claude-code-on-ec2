# DevOps Learning Roadmap

A tracked log of the steps taken to mature this project from "it works" to
"it works reliably." Each item gets checked off with a short writeup of what
was actually done and why, once it's complete — this file is a learning
journal, not just a checklist.

## Tier 1 — Safety nets

These close real risks that exist *right now* in the current setup.

- [x] **1. Automated Postgres backups** — see log below.
- [ ] **2. Tests running in CI before deploy** — `git push` to `main`
      currently auto-deploys with zero checks in between. Broken code would
      deploy broken code, instantly, to the live site.
- [ ] **3. Basic uptime monitoring/alerting** — there is currently no way to
      find out the site is down other than manually checking it.

## Tier 2 — CI/CD maturity

- [ ] **4. Build-once image registry + versioned deploys** — every deploy
      currently rebuilds Docker images *on the production server itself*.
      The more standard pattern: CI builds and tags an image, pushes it to a
      registry, and the server just pulls and runs that exact artifact —
      enabling instant rollback and keeping build tooling off production.
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
  than 30 days, so storage cost never grows unbounded.

**Verified, not just assumed:** ran the script manually, confirmed the
object landed in R2, then did a full restore drill — downloaded that exact
backup, restored it into a scratch `restore_test` database, and confirmed
its row count matched the live database exactly before dropping the scratch
db. A backup that's never been test-restored isn't a verified backup.

**Key lesson:** a backup stored on the same disk as the thing it's backing
up protects against nothing — it has to live somewhere else entirely. Object
storage (S3/R2) plus a scoped, least-privilege credential is the standard
pattern for exactly this.

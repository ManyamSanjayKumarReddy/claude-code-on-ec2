# DevOps Learning Roadmap

A tracked log of the steps taken to mature this project from "it works" to
"it works reliably." Each item gets checked off with a short writeup of what
was actually done and why, once it's complete — this file is a learning
journal, not just a checklist.

## Tier 1 — Safety nets

These close real risks that exist *right now* in the current setup.

- [ ] **1. Automated Postgres backups** — all product data currently lives
      only in a Docker volume on this one EC2 instance. No backup exists. If
      the disk or instance is lost, the data is gone permanently.
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

_(Nothing completed yet — entries get added here as each step finishes.)_

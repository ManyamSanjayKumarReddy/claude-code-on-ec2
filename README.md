# claude-code-on-ec2

A small full-stack store app — FastAPI + Postgres backend, React frontend —
containerized with Docker Compose and deployed on a single EC2 instance
behind Nginx with a real Let's Encrypt HTTPS certificate.

Live at: https://claude-on-ec2.theskilledguru.com

For local setup and deployment steps, see [GUIDE.md](./GUIDE.md).

## Features

- **Product catalog CRUD** — add, edit, and delete products (name,
  description, price, stock quantity) through a REST API and a matching UI
- **Persistent storage** — Postgres, with schema changes tracked as Aerich
  migrations (applied automatically on container start, not run by hand)
- **Clean UI** — React + Tailwind CSS v4 + shadcn/ui (Nova/Geist preset):
  product grid, add/edit dialog, delete confirmation, loading/empty/error
  states
- **HTTPS by default** — Nginx reverse proxy terminates TLS with a
  Let's Encrypt certificate that renews itself automatically every 12 hours
- **One command to run anywhere** — the entire stack (frontend, backend,
  database, reverse proxy, cert renewal) comes up with a single
  `docker compose up`, identically on a laptop or on the EC2 instance

## Architecture

```
Browser --> Nginx (web service, ports 80/443, TLS termination)
              |-- /            -> static React build (Vite)
              |-- /api/*       -> FastAPI (backend service, internal port 8000)
                                     |
                                     -- Postgres (db service, internal only)
```

Only `web` is exposed to the internet. `backend` and `db` are only reachable
from other services on the Docker Compose network.

## Tech stack

| Layer          | Choice                                   |
|----------------|-------------------------------------------|
| Frontend       | React, TypeScript, Vite, Tailwind CSS v4, shadcn/ui |
| Backend        | FastAPI, Tortoise ORM, Aerich (migrations) |
| Database       | PostgreSQL                                |
| Reverse proxy  | Nginx                                     |
| TLS            | Let's Encrypt via Certbot                 |
| Orchestration  | Docker Compose                            |

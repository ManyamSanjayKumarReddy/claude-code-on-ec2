# claude-code-on-ec2

A minimal FastAPI + React full-stack app, containerized with Docker Compose,
served behind Nginx, deployed on a single EC2 instance.

## Architecture

```
Browser --> Nginx (web service, ports 80/443)
              |-- /            -> static React build (Vite)
              |-- /api/*       -> FastAPI (backend service, internal port 8000)
```

Only the `web` service is exposed to the internet. `backend` is only reachable
from `web` over the Docker Compose network.

## Local run

```bash
cp .env.example .env   # adjust values if needed
docker compose up -d --build
```

- App: http://localhost/
- API health: http://localhost/api/health

## Project layout

- `backend/` - FastAPI app (`app/main.py`), Dockerfile
- `frontend/` - React + Vite + TypeScript app, Dockerfile builds it and serves
  it via Nginx, `frontend/nginx/` holds the Nginx reverse-proxy config
- `docker-compose.yml` - the two services above

## Deploying to a fresh EC2 instance

See deployment notes (added as we go) for:
1. Security group rules (22, 80, 443)
2. Installing Docker + Compose plugin
3. Pointing DNS at the instance
4. Issuing a Let's Encrypt certificate with Certbot

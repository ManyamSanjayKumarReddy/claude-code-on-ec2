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
- `docker-compose.yml` - `backend`, `web` (Nginx + static build), and `certbot`
  (renews the TLS cert every 12h)
- `certbot/` - Let's Encrypt account/cert data (`conf/`) and the ACME
  HTTP-01 challenge webroot (`www/`); both are git-ignored, generated at runtime

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
   cp .env.example .env   # set ALLOWED_ORIGINS to your real domain
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

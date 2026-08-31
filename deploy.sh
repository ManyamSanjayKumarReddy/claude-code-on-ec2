#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"

git pull --ff-only origin main
docker compose pull backend web
docker compose up -d

#!/bin/bash
# Dumps the Postgres database, compresses it, and uploads it to the
# Cloudflare R2 bucket configured in .env. Meant to run on a schedule (cron)
# on the EC2 instance itself, alongside the running Docker Compose stack.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
AWS_CLI="/home/claudeuser/.local/bin/aws"

cd "$REPO_DIR"
set -a
source .env
set +a

TIMESTAMP="$(date -u +%Y%m%d-%H%M%S)"
DUMP_FILE="/tmp/${POSTGRES_DB}-${TIMESTAMP}.sql.gz"

echo "[$(date -u +%FT%TZ)] Starting backup: ${DUMP_FILE}"

docker compose exec -T db pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" | gzip > "$DUMP_FILE"

AWS_ACCESS_KEY_ID="$R2_ACCESS_KEY_ID" \
AWS_SECRET_ACCESS_KEY="$R2_SECRET_ACCESS_KEY" \
"$AWS_CLI" s3 cp "$DUMP_FILE" "s3://${R2_BUCKET}/$(basename "$DUMP_FILE")" \
  --endpoint-url "$R2_ENDPOINT_URL" --region auto

rm -f "$DUMP_FILE"

echo "[$(date -u +%FT%TZ)] Backup uploaded: $(basename "$DUMP_FILE")"

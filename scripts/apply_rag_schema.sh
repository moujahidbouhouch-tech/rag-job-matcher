#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$ROOT_DIR/.env"

# Load .env if present
if [[ -f "$ENV_FILE" ]]; then
  set -o allexport
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +o allexport
fi

HOST="${DB_POSTGRESDB_HOST:-${POSTGRES_HOST_RAG:-${POSTGRES_HOST:-localhost}}}"
PORT="${DB_POSTGRESDB_PORT:-${POSTGRES_PORT_RAG:-${POSTGRES_PORT:-5433}}}"
DB="${DB_POSTGRESDB_DATABASE:-${POSTGRES_DB_RAG:-${POSTGRES_DB:-rag}}}"
USER="${DB_POSTGRESDB_USER:-${POSTGRES_USER_RAG:-${POSTGRES_USER:-rag}}}"
PASS="${DB_POSTGRESDB_PASSWORD:-${POSTGRES_PASSWORD_RAG:-${POSTGRES_PASSWORD:-}}}"

export PGPASSWORD="${PASS}"

echo "[apply_rag_schema] Using host=${HOST} port=${PORT} db=${DB} user=${USER}"
psql -h "${HOST}" -p "${PORT}" -U "${USER}" -d "${DB}" -f "${ROOT_DIR}/scripts/rag_schema.sql"

echo "[apply_rag_schema] Schema applied."

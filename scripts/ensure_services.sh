#!/usr/bin/env bash
# Ensure required services (Postgres, n8n; optional Ollama/models) are up for app/tests.
# Respects envs: OLLAMA_HOST, OLLAMA_HEALTHCHECK_PATH, OLLAMA_HEALTH_TIMEOUT_SECONDS,
# OLLAMA_MODELS, POSTGRES_*_RAG (via docker-compose.yml), SUDO_ADMIN_PW for restarting ollama.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE="docker compose"
TIMEOUT_SECONDS=300

log() { echo "[$(date +%H:%M:%S)] $*"; }
info() { log "[INFO] $*"; }
err() { log "[ERROR] $*" >&2; }

usage() {
  cat <<EOF
Usage: $(basename "$0") [all|db|n8n|ollama|models|diag]
  all     (default) ensure Postgres (n8n-db) + rag-db + n8n, ensure Ollama, pull/warm models
  db      ensure Postgres (n8n-db) + rag-db only
  n8n     ensure Postgres (n8n-db) + rag-db + n8n
  ollama  ensure Ollama running (no model pulls)
  models  assume Ollama running; pull required models and warm up
  diag    run system_check.sh if present (no changes)
EOF
}

check_docker() {
  if ! command -v docker >/dev/null 2>&1; then
    err "docker not available"
    exit 1
  fi
}

wait_for_health() {
  local svc="$1"
  local start_ts=$2
  while true; do
    local now
    now=$(date +%s)
    if (( now - start_ts > TIMEOUT_SECONDS )); then
      err "Timeout waiting for ${svc} to become healthy"
      exit 1
    fi

    local cid
    cid=$($COMPOSE -f "$ROOT_DIR/docker-compose.yml" ps -q "$svc" || true)
    if [[ -z "$cid" ]]; then
      sleep 2
      continue
    fi

    local health
    health=$(docker inspect --format='{{.State.Health.Status}}' "$cid" 2>/dev/null || echo "unknown")
    if [[ "$health" == "healthy" || "$health" == "none" ]]; then
      info "$svc is ready (health: $health)"
      break
    fi
    info "Waiting for $svc (health: $health)..."
    sleep 2
  done
}

ensure_containers() {
  local start_ts
  start_ts=$(date +%s)
  local services=("$@")
  check_docker
  info "Starting services: ${services[*]}"
  $COMPOSE -f "$ROOT_DIR/docker-compose.yml" up -d "${services[@]}"
  for svc in "${services[@]}"; do
    wait_for_health "$svc" "$start_ts"
  done
}

wait_for_ollama() {
  local host="${OLLAMA_HOST:-http://127.0.0.1:11434}"
  local health="${OLLAMA_HEALTHCHECK_PATH:-/api/tags}"
  local health_timeout="${OLLAMA_HEALTH_TIMEOUT_SECONDS:-5}"
  local start_ts
  start_ts=$(date +%s)
  while true; do
    if curl -sf --max-time "${health_timeout}" "${host}${health}" >/dev/null; then
      info "Ollama reachable at ${host}"
      return 0
    fi
    if (( $(date +%s) - start_ts > TIMEOUT_SECONDS )); then
      err "Timeout waiting for Ollama at ${host}"
      return 1
    fi
    sleep 2
  done
}

start_ollama_with_fallback() {
  local host="${OLLAMA_HOST:-http://127.0.0.1:11434}"
  if pgrep -x "ollama" >/dev/null 2>&1; then
    info "Ollama already running"
    return 0
  fi
  if ! command -v ollama >/dev/null 2>&1; then
    err "ollama CLI not found"
    return 1
  fi

  info "Starting ollama serve..."
  (nohup ollama serve >/tmp/ollama.log 2>&1 &)
  sleep 2
  if wait_for_ollama; then
    return 0
  fi

  info "Ollama failed to start; attempting fallback"
  if [[ -n "${SUDO_ADMIN_PW:-}" ]]; then
    echo "$SUDO_ADMIN_PW" | sudo -S systemctl stop ollama >/dev/null 2>&1 || true
    info "Retrying ollama serve after systemctl stop"
    (nohup ollama serve >/tmp/ollama.log 2>&1 &)
    sleep 2
    if wait_for_ollama; then
      return 0
    fi
  else
    err "Ollama failed to start; run 'sudo systemctl stop ollama' manually and then rerun this script."
  fi
  err "Ollama not reachable at ${host}"
  return 1
}

ensure_ollama_running() {
  start_ollama_with_fallback
}

ensure_models() {
  local host="${OLLAMA_HOST:-http://127.0.0.1:11434}"
  local required_models=${OLLAMA_MODELS:-"llama3.1:8b-instruct-q8_0 llama3.1:8b qwen2.5:1.5b-instruct"}
  local health_timeout="${OLLAMA_HEALTH_TIMEOUT_SECONDS:-5}"
  if ! command -v ollama >/dev/null 2>&1; then
    err "ollama CLI not found"
    return 1
  fi
  for model in $required_models; do
    if ! curl -sf --max-time "${health_timeout}" "${host}/api/tags" | grep -q "\"name\":\"${model}\""; then
      info "Pulling Ollama model: ${model}"
      if ! ollama pull "${model}" >/tmp/ollama_pull.log 2>&1; then
        err "Failed to pull ${model}; see /tmp/ollama_pull.log"
        return 1
      fi
    else
      info "Model ${model} already present"
    fi
  done

  local primary_model
  primary_model=$(echo "$required_models" | awk '{print $1}')
  if [[ -n "$primary_model" ]]; then
    info "Warming up Ollama model: ${primary_model}"
    curl -sf --max-time 10 -X POST "${host}/api/generate" \
      -d "{\"model\":\"${primary_model}\",\"prompt\":\"hi\",\"stream\":false,\"options\":{\"num_predict\":4}}" \
      >/tmp/ollama_warmup.log 2>&1 || info "Warmup request failed; see /tmp/ollama_warmup.log"
  fi
}

run_diag() {
  if [[ -x "$ROOT_DIR/system_check.sh" ]]; then
    "$ROOT_DIR/system_check.sh"
  else
    err "system_check.sh not found at $ROOT_DIR"
  fi
}

cmd="${1:-all}"

case "$cmd" in
  -h|--help)
    usage
    ;;
  ""|"all")
    ensure_containers postgres rag-postgres n8n
    if ensure_ollama_running && wait_for_ollama; then
      ensure_models
    fi
    info "All required services are up."
    ;;
  "db")
    ensure_containers postgres rag-postgres
    info "Postgres (n8n-db) and rag-db are up."
    ;;
  "n8n")
    ensure_containers postgres rag-postgres n8n
    info "Postgres (n8n-db), rag-db, and n8n are up."
    ;;
  "ollama")
    if ensure_ollama_running && wait_for_ollama; then
      info "Ollama is up."
    else
      exit 1
    fi
    ;;
  "models")
    if wait_for_ollama; then
      ensure_models
    else
      exit 1
    fi
    ;;
  "diag")
    run_diag
    ;;
  *)
    err "Unknown command: $cmd"
    usage
    exit 1
    ;;
esac

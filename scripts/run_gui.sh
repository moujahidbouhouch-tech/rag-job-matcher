#!/usr/bin/env bash
# Launch the ingestion GUI with the repo's virtualenv activated.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${ROOT_DIR}/.venv"

if [[ ! -d "$VENV_DIR" ]]; then
  echo "Virtualenv not found at $VENV_DIR. Create it first (e.g., python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt)." >&2
  exit 1
fi

source "${VENV_DIR}/bin/activate"
cd "$ROOT_DIR"
"${VENV_DIR}/bin/python" -m rag_project.rag_gui.main

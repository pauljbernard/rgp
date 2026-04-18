#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../apps/api"
source .venv/bin/activate
export RGP_DATABASE_URL="${RGP_DATABASE_URL:-postgresql+psycopg://rgp:rgp@localhost:5432/rgp}"
uvicorn app.transport:get_asgi_app --factory --reload --host 0.0.0.0 --port 8000

#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
pnpm --filter @rgp/web dev

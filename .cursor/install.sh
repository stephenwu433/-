#!/usr/bin/env bash
# Idempotent Cloud Agent bootstrap for the `ban` repository.
#
# This repository currently holds only planning/specification documents
# (Excel, PDF, Word) for the "梅见 AI 市场决策系统". There is no application
# source yet, so the environment provides a Python virtualenv with the
# libraries needed to read and process those source documents.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# `python3 -m venv` needs ensurepip, which is not in the default image.
if ! python3 -c "import ensurepip" >/dev/null 2>&1; then
  sudo apt-get update -qq
  sudo apt-get install -y -qq python3-venv
fi

if [ ! -x ".venv/bin/python" ]; then
  python3 -m venv .venv
fi

# shellcheck disable=SC1091
. .venv/bin/activate
python -m pip install --upgrade pip >/dev/null
python -m pip install -r .cursor/requirements.txt

echo "Environment ready. Activate with: source .venv/bin/activate"

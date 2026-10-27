#!/bin/bash
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
VENV="${LOCAL_GROUNDING_VENV:-$HOME/.local/share/local-grounding-mcp/venv}"
PYTHON="${PYTHON:-python3.11}"
command -v "$PYTHON" >/dev/null || { echo "Python 3.11 is required."; exit 1; }
mkdir -p "$(dirname "$VENV")" "$HOME/.local/bin"
"$PYTHON" -m venv "$VENV"
"$VENV/bin/python" -m pip install --upgrade pip
"$VENV/bin/python" -m pip install "$REPO"
for cmd in local-grounding-mcp local-grounding-service local-grounding-doctor local-grounding-status local-grounding-stop local-grounding-metrics; do
  ln -sf "$VENV/bin/$cmd" "$HOME/.local/bin/$cmd"
done
echo "Installed to $VENV"
echo "Run: local-grounding-doctor"
echo "MCP examples: $REPO/examples/"

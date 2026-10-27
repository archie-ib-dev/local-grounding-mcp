#!/bin/bash
set -euo pipefail
VENV="${LOCAL_GROUNDING_VENV:-$HOME/.local/share/local-grounding-mcp/venv}"
for cmd in local-grounding-mcp local-grounding-service local-grounding-doctor local-grounding-status local-grounding-stop local-grounding-metrics local-grounding-config; do rm -f "$HOME/.local/bin/$cmd"; done
rm -rf "$VENV"
echo "Removed commands and virtual environment. Model, logs, metrics, and client configs were preserved."

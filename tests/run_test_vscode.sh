#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
"$SCRIPT_DIR/../gfxlaunch" --vgl --group ondemand --title "VS Code" --cmd /sw/pkg/ondemand-dt/run/vscode.sh

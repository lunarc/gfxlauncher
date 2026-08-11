#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
"$SCRIPT_DIR/../gfxlaunch" --vgl --group ondemand --title "ParaView 5.11.1" --cmd /sw/pkg/ondemand-dt/run/paraview-5.11.1.sh

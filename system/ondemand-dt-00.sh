#/bin/bash

export ONDEMAND_DT_DIR=/sw/pkg/gfxlauncher
export PATH=${ONDEMAND_DT_DIR}:$PATH

# Generate user menu

gfxmenu --silent &>/dev/null

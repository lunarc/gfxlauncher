#/bin/sh

export ONDEMAND_DT_INSTALL=/sw/pkg/gfxlauncher
export PATH=${ONDEMAND_DT_INSTALL}:$PATH

gfxmenu 2>&1

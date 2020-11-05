#!/bin/bash 
/sw/pkg/freerdp/2.0.0-rc4/bin/xfreerdp /v:10.18.50.22 /u:$USER /d:ad.lunarc /sec:tls /audio-mode:1 /gfx +gfx-progressive -bitmap-cache -offscreen-cache 
-glyph-cache +clipboard -themes -wallpaper /size:1280x1024 /dynamic-resolution /kbd:0x41D /kbd-type:pc105 /t:"LUNARC HPC Desktop Windows 10 (NVIDA V100)"

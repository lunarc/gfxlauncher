#!/bin/sh

rdp_P=/sw/pkg/freerdp/2.0.0-rc4/bin

$rdp_P/xfreerdp /v:10.18.50.22 /u:anfo /d:ad.lunarc /sec:tls /cert-ignore /audio-mode:1 /gfx +gfx-progressive -bitmap-cache -offscreen-cache -glyph-cache +clipboard -themes -wallpaper /size:1280x1024 /dynamic-resolution /t:"LUNARC HPC Desktop Windows 10 (NVIDA V100)"


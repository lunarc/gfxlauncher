#!/bin/sh

##LDT category = "Volume Rendering"
##LDT title = "VivoQuant 3.5"
##LDT group = "ondemand"
vgl_P=/opt/VirtualGL/bin
app_P=/sw/pkg/vivoquant/vivoquant-linux-3.5patch2

mkdir $HOME/.VivoQuant
cp /sw/pkg/vivoquant/licenses/vq-license--eg17-eg24.txt $HOME/.VivoQuant/licensekey.txt

$vgl_P/vglrun $app_P/vivoquant

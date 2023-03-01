#!/bin/sh

##LDT category = "Post Processing"
##LDT title = "VMD 1.9.2"
##LDT group = "ondemand"
vgl_P=/opt/VirtualGL/bin
app_P=/sw/pkg/vmd/1.9.2/bin

$vgl_P/vglrun xterm -e "$app_P/vmd"

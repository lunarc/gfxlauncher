#!/bin/sh

##LDT category = "3D Modeling"
##LDT title = "Blender 3.1.0 (Terminal)"
##LDT group = "ondemand"
vgl_P=/opt/VirtualGL/bin
app_P=/sw/pkg/blender/3.1.0

$vgl_P/vglrun xterm -e "$app_P/blender"

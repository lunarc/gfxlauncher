#!/bin/sh

##LDT category = "CAE"
##LDT title = "Abaqus/CAE 6.13-5"
##LDT group = "ondemand"
vgl_P=/opt/VirtualGL/bin
app_P=

module load abaqus/6.21-6

export XLIB_SKIP_ARGB_VISUALS=1

$vgl_P/vglrun abaqus cae

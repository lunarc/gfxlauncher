#!/bin/sh

##LDT category = "CAE"
##LDT title = "Abaqus/CAE V6R2019"
##LDT group = "ondemand"
##LDT version = "6.13-5"

vgl_P=/opt/VirtualGL/bin
app_P=

module load abaqus/V6R2019x

export XLIB_SKIP_ARGB_VISUALS=1

$vgl_P/vglrun abaqus cae

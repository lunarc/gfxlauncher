#!/bin/sh

##LDT category = "CAE"
##LDT title = "Abaqus/CAE 6.13-5"
##LDT group = "ondemand"
##LDT version = "6.13-5"
vgl_P=/opt/VirtualGL/bin
app_P=

module load icc/2015.3.187-GNU-4.9.3-2.25
module load ifort/2015.3.187-GNU-4.9.3-2.25
module load abaqus/6.13-5

export XLIB_SKIP_ARGB_VISUALS=1

$vgl_P/vglrun abaqus cae

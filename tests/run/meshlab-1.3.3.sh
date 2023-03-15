#!/bin/sh

##LDT category = "3D Modeling"
##LDT title = "Meshlab 1.3.3"
##LDT group = "ondemand"

vgl_P=/opt/VirtualGL/bin
app_P=/sw/pkg/meshlab/1.3.3/distrib

export LD_LIBRARY_PATH=$app_P

$vgl_P/vglrun $app_P/meshlab

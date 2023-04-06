#!/bin/sh

##LDT category = "3D Modeling"
##LDT title = "MetaShape 1.6.2"
##LDT group = "ondemand"
vgl_P=/opt/VirtualGL/bin
app_P=/sw/pkg/metashape/1.6.2/metashape-pro

module load metashape/1.6.2

$vgl_P/vglrun $app_P/metashape.sh

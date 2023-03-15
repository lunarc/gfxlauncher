#!/bin/sh

##LDT category = "3D Modeling"
##LDT title = "MetaShape 1.8.4"
##LDT group = "metashape184"
vgl_P=/opt/VirtualGL/bin
app_P=/sw/pkg/metashape/1.8.4/metashape-pro

module load metashape/1.8.4

$vgl_P/vglrun $app_P/metashape.sh

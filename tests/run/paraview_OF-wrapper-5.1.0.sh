#!/bin/sh

##LDT category = "Post Processing"
##LDT title = "ParaView 5.1.0 - OpenFOAM"
##LDT group = "ondemand"
vgl_P=/opt/VirtualGL/bin/latest
app_P=/sw/pkg/paraview/5.1.0/bin

$vgl_P/vglrun $app_P/paraview $1

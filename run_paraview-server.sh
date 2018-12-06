#!/bin/sh

##LDT category = "Post Processing"
##LDT title = "ParaView 5.4.1"

vgl_P=/sw/pkg/rviz/vgl/bin/latest
app_P=/sw/pkg/paraview/5.4.1/bin

ml foss/2018b
ml Mesa

export GALLIUM_DRIVER=swr

$vgl_P/vglrun $app_P/paraview

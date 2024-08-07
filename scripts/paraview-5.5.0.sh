#!/bin/sh

##LDT category = "Post Processing"
##LDT title = "ParaView 5.5.0 (swr)"
##LDT part = "snic"
##LDT group = "ondemand"
vgl_P=/opt/VirtualGL/bin
app_P=/sw/pkg/paraview/5.5.0/bin

$vgl_P/vglrun $app_P/paraview

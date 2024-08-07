#!/bin/bash

##LDT category = "3D Modeling"
##LDT title = "Meshlab 2021.10"
##LDT group = "ondemand"
vgl_P=/opt/VirtualGL/bin
app_P=/sw/pkg/meshlab/2021/bin

module load meshlab/2021.10
$vgl_P/vglrun $app_P/meshlab

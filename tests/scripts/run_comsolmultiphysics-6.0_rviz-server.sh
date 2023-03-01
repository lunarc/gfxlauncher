#!/bin/sh

##LDT category = "Comsol"
##LDT title = "Comsol Multiphysic 6.0"
##LDT group = "ondemand"

vgl_P=/opt/VirtualGL/bin
app_P=


module load comsol/6.0 

$vgl_P/vglrun comsol &

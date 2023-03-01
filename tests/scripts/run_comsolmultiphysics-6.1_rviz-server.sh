#!/bin/sh

##LDT category = "Comsol"
##LDT title = "Comsol Multiphysic 6.1"
##LDT group = "ondemand"

vgl_P=/opt/VirtualGL/bin
app_P=


module load comsol/6.1 

$vgl_P/vglrun comsol &

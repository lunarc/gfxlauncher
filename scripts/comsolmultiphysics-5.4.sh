#!/bin/sh

##LDT category = "Comsol"
##LDT title = "Comsol Multiphysic 5.4"
##LDT group = "ondemand"

vgl_P=/opt/VirtualGL/bin
app_P=


module load comsol/5.4 

$vgl_P/vglrun comsol &

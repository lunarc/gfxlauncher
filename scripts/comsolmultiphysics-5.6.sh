#!/bin/sh

##LDT category = "Comsol"
##LDT title = "Comsol Multiphysic 5.6"
##LDT group = "ondemand"

vgl_P=/opt/VirtualGL/bin
app_P=


module load comsol/5.6 

$vgl_P/vglrun comsol &

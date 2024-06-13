#!/bin/sh

##LDT category = "Comsol"
##LDT title = "Comsol Multiphysics 5.3"
##LDT group = "ondemand"

vgl_P=/opt/VirtualGL/bin
app_P=


module load comsol/5.2 

$vgl_P/vglrun comsol & 

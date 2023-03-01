#!/bin/sh

##LDT category = "Volume Rendering"
##LDT title = "Tomviz 1.5"
##LDT group = "ondemand"
vgl_P=/opt/VirtualGL/bin
app_P=

#ml foss/2018b
module load GCC/7.3.0-2.30
module load OpenMPI/3.1.1
ml Tomviz

$vgl_P/vglrun tomviz

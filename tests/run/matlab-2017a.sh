#!/bin/sh

##LDT category = "Matlab"
##LDT title = "Matlab 2017a"
##LDT group = "ondemand"
vgl_P=/opt/VirtualGL/bin
app_P=

module load GCC/4.9.3
module load matlab/2017a

$vgl_P/vglrun matlab -desktop -nosoftwareopengl

#!/bin/sh

##LDT category = "Matlab"
##LDT title = "Matlab 8.7"
##LDT group = "ondemand"
vgl_P=/opt/VirtualGL/bin
app_P=


module load matlab/8.7 

$vgl_P/vglrun matlab -desktop -nosoftwareopengl

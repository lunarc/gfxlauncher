#!/bin/sh

##LDT category = "Matlab"
##LDT title = "Matlab 2020a"
##LDT group = "ondemand"
vgl_P=/opt/VirtualGL/bin
app_P=


module load matlab/2020a


$vgl_P/vglrun matlab -desktop -nosoftwareopengl

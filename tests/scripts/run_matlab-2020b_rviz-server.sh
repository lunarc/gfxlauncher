#!/bin/sh

##LDT category = "Matlab"
##LDT title = "Matlab 2020b"
##LDT group = "ondemand"
vgl_P=/opt/VirtualGL/bin
app_P=


module load matlab/2020b


$vgl_P/vglrun matlab -desktop -nosoftwareopengl

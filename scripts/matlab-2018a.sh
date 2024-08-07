#!/bin/sh

##LDT category = "Matlab"
##LDT title = "Matlab 2018a"
##LDT group = "ondemand"
vgl_P=/opt/VirtualGL/bin
app_P=

module load GCC/6.4.0-2.28
module load CUDA/9.1.85
module load matlab/2018a

$vgl_P/vglrun matlab -desktop -nosoftwareopengl

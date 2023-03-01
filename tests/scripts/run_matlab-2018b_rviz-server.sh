#!/bin/sh

##LDT category = "Matlab"
##LDT title = "Matlab 2018b"
##LDT group = "ondemand"
vgl_P=/opt/VirtualGL/bin
app_P=


ml add GCC/6.3.0-2.27 
ml add CUDA/9.1.85
module load matlab/2018b


$vgl_P/vglrun matlab -desktop -nosoftwareopengl

#!/bin/sh

##LDT category = "Medical Imaging"
##LDT title = "FreeSurfer 5.3.0"
##LDT group = "ondemand"
vgl_P=/opt/VirtualGL/bin
app_P=


module load FreeSurfer/5.3.0-centos4_x86_64

$vgl_P/vglrun freeview

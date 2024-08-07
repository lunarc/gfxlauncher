#!/bin/sh

##LDT category = "Medical Imaging"
##LDT title = "FreeSurfer 6.0.0"
##LDT group = "ondemand"

vgl_P=/opt/VirtualGL/bin
app_P=


module load FreeSurfer/6.0.0-centos6_x86_64

$vgl_P/vglrun freeview

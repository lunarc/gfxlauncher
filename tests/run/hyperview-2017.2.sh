#!/bin/sh

##LDT category = "CAE"
##LDT title = "HyperView 2017.2"
##LDT group = "ondemand"
vgl_P=/opt/VirtualGL/bin
app_P=


module load altair/HYPERWORKS 

#$vgl_P/vglrun hv &
$vgl_P/vglrun hmdesktop &

#!/bin/sh

##LDT category = "Post Processing"
##LDT title = "LS PrePost 4.3"
##LDT group = "ondemand"
vgl_P=/opt/VirtualGL/bin
app_P=


module load foss/2016b 
module load libpng
module load lsprepost/4.3_leap42 

$vgl_P/vglrun lsprepost

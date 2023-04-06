#!/bin/sh

##LDT category = "3D Modeling"
##LDT title = "PhotoScan 1.4.2"
##LDT group = "ondemand"
vgl_P=/opt/VirtualGL/bin

module load photoscan/1.4.2

$vgl_P/vglrun photoscan.sh

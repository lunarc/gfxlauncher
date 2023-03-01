#!/bin/sh

##LDT category = "CAE"
##LDT title = "Ansys 16.0"
##LDT group = "ondemand"
vgl_P=/opt/VirtualGL/bin
app_P=/sw/pkg/ansys/16.0/ansys_inc/v160/Framework/bin/Linux64/

module add ansys/16.0
$vgl_P/vglrun runwb2&

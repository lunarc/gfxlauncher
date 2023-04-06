#!/bin/sh

##LDT category = "CAE"
##LDT title = "Ansys 20.1"
##LDT group = "ondemand"
vgl_P=/opt/VirtualGL/bin
app_P=/sw/pkg/ansys/20.1/ansys_inc/v201/Framework/bin/Linux64/

module add ansys/20.1
$vgl_P/vglrun runwb2&

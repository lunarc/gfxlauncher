#!/bin/sh

##LDT category = "CAE"
##LDT title = "Ansys 19.3"
##LDT group = "ondemand"
vgl_P=/opt/VirtualGL/bin
app_P=/sw/pkg/ansys/19.3/ansys_inc/v193/Framework/bin/Linux64/

module add ansys/19.3
$vgl_P/vglrun runwb2&

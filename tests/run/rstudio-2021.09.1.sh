#!/bin/sh

##LDT category = "Development"
##LDT title = "Rstudio 2021.09.1"
##LDT group = "ondemand"
vgl_P=/opt/VirtualGL/bin
app_P=/sw/pkg/rstudio/2021.09.1-372/bin

ml rstudio/2021.09.1
$vgl_P/vglrun $app_P/rstudio


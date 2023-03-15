#!/bin/sh

##LDT category = "Development"
##LDT title = "Rstudio 1.2.5019"
##LDT group = "ondemand"
vgl_P=/opt/VirtualGL/bin
app_P=/sw/pkg/rstudio/1.2.5019/bin

ml rstudio/1.2.5019
$vgl_P/vglrun $app_P/rstudio


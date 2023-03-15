#!/bin/sh

##LDT category = "Development"
##LDT title = "Rstudio 2021.09.1 (CPU)"
##LDT part = "lu"
##LDT vgl = "no"
##LDT group = "cpu"
vgl_P=/opt/VirtualGL/bin
app_P=/sw/pkg/rstudio/2021.09.1-372/bin

ml rstudio/2021.09.1
$app_P/rstudio


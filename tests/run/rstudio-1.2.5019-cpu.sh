#!/bin/sh

##LDT category = "Development"
##LDT title = "Rstudio 1.2.5019 (CPU)"
##LDT part = "lu"
##LDT vgl = "no"
##LDT group = "cpu"
vgl_P=/opt/VirtualGL/bin
app_P=/sw/pkg/rstudio/1.2.5019/bin

ml rstudio/1.2.5019
$app_P/rstudio


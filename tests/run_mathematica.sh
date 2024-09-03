#!/bin/sh

##LDT category = "Mathematica"
##LDT title = "Mathematica 14.0.0 (CPU)"
###LDT part = "lu"
##LDT vgl = "no"
##LDT group = "mathem"
##LDT feature_disable = "yes"
###LDT part_disable = "yes"

vgl_P=/opt/VirtualGL/bin
app_P=/sw/easybuild_milan/software/Mathematica/14.0.0/Executables

ml Mathematica/14.0.0
$app_P/mathematica


#!/bin/sh

##LDT category = "Development"
##LDT title = "VS Code"
##LDT group = "ondemand"
##LDT vgl = "yes"
vgl_P=/opt/VirtualGL/bin

module load vscode

$vgl_P/vglrun code

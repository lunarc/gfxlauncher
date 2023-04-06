#!/bin/sh

##LDT category = "Development"
##LDT title = "Qt Creator 4.12.3"
##LDT group = "ondemand"
vgl_P=/opt/VirtualGL/bin

module load GCC
module load CMake
module load qtcreator/4.12.3
export CMAKE_CXX_COMPILER=`which g++`
export CMAKE_C_COMPILER=`which gcc`
CMAKE_CXX_COMPILER=`which g++` qtcreator
$vgl_P/vglrun /sw/pkg/qtcreator/4.12.3/bin/qtcreator

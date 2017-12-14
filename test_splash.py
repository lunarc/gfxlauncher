#!/bin/env python

import os
import sys

from PyQt4 import QtGui

# --- Version information

gfxlaunch_version = "0.1"

# --- Fix search path for tool

tool_path = os.path.dirname(os.path.abspath(sys.argv[0]))
sys.path.append(tool_path)

import lhpcdt.launcher


if __name__ == '__main__':

    # Show version information

    print("LUNARC HPC Desktop - Graphical Application Launcher - Version %s" % gfxlaunch_version)
    print("Written by Jonas Lindemann (jonas.lindemann@lunarc.lu.se)")
    print("Copyright (C) 2017 LUNARC, Lund University")
    print()

    launchSettings = lhpcdt.settings.LaunchSettings.create()
    launchSettings.tool_path = tool_path

    app = QtGui.QApplication(sys.argv)
    app.setStyle("GTK+")

    # Show user interface

    splashWindow = lhpcdt.launcher.SplashWindow()
    splashWindow.show()

    # Start main application loop

    sys.exit(app.exec_())

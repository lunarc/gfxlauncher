#!/bin/env python

import os, sys, argparse

from queue import Queue
from PyQt5 import QtCore, QtGui, QtWidgets

# --- Version information

gfxlaunch_copyright = """LUNARC HPC Desktop On-Demand - Version %s
Copyright (C) 2017-2019 LUNARC, Lund University
"""
gfxlaunch_copyright_short = """LUNARC HPC Desktop On-Demand - %s"""
gfxlaunch_version = "0.5-beta"

# --- Fix search path for tool

tool_path = os.path.dirname(os.path.abspath(sys.argv[0]))
sys.path.append(tool_path)

print(tool_path)

from lhpcdt import *

def create_dark_palette():
    """Create a dark palette"""
    darkPalette = QtGui.QPalette()
    darkPalette.setColor(QtGui.QPalette.Window, QtGui.QColor(53,53,53))
    darkPalette.setColor(QtGui.QPalette.WindowText,QtCore.Qt.white);
    darkPalette.setColor(QtGui.QPalette.Disabled,QtGui.QPalette.WindowText,QtGui.QColor(127,127,127));
    darkPalette.setColor(QtGui.QPalette.Base,QtGui.QColor(42,42,42));
    darkPalette.setColor(QtGui.QPalette.AlternateBase,QtGui.QColor(66,66,66));
    darkPalette.setColor(QtGui.QPalette.ToolTipBase,QtCore.Qt.white);
    darkPalette.setColor(QtGui.QPalette.ToolTipText,QtCore.Qt.white);
    darkPalette.setColor(QtGui.QPalette.Text,QtCore.Qt.white);
    darkPalette.setColor(QtGui.QPalette.Disabled,QtGui.QPalette.Text,QtGui.QColor(127,127,127));
    darkPalette.setColor(QtGui.QPalette.Dark,QtGui.QColor(35,35,35));
    darkPalette.setColor(QtGui.QPalette.Shadow,QtGui.QColor(20,20,20));
    darkPalette.setColor(QtGui.QPalette.Button,QtGui.QColor(53,53,53));
    darkPalette.setColor(QtGui.QPalette.ButtonText,QtCore.Qt.white);
    darkPalette.setColor(QtGui.QPalette.Disabled,QtGui.QPalette.ButtonText,QtGui.QColor(127,127,127));
    darkPalette.setColor(QtGui.QPalette.BrightText,QtCore.Qt.red);
    darkPalette.setColor(QtGui.QPalette.Link,QtGui.QColor(42,130,218));
    darkPalette.setColor(QtGui.QPalette.Highlight,QtGui.QColor(42,130,218));
    darkPalette.setColor(QtGui.QPalette.Disabled,QtGui.QPalette.Highlight,QtGui.QColor(80,80,80));
    darkPalette.setColor(QtGui.QPalette.HighlightedText,QtCore.Qt.white);
    darkPalette.setColor(QtGui.QPalette.Disabled,QtGui.QPalette.HighlightedText,QtGui.QColor(127,127,127));

    return darkPalette

def create_light_palette():
    """Create light palette"""
    
    lightPalette = QtGui.QPalette()

    lightPalette.setColor(QtGui.QPalette.Window, QtGui.QColor(212,212,212))
    lightPalette.setColor(QtGui.QPalette.WindowText,QtCore.Qt.black);
    lightPalette.setColor(QtGui.QPalette.Disabled,QtGui.QPalette.WindowText,QtGui.QColor(172,172,172));
    lightPalette.setColor(QtGui.QPalette.Base,QtGui.QColor(255,255,230));
    lightPalette.setColor(QtGui.QPalette.AlternateBase,QtGui.QColor(0,255,0));
    lightPalette.setColor(QtGui.QPalette.ToolTipBase,QtCore.Qt.black);
    lightPalette.setColor(QtGui.QPalette.ToolTipText,QtCore.Qt.black);
    lightPalette.setColor(QtGui.QPalette.Text,QtCore.Qt.black);
    lightPalette.setColor(QtGui.QPalette.Disabled,QtGui.QPalette.Text,QtGui.QColor(128,128,128));
    lightPalette.setColor(QtGui.QPalette.Dark,QtGui.QColor(160,160,160));
    lightPalette.setColor(QtGui.QPalette.Shadow,QtGui.QColor(100,100,100));
    lightPalette.setColor(QtGui.QPalette.Button,QtGui.QColor(212,212,212));
    lightPalette.setColor(QtGui.QPalette.ButtonText,QtCore.Qt.black);
    lightPalette.setColor(QtGui.QPalette.Disabled,QtGui.QPalette.ButtonText,QtGui.QColor(172,172,172));
    lightPalette.setColor(QtGui.QPalette.BrightText,QtCore.Qt.red);
    lightPalette.setColor(QtGui.QPalette.Link,QtGui.QColor(42,130,218));
    lightPalette.setColor(QtGui.QPalette.Highlight,QtGui.QColor(42,130,218));
    lightPalette.setColor(QtGui.QPalette.Disabled,QtGui.QPalette.Highlight,QtGui.QColor(80,80,80));
    lightPalette.setColor(QtGui.QPalette.HighlightedText,QtCore.Qt.white);
    lightPalette.setColor(QtGui.QPalette.Disabled,QtGui.QPalette.HighlightedText,QtGui.QColor(127,127,127));

    return lightPalette

if __name__ == '__main__':

    # Show version information


    print((gfxlaunch_copyright % gfxlaunch_version))
    print("")

    parser = argparse.ArgumentParser(description="Graphical Job Launcher")

    args = parser.parse_args()
    print(args)

    launchSettings = settings.LaunchSettings.create()
    launchSettings.args = args
    launchSettings.tool_path = tool_path
    launchSettings.copyright_info = gfxlaunch_copyright
    launchSettings.copyright_short_info = gfxlaunch_copyright_short
    launchSettings.version_info = gfxlaunch_version

    # User interface 

    dark_mode = False

    # Redirect standard output

    redirect = False

    app = QtWidgets.QApplication(sys.argv)

    if dark_mode:
        palette = create_dark_palette()
    else:
        palette = create_light_palette()
    
    app.setPalette(palette)

    #app.setStyle("gtk2")

    # Show user interface
    
    form = lmod_ui.LmodQueryWindow()
    form.show()

    # Start main application loop

    #app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())

    app.exec_()

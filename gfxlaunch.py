#!/bin/env python

from lhpcdt import *
import os
import sys
import argparse

from queue import Queue
from PyQt5 import QtCore, QtGui, QtWidgets

# --- Version information

gfxlaunch_copyright = """LUNARC HPC Desktop On-Demand - Version %s
Copyright (C) 2017-2020 LUNARC, Lund University
"""
gfxlaunch_copyright_short = """LUNARC HPC Desktop On-Demand - %s"""
gfxlaunch_version = "0.5.4"

# --- Fix search path for tool

tool_path = os.path.dirname(os.path.abspath(sys.argv[0]))
sys.path.append(tool_path)


def create_dark_palette():
    """Create a dark palette"""
    darkPalette = QtGui.QPalette()
    darkPalette.setColor(QtGui.QPalette.Window, QtGui.QColor(53, 53, 53))
    darkPalette.setColor(QtGui.QPalette.WindowText, QtCore.Qt.white)
    darkPalette.setColor(QtGui.QPalette.Disabled,
                         QtGui.QPalette.WindowText, QtGui.QColor(127, 127, 127))
    darkPalette.setColor(QtGui.QPalette.Base, QtGui.QColor(42, 42, 42))
    darkPalette.setColor(QtGui.QPalette.AlternateBase,
                         QtGui.QColor(66, 66, 66))
    darkPalette.setColor(QtGui.QPalette.ToolTipBase, QtCore.Qt.white)
    darkPalette.setColor(QtGui.QPalette.ToolTipText, QtCore.Qt.white)
    darkPalette.setColor(QtGui.QPalette.Text, QtCore.Qt.white)
    darkPalette.setColor(QtGui.QPalette.Disabled,
                         QtGui.QPalette.Text, QtGui.QColor(127, 127, 127))
    darkPalette.setColor(QtGui.QPalette.Dark, QtGui.QColor(35, 35, 35))
    darkPalette.setColor(QtGui.QPalette.Shadow, QtGui.QColor(20, 20, 20))
    darkPalette.setColor(QtGui.QPalette.Button, QtGui.QColor(53, 53, 53))
    darkPalette.setColor(QtGui.QPalette.ButtonText, QtCore.Qt.white)
    darkPalette.setColor(QtGui.QPalette.Disabled,
                         QtGui.QPalette.ButtonText, QtGui.QColor(127, 127, 127))
    darkPalette.setColor(QtGui.QPalette.BrightText, QtCore.Qt.red)
    darkPalette.setColor(QtGui.QPalette.Link, QtGui.QColor(42, 130, 218))
    darkPalette.setColor(QtGui.QPalette.Highlight, QtGui.QColor(42, 130, 218))
    darkPalette.setColor(QtGui.QPalette.Disabled,
                         QtGui.QPalette.Highlight, QtGui.QColor(80, 80, 80))
    darkPalette.setColor(QtGui.QPalette.HighlightedText, QtCore.Qt.white)
    darkPalette.setColor(QtGui.QPalette.Disabled,
                         QtGui.QPalette.HighlightedText, QtGui.QColor(127, 127, 127))

    return darkPalette


def create_light_palette():
    """Create light palette"""

    lightPalette = QtGui.QPalette()

    lightPalette.setColor(QtGui.QPalette.Window, QtGui.QColor(212, 212, 212))
    lightPalette.setColor(QtGui.QPalette.WindowText, QtCore.Qt.black)
    lightPalette.setColor(QtGui.QPalette.Disabled,
                          QtGui.QPalette.WindowText, QtGui.QColor(172, 172, 172))
    lightPalette.setColor(QtGui.QPalette.Base, QtGui.QColor(255, 255, 230))
    lightPalette.setColor(QtGui.QPalette.AlternateBase,
                          QtGui.QColor(0, 255, 0))
    lightPalette.setColor(QtGui.QPalette.ToolTipBase, QtCore.Qt.black)
    lightPalette.setColor(QtGui.QPalette.ToolTipText, QtCore.Qt.black)
    lightPalette.setColor(QtGui.QPalette.Text, QtCore.Qt.black)
    lightPalette.setColor(QtGui.QPalette.Disabled,
                          QtGui.QPalette.Text, QtGui.QColor(128, 128, 128))
    lightPalette.setColor(QtGui.QPalette.Dark, QtGui.QColor(160, 160, 160))
    lightPalette.setColor(QtGui.QPalette.Shadow, QtGui.QColor(100, 100, 100))
    lightPalette.setColor(QtGui.QPalette.Button, QtGui.QColor(212, 212, 212))
    lightPalette.setColor(QtGui.QPalette.ButtonText, QtCore.Qt.black)
    lightPalette.setColor(QtGui.QPalette.Disabled,
                          QtGui.QPalette.ButtonText, QtGui.QColor(172, 172, 172))
    lightPalette.setColor(QtGui.QPalette.BrightText, QtCore.Qt.red)
    lightPalette.setColor(QtGui.QPalette.Link, QtGui.QColor(42, 130, 218))
    lightPalette.setColor(QtGui.QPalette.Highlight, QtGui.QColor(42, 130, 218))
    lightPalette.setColor(QtGui.QPalette.Disabled,
                          QtGui.QPalette.Highlight, QtGui.QColor(80, 80, 80))
    lightPalette.setColor(QtGui.QPalette.HighlightedText, QtCore.Qt.white)
    lightPalette.setColor(QtGui.QPalette.Disabled,
                          QtGui.QPalette.HighlightedText, QtGui.QColor(127, 127, 127))

    return lightPalette


if __name__ == '__main__':

    # Show version information

    print((gfxlaunch_copyright % gfxlaunch_version))
    print("")

    # Parse command line arguments

    parser = argparse.ArgumentParser(description="Graphical Job Launcher")

    parser.add_argument("--simplified", dest="simplified",
                        action="store_true", default=True)
    parser.add_argument("--cmd", dest="cmdLine", action="store", default="", required=False,
                        help="Command line to launch application")

    parser.add_argument("--vgl", dest="useVGL", action="store_true", default=False,
                        help="Use VirtuaGL infrastructure")

    parser.add_argument("--vglrun", dest="use_vglrun", action="store_true", default=False,
                        help="Prefix command with vglrun")

    parser.add_argument("--title", dest="title", action="store", default="Lunarc Job Launcher",
                        help="Window title")

    parser.add_argument("--partition", dest="part", action="store",
                        help="Default partition to use")

    parser.add_argument("--account", dest="account", action="store", default="",
                        help="Default account to use")

    parser.add_argument("--grantfile", dest="grant_filename", action="store", default="",
                        help="Default grantfile to use")

    parser.add_argument("--exclusive", dest="exclusive", action="store_true", default=False,
                        help="Use node exclusively")

    parser.add_argument("--count", dest="count", action="store", default=1,
                        help="Number of cpu:s to use")

    parser.add_argument("--memory", dest="memory", action="store", default=-1,
                        help="Memory in MB to use")

    parser.add_argument("--time", dest="time",
                        action="store", default="00:30:00")

    parser.add_argument("--only-submit", dest="only_submit", action="store_true", default=False,
                        help="Only job submission. No remote execution to node.")

    parser.add_argument("--job", dest="job_type", action="store", default="",
                        help="Submit a specific type of job.")

    parser.add_argument("--name", dest="job_name", action="store",
                        default="lhpc", help="Job name in LRMS.")

    parser.add_argument("--tasks-per-node", dest="tasks_per_node",
                        action="store", default="1", help="Number of tasks per node.")

    parser.add_argument("--cpus-per-task", dest="cpus_per_task",
                        action="store", default="1", help="Number of cpus per task.")

    parser.add_argument("--no-requeue", dest="no_requeue",
                        action="store_true", default=False, help="No requeuing of job.")

    parser.add_argument("--user", dest="user", action="store",
                        default="", help="Use the following user instead of default.")

    parser.add_argument("--ignore-grantfile", dest="ignore_grantfile",
                        action="store_true", default=False, help="Ignore grantfile checking.")

    parser.add_argument("--jupyterlab-module", dest="jupyterlab_module", action="store", 
                        default="Anaconda3", help="Specify module to load for Jupyter Lab jobs.")

    parser.add_argument("--notebook-module", dest="notebook_module", action="store", 
                        default="Anaconda3", help="Specify module to load for Jupyter Notebook jobs.")

    args = parser.parse_args()

    # Setup global settings singleton

    launch_settings = settings.LaunchSettings.create()
    launch_settings.args = args
    launch_settings.tool_path = tool_path
    launch_settings.copyright_info = gfxlaunch_copyright
    launch_settings.copyright_short_info = gfxlaunch_copyright_short
    launch_settings.version_info = gfxlaunch_version

    # User interface

    dark_mode = False

    # Redirect standard output

    redirect = True

    # Create Queue and redirect sys.stdout to this queue

    if redirect:
        queue = Queue()
        sys.stdout = launcher.WriteStream(queue)

    # Create application object

    app = QtWidgets.QApplication(sys.argv)

    if dark_mode:
        palette = create_dark_palette()
    else:
        palette = create_light_palette()

    app.setPalette(palette)

    # app.setStyle("gtk2")

    # Show splash

    splash_window = splash_win.SplashWindow(
        None, gfxlaunch_copyright % gfxlaunch_version)
    splash_window.show()

    # Show user interface

    form = launcher.GfxLaunchWindow()
    form.show()

    # Create receiver thread for catching stdout events and redirecting
    # to user interface.

    if redirect:
        thread = QtCore.QThread()
        receiver = launcher.OutputReceiver(queue)
        receiver.mysignal.connect(form.on_append_text)
        receiver.moveToThread(thread)

        thread.started.connect(receiver.run)
        thread.start()

    # Start main application loop

    # app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())

    app.exec_()

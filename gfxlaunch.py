#!/usr/bin/env python
#
# LUNARC HPC Desktop On-Demand graphical launch tool
# Copyright (C) 2017-2023 LUNARC, Lund University
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from lhpcdt import *
import os
import sys
import argparse

from queue import Queue
from PyQt5 import QtCore, QtGui, QtWidgets

# --- Version information

gfxlaunch_copyright = """LUNARC HPC Desktop On-Demand - Version %s
Copyright (C) 2017-2023 LUNARC, Lund University
This program comes with ABSOLUTELY NO WARRANTY; for details see LICENSE.
This is free software, and you are welcome to redistribute it
under certain conditions; see LICENSE for details.
"""
gfxlaunch_copyright_short = """LUNARC HPC Desktop On-Demand - %s"""
gfxlaunch_version = "0.9.4"

# --- Fix search path for tool

tool_path = os.path.dirname(os.path.abspath(sys.argv[0]))
sys.path.insert(0, tool_path)
# sys.path.append(tool_path)


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
    lightPalette.setColor(QtGui.QPalette.ToolTipBase,
                          QtGui.QColor(255, 255, 230))
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

    print(sys.argv[0])

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
                        default="", help="Specify module to load for Jupyter Lab jobs.")

    parser.add_argument("--notebook-module", dest="notebook_module", action="store",
                        default="", help="Specify module to load for Jupyter Notebook jobs.")

    parser.add_argument("--autostart", dest="autostart",
                        action="store_true", default=False)

    parser.add_argument("--locked", dest="locked",
                        action="store_true", default=False)

    parser.add_argument("--group", dest="group",
                        help="Limit partitions to group.", default="")

    parser.add_argument("--silent",
                        dest="silent",
                        help="Run silently. No user interface controls. Application will start automatically",
                        action="store_true", default=False)

    parser.add_argument("--splash",
                        dest="splash",
                        help="Show splash screen.",
                        action="store_true", default=False)
    
    parser.add_argument("--restrict",
                        dest="restrict",
                        help="Restrict usage to unix-group.",
                        default="")

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

    old_stdout = sys.stdout

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

    # Show splash

    if (not args.silent) and (args.splash):
        splash_window = splash_win.SplashWindow(
            None, gfxlaunch_copyright % gfxlaunch_version)
        splash_window.show()

    # Show user interface

    form = launcher.GfxLaunchWindow()
    form.console_output = old_stdout
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
        form.redirect_thread = thread

    # Start main application loop

    # app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())

    app.exec_()

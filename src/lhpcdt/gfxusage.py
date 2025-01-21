#!/bin/env python
#
# LUNARC HPC Desktop On-Demand graphical job status display
# Copyright (C) 2017-2025 LUNARC, Lund University
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

gfxlaunch_copyright = """LUNARC HPC Desktop On-Demand GfxUsage - Version %s
Copyright (C) 2017-2025 LUNARC, Lund University
This program comes with ABSOLUTELY NO WARRANTY; for details see LICENSE.
This is free software, and you are welcome to redistribute it
under certain conditions; see LICENSE for details.
"""
gfxlaunch_copyright_short = """LUNARC HPC Desktop On-Demand GfxUsage - %s"""
gfxlaunch_version = "0.9.18"

# --- Fix search path for tool

tool_path = os.path.dirname(os.path.abspath(sys.argv[0]))
sys.path.append(tool_path)


def main():
    # Show version information

    print(gfxlaunch_copyright % gfxlaunch_version)
    print("")

    launchSettings = settings.LaunchSettings.create()
    launchSettings.tool_path = tool_path
    launchSettings.copyright_info = gfxlaunch_copyright
    launchSettings.copyright_short_info = gfxlaunch_copyright_short
    launchSettings.version_info = gfxlaunch_version

    # Redirect standard output

    redirect = False

    # Start Qt application

    app = QtWidgets.QApplication(sys.argv)

    # Show user interface

    form = monitor.SessionWindow()
    form.show()

    # Start main application loop

    app.exec_()


if __name__ == '__main__':
    main()

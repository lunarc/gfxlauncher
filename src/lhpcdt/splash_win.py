#!/bin/env python
#
# LUNARC HPC Desktop On-Demand graphical launch tool
# Copyright (C) 2017-2021 LUNARC, Lund University
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

"""
Splash window

Implements the splash window.
"""

import os
import getpass
from datetime import datetime

from PyQt5 import Qt, QtCore, QtGui, QtWidgets, uic

from . import jobs
from . import lrms
from . import remote
from . import settings
from . import config
from . import launcher

class SplashWindow(QtWidgets.QWidget):
    def __init__(self, parent = None, splash_text = ""):
        super(SplashWindow, self).__init__(parent)

        # Where can we find the user interface definitions (ui-files)

        self.tool_path = settings.LaunchSettings.create().tool_path

        ui_path = os.path.join(self.tool_path, "ui")
        image_path = os.path.join(self.tool_path, "images")

        # Load appropriate user interface

        uic.loadUi(os.path.join(ui_path, "splash.ui"), self)

        pixmap = QtGui.QPixmap(os.path.join(image_path, "lhpcdt_splash3.png"))
        self.splashLabel.setPixmap(pixmap)

        #self.setWindowFlags(QtCore.Qt.SplashScreen)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)

        self.center()

        self.versionLabel.setText(splash_text)

        self.statusTimer = QtCore.QTimer()
        self.statusTimer.timeout.connect(self.on_timeout)
        self.statusTimer.setInterval(5000)
        self.statusTimer.start()

        self.closeButton.clicked.connect(self.on_close_button_clicked)

    def center(self):
        frameGm = self.frameGeometry()
        screen = QtWidgets.QApplication.desktop().screenNumber(QtWidgets.QApplication.desktop().cursor().pos())
        centerPoint = QtWidgets.QApplication.desktop().screenGeometry(screen).center()
        frameGm.moveCenter(centerPoint)
        self.move(frameGm.topLeft())

    def on_timeout(self):
        self.statusTimer.stop()
        self.close()

    def on_close_button_clicked(self):
        self.statusTimer.stop()
        self.close()

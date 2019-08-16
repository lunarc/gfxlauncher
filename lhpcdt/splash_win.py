"""LUNARC HPC Desktop Launcher Module"""

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

        pixmap = QtGui.QPixmap(os.path.join(image_path, "lhpcdt_splash.png"))
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

#!/bin/env python
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

"""
Job User Interface module

This module provide job user interface functionality.
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
from . import conda_utils as cu

class JupyterNotebookJobPropWindow(QtWidgets.QDialog):
    """Resource specification window"""

    def __init__(self, parent=None):
        """Resource window constructor"""

        super(QtWidgets.QDialog, self).__init__(parent, QtCore.Qt.Window)

        self.tool_path = settings.LaunchSettings.create().tool_path
        ui_path = os.path.join(self.tool_path, "ui")

        uic.loadUi(os.path.join(ui_path, "notebook_job_prop_win.ui"), self)

        self.parent = parent
        self.__python_module = "Anaconda3"
        self.__use_custom_anaconda_env = False
        self.__custom_anaconda_env = ""
        self.__conda_install = cu.CondaInstall()

        self.set_data()

    def update_controls(self):
        self.conda_module_text.setText(self.__python_module)
        self.use_custom_env_check.setChecked(self.__use_custom_anaconda_env)
        self.conda_env_list.setEnabled(self.__use_custom_anaconda_env)

    def update_list(self):
        self.conda_env_list.clear()

        for e in self.__conda_install.conda_envs.keys():
            if "ipykernel" in self.__conda_install.conda_envs[e]["packages"]:
                self.conda_env_list.addItem(e)


    def set_data(self):
        """Assign values to controls"""
        self.update_controls()
        self.update_list()

    def get_data(self):
        """Get values from controls"""
        print("get_data()")
        self.__custom_anaconda_env = self.conda_env_list.currentText()
        self.__python_module = self.conda_module_text.text()
        self.__use_custom_anaconda_env = self.use_custom_env_check.isChecked()

    @property
    def python_module(self):
        return self.__python_module

    @python_module.setter
    def python_module(self, value):
        self.__python_module = value
        self.set_data()

    @property
    def use_custom_anaconda_env(self):
        return self.__use_custom_anaconda_env

    @use_custom_anaconda_env.setter
    def use_custom_anaconda_env(self, value):
        self.__use_custom_anaconda_env = value
        self.set_data()

    @property
    def custom_anaconda_env_list(self):
        return self.__custom_anaconda_env_list

    @custom_anaconda_env_list.setter
    def custom_anaconda_env_list(self, value):
        self.__custom_anaconda_env_list = value
        self.set_data()

    @property
    def custom_anaconda_env(self):
        return self.__custom_anaconda_env

    @custom_anaconda_env.setter
    def custom_anaconda_env(self, value):
        self.__custom_anaconda_env = value
        self.set_data()


    @QtCore.pyqtSlot()
    def on_ok_button_clicked(self):
        """Event method for OK button"""
        self.get_data()
        self.close()

    @QtCore.pyqtSlot()
    def on_cancel_button_clicked(self):
        """Event method for Cancel button"""
        self.close()

    @QtCore.pyqtSlot()
    def on_use_custom_env_check_clicked(self):
        self.__use_custom_anaconda_env = self.use_custom_env_check.isChecked()
        self.set_data()

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
import subprocess
from datetime import datetime

from PyQt5 import Qt, QtCore, QtGui, QtWidgets, uic

from . import jobs
from . import lrms
from . import remote
from . import settings
from . import config
from . import launcher
from . import conda_utils as cu
from . import ui_notebook_job_prop_win as ui

class ProcessThread(QtCore.QThread):
    """Job submission thread"""
    def __init__(self, cmd):
        QtCore.QThread.__init__(self)

        self.__cmd = cmd
        self.output = ""

    def run(self):
        """Main thread method"""

        self.output = subprocess.check_output(self.__cmd, shell=True)

class JupyterNotebookJobPropWindow(QtWidgets.QDialog, ui.Ui_notebook_prop_form):
    """Resource specification window"""

    def __init__(self, parent=None):
        """Resource window constructor"""

        super(QtWidgets.QDialog, self).__init__(parent, QtCore.Qt.Window)
        self.setupUi(self)

        self.tool_path = settings.LaunchSettings.create().tool_path

        self.parent = parent
        self.__python_module = "Anaconda3"
        self.__use_custom_anaconda_env = False
        self.__custom_anaconda_env = ""
        self.__conda_install = cu.CondaInstall()
        self.__conda_install.query_packages = False
        self.__conda_install.on_query_env = self.on_query_env
        self.__conda_install.on_query_completed = self.on_query_completed

    def showEvent(self, event):
        """Disable controls and start timer for querying modules"""
        self.disable_controls()
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.on_timeout)
        self.timer.start(1000)

    def disable_controls(self):
        """Disable controls on dialog"""
        self.setEnabled(False)

    def enable_controls(self):
        """Enable all controls on dialog"""
        self.setEnabled(True)

    def on_timeout(self):
        """Timeout for starting conda query"""
        self.timer.stop()
        self.__conda_install.query()

    def on_query_env(self, conda_env):
        """Conda query callback for updating UI"""

        self.env_status_text.setText(f'Querying environment: {conda_env}')
        self.update()
        QtCore.QCoreApplication.processEvents()
    
    def on_query_completed(self):
        """Conda queryt callback when query is completed"""

        self.env_status_text.setText('')
        self.update()
        QtCore.QCoreApplication.processEvents()
        self.enable_controls()
        self.get_data()
        self.update_controls()
        self.update_list()

    def update_controls(self):
        """Update user interface controls"""

        if not self.modules_supports_anaconda():
            self.__use_custom_anaconda_env = False
            self.conda_env_list.setCurrentIndex(-1)
            self.conda_env_list.setEnabled(False)
            self.use_custom_env_check.setEnabled(False)
        else:
            self.conda_env_list.setCurrentIndex(-1)
            self.conda_env_list.setEnabled(True)
            self.use_custom_env_check.setEnabled(True)

        self.conda_module_text.setPlainText(self.__python_module)
        self.use_custom_env_check.setChecked(self.__use_custom_anaconda_env)
        self.conda_env_list.setEnabled(self.__use_custom_anaconda_env)
        if not self.__use_custom_anaconda_env:
            self.conda_env_list.setCurrentIndex(-1)


    def update_list(self):
        """Update list box"""

        self.conda_env_list.clear()

        for e in self.__conda_install.conda_envs.keys():
            self.conda_env_list.addItem(e)

        self.conda_env_list.setCurrentIndex(-1)

    def modules_supports_anaconda(self):
        """Check for anaconda support"""
        return "anaconda" in self.__python_module.lower()

    def set_data(self):
        """Assign values to controls"""
        self.update_list()
        self.update_controls()

    def get_data(self):
        """Get values from controls"""
        self.__custom_anaconda_env = self.conda_env_list.currentText()
        self.__python_module = self.conda_module_text.toPlainText()
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

    @QtCore.pyqtSlot()
    def on_browse_modules_button_clicked(self):
        """Start ml-browse as a separate thread"""
        self.disable_controls()

        self.process_thread = ProcessThread("ml-browse --select --name-only --filter=%s" %(self.__python_module))
        self.process_thread.finished.connect(self.on_process_thread_finished)
        self.process_thread.start()

    @QtCore.pyqtSlot()
    def on_process_thread_finished(self):        
        """Handle output from ml-browse"""
        self.enable_controls()

        output = self.process_thread.output

        print(output.decode("utf-8"))

        if output!="":
            module_list = []
            append_module = False
            for line in output.decode("utf-8").split("\n"):
                if "#MODSTART#" in line.strip():
                    append_module = True
                else:
                    if append_module:
                        if line.strip()=="":
                            append_module = False
                        else:
                            if len(line)>0:
                                module_list.append(line.strip())

            if len(module_list)>0:
                self.__python_module = ",".join(module_list)
                self.update_controls()
                self.update_list()
        

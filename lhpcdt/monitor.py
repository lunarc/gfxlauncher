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
# 
"""LUNARC HPC Desktop Monitor Module"""

import os
import getpass
from datetime import datetime

from PyQt5 import Qt, QtCore, QtGui, QtWidgets, uic

from . import jobs
from . import lrms
from . import remote
from . import settings
from . import config

from subprocess import Popen, PIPE, STDOUT

class MonitorWindow(QtWidgets.QWidget):
    def __init__(self, parent = None):
        super(MonitorWindow, self).__init__(parent)
        self.tool_path = settings.LaunchSettings.create().tool_path

        if len(settings.LaunchSettings.create().args)>1:
            self.hostname = settings.LaunchSettings.create().args[1]
            self.local_exec = False
        else:
            self.hostname = ""
            self.local_exec = True

        ui_path = os.path.join(self.tool_path, "ui")

        # Load appropriate user interface

        uic.loadUi(os.path.join(ui_path, "monitor.ui"), self)

        self.remote_probe = remote.StatusProbe(local_exec=self.local_exec)
        self.remote_probe.check_all(self.hostname)

        self.update_controls()

    def update_controls(self):
        self.progressMemory.setMaximum(self.remote_probe.total_mem)
        self.progressMemory.setValue(self.remote_probe.used_mem)
        self.progressCPU.setMaximum(100)
        self.progressCPU.setValue(self.remote_probe.cpu_usage)
        self.hostnameEdit.setText(self.hostname)

        self.progressGPU1.setEnabled(False)
        self.progressGPU2.setEnabled(False)
        self.progressGPU3.setEnabled(False)
        self.progressGPU4.setEnabled(False)
        self.progressGPU5.setEnabled(False)
        self.progressGPU6.setEnabled(False)
        self.progressGPU7.setEnabled(False)
        self.progressGPU8.setEnabled(False)

        if len(self.remote_probe.gpu_usage)>=1:
            self.progressGPU1.setEnabled(True)
            self.progressGPU1.setValue(self.remote_probe.gpu_usage[0])
        if len(self.remote_probe.gpu_usage)>=2:
            self.progressGPU2.setEnabled(True)
            self.progressGPU2.setValue(self.remote_probe.gpu_usage[1])
        if len(self.remote_probe.gpu_usage)>=3:
            self.progressGPU3.setEnabled(True)
            self.progressGPU3.setValue(self.remote_probe.gpu_usage[2])
        if len(self.remote_probe.gpu_usage)>=4:
            self.progressGPU4.setEnabled(True)
            self.progressGPU4.setValue(self.remote_probe.gpu_usage[3])
        if len(self.remote_probe.gpu_usage)>=5:
            self.progressGPU5.setEnabled(True)
            self.progressGPU5.setValue(self.remote_probe.gpu_usage[4])
        if len(self.remote_probe.gpu_usage)>=6:
            self.progressGPU6.setEnabled(True)
            self.progressGPU6.setValue(self.remote_probe.gpu_usage[4])
        if len(self.remote_probe.gpu_usage)>=7:
            self.progressGPU7.setEnabled(True)
            self.progressGPU7.setValue(self.remote_probe.gpu_usage[7])
        if len(self.remote_probe.gpu_usage)>=8:
            self.progressGPU8.setEnabled(True)
            self.progressGPU8.setValue(self.remote_probe.gpu_usage[8])


class SessionWindow(QtWidgets.QWidget):
    """Session Window class"""

    def __init__(self, parent=None):
        super(SessionWindow, self).__init__(parent)
        self.slurm = lrms.Slurm()
        self.queue = lrms.Queue()

        #uic.loadUi("../session_manager.ui", self)

        self.tool_path = settings.LaunchSettings.create().tool_path

        ui_path = os.path.join(self.tool_path, "ui")

        # Load appropriate user interface

        uic.loadUi(os.path.join(ui_path, "session_manager.ui"), self)

        self.update_table()

    def update_table(self):
        """Update session table"""

        self.queue.update()

        user = getpass.getuser()

        self.sessionTable.setColumnCount(9)
        self.sessionTable.setHorizontalHeaderLabels(
            ["Id", "Name", "State", "Time",
             "Requested", "Count", "Nodes", "", ""]
            )

        if user in self.queue.userJobs:
            self.sessionTable.setRowCount(
                len(list(self.queue.userJobs[user].keys())))
        else:
            self.sessionTable.setRowCount(0)
            return


        row = 0
        for id in list(self.queue.userJobs[user].keys()):
            self.sessionTable.setItem(row, 0, QtWidgets.QTableWidgetItem(str(id)))
            self.sessionTable.setItem(row, 1, QtWidgets.QTableWidgetItem(
                str(self.queue.userJobs[user][id]["name"])))
            self.sessionTable.setItem(row, 2, QtWidgets.QTableWidgetItem(
                str(self.queue.userJobs[user][id]["state"])))
            self.sessionTable.setItem(row, 3, QtWidgets.QTableWidgetItem(
                str(self.queue.userJobs[user][id]["time"])))
            self.sessionTable.setItem(row, 4, QtWidgets.QTableWidgetItem(
                str(self.queue.userJobs[user][id]["timelimit"])))
            self.sessionTable.setItem(row, 5, QtWidgets.QTableWidgetItem(
                str(self.queue.userJobs[user][id]["nodes"])))
            self.sessionTable.setItem(row, 6, QtWidgets.QTableWidgetItem(
                str(self.queue.userJobs[user][id]["nodelist"])))

            cancelButton = QtWidgets.QPushButton("Cancel")
            cancelButton.clicked.connect(self.cancel_button_clicked)
            infoButton = QtWidgets.QPushButton("Info")
            infoButton.clicked.connect(self.info_button_clicked)

            self.sessionTable.setCellWidget(row, 7, cancelButton)
            self.sessionTable.setCellWidget(row, 8, infoButton)
            row += 1

        self.sessionTable.resizeColumnsToContents()

    def cancel_button_clicked(self):
        button = self.sender()
        index = self.sessionTable.indexAt(button.pos())
        if index.isValid():
            jobId = int(self.sessionTable.item(index.row(), 0).text())
            self.slurm.cancel_job_with_id(jobId)
            self.update_table()

    def info_button_clicked(self):
        button = self.sender()
        index = self.sessionTable.indexAt(button.pos())
        if index.isValid():
            print(index.row(), index.column())

    @QtCore.pyqtSlot()
    def on_refreshButton_clicked(self):
        self.update_table()

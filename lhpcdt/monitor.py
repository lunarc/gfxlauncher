#
# LUNARC HPC Desktop On-Demand graphical launch tool
# Copyright (C) 2017-2022 LUNARC, Lund University
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

class QueueSortFilterProxyModel(QtCore.QSortFilterProxyModel):
    def __init__(self, parent, state_filter="", user_filter=""):
        super().__init__(parent)
        self.state_filter = state_filter
        self.user_filter = user_filter

    def lessThan(self, left, right):
        left_data = self.sourceModel().data(left)
        right_data = self.sourceModel().data(right)
        return left_data < right_data
    
    def filterAcceptsRow(self, source_row, source_parent):
        model = self.sourceModel()
        job_id = model.job_keys[source_row]
        if self.state_filter == "" and self.user_filter =="":
            return True
        else:
            if self.state_filter == "" and self.user_filter!= "":
                return model.job_dict[job_id]["user"] == self.user_filter
            elif self.state_filter != ""  and self.user_filter == "":
                return model.job_dict[job_id]["state"] == self.state_filter
            elif self.state_filter != "" and self.user_filter != "":
                if model.job_dict[job_id]["state"] == self.state_filter:
                    return model.job_dict[job_id]["user"] == self.user_filter
                else:
                    return False
            else:
                return True


class QueueTableModel(QtCore.QAbstractTableModel):
    def __init__(self, data):
        super(QueueTableModel, self).__init__()

        self.__data = data
        self.__headers = ["Id", "Partition", "Name", "User", "Account", "Progress", "Start", "Left", "Nodes", "CPUs", "Nodelist"]     
        self.__column_keys = ["", "state, partition", "name", "user", "account", "timestart", "timeleft", "nodes", "cpus", "nodelist"]
        self.__job_keys = list(self.__data.keys())

    @property
    def job_keys(self):
        return self.__job_keys

    @property
    def job_dict(self):
        return self.__data

    def headerData(self, section, orientation, role):
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                return str(self.__headers[section])

            if orientation == QtCore.Qt.Vertical:
                return str(section)            

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole:

            job_key = self.__job_keys[index.row()]

            job_values = self.__data[job_key]

            value = ""

            if index.column() == 0:
                return int(job_key)

            if index.column() == 1:
                return str(job_values["partition"])

            if index.column() == 2:
                return str(job_values["name"])

            if index.column() == 3:
                return str(job_values["user"])

            if index.column() == 4:
                return str(job_values["account"])

            if index.column() == 5:
                return str(0)

            if index.column() == 6:
                return str(job_values["timestart"])

            if index.column() == 7:
                return str(job_values["timeleft"])

            if index.column() == 8:
                return int(job_values["nodes"])

            if index.column() == 9:
                return int(job_values["cpus"])

            if index.column() == 10:
                return str(job_values["nodelist"])

            return ""

    def rowCount(self, index):
        return len(self.__data.keys())

    def columnCount(self, index):
        return 11

class SessionWindow(QtWidgets.QMainWindow):
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

        self.refresh_timer = QtCore.QTimer()
        self.refresh_timer.setInterval(15000)
        self.refresh_timer.timeout.connect(self.on_refresh_timer_timeout)

        self.job_info_window = None

        self.use_progress_control = False

        self.update_table()
        self.processing_progress.setVisible(False)

    def time_to_decimal(self, time_string):
        """Time to decimal conversion routine"""

        d = "0"
        h = "0"
        m = "0"
        s = "0"

        if "-" in time_string:
            (d, time_rest) = time_string.split("-")
        else:
            time_rest = time_string

        if len(time_rest.split(':')) == 2:
            (m, s) = time_rest.split(':')
        elif len(time_rest.split(':')) == 3:
            (h, m, s) = time_rest.split(':')

        return int(d) * 86400 + int(h) * 3600 + int(m) * 60 + int(s)

    def state_bg_color(self, state_str):
        """Return a color depending on the SLURM state."""

        if state_str == "RUNNING":
            return QtGui.QColor("mediumseagreen")
        elif state_str == "PENDING":
            return QtGui.QColor("gold")
        elif state_str == "PENDING":
            return QtGui.QColor("gold")
        else:
            return QtGui.QColor("white")

    def update_table(self):
        """Update session table"""

        print("update_table()")

        # Query the queue

        self.queue.update()

        # Get user information

        user = getpass.getuser()

        # Test tableview

        self.queue_model = QueueTableModel(self.queue.jobs)

        if self.action_show_all_jobs.isChecked():
            self.running_model = QueueSortFilterProxyModel(self, "RUNNING")
            self.running_model.setSourceModel(self.queue_model)
            self.waiting_model = QueueSortFilterProxyModel(self, "PENDING")
            self.waiting_model.setSourceModel(self.queue_model)
        else:
            self.running_model = QueueSortFilterProxyModel(self, "RUNNING", user)
            self.running_model.setSourceModel(self.queue_model)
            self.waiting_model = QueueSortFilterProxyModel(self, "PENDING", user)
            self.waiting_model.setSourceModel(self.queue_model)

        self.running_table_view.setModel(self.running_model)
        self.running_table_view.setSortingEnabled(True)

        self.waiting_table_view.setModel(self.waiting_model)
        self.waiting_table_view.setSortingEnabled(True)

        return

    def get_selected_job_list(self):
        """Get selected job list from table selection."""

        selected_indexes = self.running_table_view.selectedIndexes()

        selected_rows = []

        for selected_index in selected_indexes:
            selected_rows.append(selected_index.row())

        selected_rows = list(set(selected_rows))

        job_list = []

        for row in selected_rows:
            job_id = self.running_model.index(row, 0).data()
            job_list.append(int(job_id))

        print(job_list)

        return job_list

    @QtCore.pyqtSlot()
    def on_action_show_all_jobs_triggered(self):
        """Toggle showing all jobs event method."""

        print("show_all_jobs_triggered")
        self.update_table()
        self.processing_progress.setVisible(False)

    @QtCore.pyqtSlot()
    def on_action_cancel_job_triggered(self):
        """Cancel selected job event method."""

        selected_jobs = self.get_selected_job_list()

        for job_id in selected_jobs:
            self.slurm.cancel_job_with_id(job_id)

        self.update_table()
        self.processing_progress.setVisible(False)

    @QtCore.pyqtSlot()
    def on_action_job_info_triggered(self):
        """Show job info window."""

        selected_jobs = self.get_selected_job_list()

        if len(selected_jobs)>1:
            QtWidgets.QMessageBox.information(
                self, "SLURM Job monitor", "You can only show job information for a single job.")

            return

        if len(selected_jobs) == 0:
            return

        if self.job_info_window is None:
            self.job_info_window = JobInfoWindow()

        self.job_info_window.job_id = selected_jobs[0]
        self.job_info_window.show()


    @QtCore.pyqtSlot()
    def on_action_refresh_triggered(self):
        """Refresh button event method."""
        print("refresh_triggered")
        self.update_table()
        self.processing_progress.setVisible(False)

    @QtCore.pyqtSlot()
    def on_action_auto_refresh_triggered(self):
        """Auto refresh button event method."""

        if self.action_auto_refresh.isChecked():
            self.refresh_timer.start()
        else:
            self.refresh_timer.stop()

    @QtCore.pyqtSlot(QtWidgets.QTableWidgetItem)
    def on_session_table_itemDoubleClicked(self, item):
        self.on_action_job_info_triggered()

    def on_refresh_timer_timeout(self):
        """Refresh timer event method."""

        print("timer_timeout")
        self.update_table()
        self.processing_progress.setVisible(False)

class JobInfoWindow(QtWidgets.QMainWindow):
    """Session Window class"""

    def __init__(self, parent=None):
        super(JobInfoWindow, self).__init__(parent)
        self.slurm = lrms.Slurm()
        self.queue = lrms.Queue()

        self.__job_id = -1

        self.job_info_dict = {}

        self.tool_path = settings.LaunchSettings.create().tool_path

        ui_path = os.path.join(self.tool_path, "ui")

        # Load appropriate user interface

        uic.loadUi(os.path.join(ui_path, "job_info.ui"), self)


    def update_table(self):
        """Update job property table"""

        self.queue.update()

        self.job_properties.clear()

        self.job_properties.setColumnCount(2)
        self.job_properties.setHorizontalHeaderLabels(
            ["Property", "Value"]
        )

        if len(self.job_info_dict.keys())>0:
            self.job_properties.setRowCount(len(self.job_info_dict.keys()))
        else:
            self.job_properties.setRowCount(0)
            return

        row = 0
        for prop, value in self.job_info_dict.items():
            self.job_properties.setItem(row, 0, QtWidgets.QTableWidgetItem(str(prop)))
            self.job_properties.setItem(row, 1, QtWidgets.QTableWidgetItem(str(value)))
            row += 1

        self.job_properties.resizeColumnsToContents()            


    def query_job_info(self):
        """Query SLURM for job information"""

        job_info = self.queue.job_info(self.__job_id)
        job_lines = job_info.split("\n")

        self.job_info_dict = {}

        for line in job_lines:
            value_pairs = line.split() 

            for value_pair in value_pairs:
                if len(value_pair.split("="))==2:
                    prop, value = value_pair.split("=")
                    self.job_info_dict[prop.strip()] = value.strip()


    def on_action_refresh_view_triggered(self):
        """Update job info and property table when refresh button is clicked."""
        self.query_job_info()
        self.update_table()


    @property
    def job_id(self):
        return self.__job_id

    @job_id.setter
    def job_id(self, value):
        self.__job_id = value
        self.setWindowTitle("Information on job %d" % self.__job_id)
        self.query_job_info()
        self.update_table()

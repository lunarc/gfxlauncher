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

        # Query the queue

        self.queue.update()

        # Clear all tables

        self.running_session_table.clear()
        self.waiting_session_table.clear()
        self.bonus_session_table.clear()

        # Get user information

        user = getpass.getuser()

        #  JOBID PARTITION                      NAME     USER ACCOUNT        ST          START_TIME  TIME_LEFT  NODES CPUS NODELIST(REASON)
        #6385516        lu           LDMX_Prod_Simul      rpt lu2021-2-100    R 2022-03-04T05:00:49       0:23      1    1 au027

        tables = [self.running_session_table, self.waiting_session_table, self.bonus_session_table]
        table_states = ['RUNNING', 'PENDING', '']
        job_dicts = [self.queue.running_jobs, self.queue.pending_jobs, {}]

        self.processing_progress.setVisible(True)
        self.processing_progress.setValue(0)

        job_counter = 0
        total_jobs = len(self.queue.jobs.keys())

        if self.action_show_all_jobs.isChecked():

            for table, table_state, jobs in zip(tables, table_states, job_dicts):

                table.setColumnCount(12)

                table.setHorizontalHeaderLabels(
                    ["Id", "Partition", "Name", "User", "Account", "State",
                    "Progress", "Start", "Left", "Nodes", "CPUs", "Nodelist"]
                    )

                if len(jobs.keys())>0:
                    table.setRowCount(
                        len(list(jobs.keys())))
                else:
                    table.setRowCount(0)
                    return

                row = 0

                for id in list(jobs.keys()):

                    if jobs[id]["state"] == table_state:

                        job_counter += 1
                        self.processing_progress.setValue(100*job_counter/total_jobs)

                        state_str = str(jobs[id]["state"])
                        state_item = QtWidgets.QTableWidgetItem(state_str)
                        state_item.setBackground(self.state_bg_color(state_str))

                        time_str = jobs[id]["time"]
                        timelimit_str = jobs[id]["timelimit"]

                        time_value = self.time_to_decimal(time_str)
                        timelimit_value = self.time_to_decimal(timelimit_str)

                        percent_value = int(100*time_value/timelimit_value)

                        progress_bar = QtWidgets.QProgressBar(self)
                        progress_bar.setValue(percent_value)

                        #  JOBID PARTITION                      NAME     USER ACCOUNT        ST          START_TIME  TIME_LEFT  NODES CPUS NODELIST(REASON)                

                        table.setItem(row, 0, QtWidgets.QTableWidgetItem(str(id)))

                        table.setItem(row, 1, QtWidgets.QTableWidgetItem(
                            str(jobs[id]["partition"])))

                        table.setItem(row, 2, QtWidgets.QTableWidgetItem(
                            str(jobs[id]["name"])))

                        table.setItem(row, 3, QtWidgets.QTableWidgetItem(
                            str(jobs[id]["user"])))

                        table.setItem(row, 4, QtWidgets.QTableWidgetItem(
                            str(jobs[id]["account"])))

                        table.setItem(row, 5, state_item)

                        table.setCellWidget(row, 6, progress_bar)

                        table.setItem(row, 7, QtWidgets.QTableWidgetItem(
                            str(jobs[id]["timestart"])))
                        table.setItem(row, 8, QtWidgets.QTableWidgetItem(
                            str(jobs[id]["timeleft"])))
                        table.setItem(row, 9, QtWidgets.QTableWidgetItem(
                            str(jobs[id]["nodes"])))
                        table.setItem(row, 10, QtWidgets.QTableWidgetItem(
                            str(jobs[id]["cpus"])))
                        table.setItem(row, 11, QtWidgets.QTableWidgetItem(
                            str(jobs[id]["nodelist"])))

                        row += 1

                    table.resizeColumnsToContents()

        else:

            self.running_session_table.setColumnCount(8)
            self.running_session_table.setHorizontalHeaderLabels(
                ["Id", "Name", "State", "Percent", "Time",
                "Requested", "Count", "Nodes"]
                )

            if user in self.queue.userJobs:
                self.running_session_table.setRowCount(
                    len(list(self.queue.userJobs[user].keys())))
            else:
                self.running_session_table.setRowCount(0)
                return

            row = 0
            for id in list(self.queue.userJobs[user].keys()):


                self.running_session_table.setItem(row, 0, QtWidgets.QTableWidgetItem(str(id)))

                self.running_session_table.setItem(row, 1, QtWidgets.QTableWidgetItem(
                    str(self.queue.userJobs[user][id]["name"])))

                state_str = str(self.queue.userJobs[user][id]["state"])
                state_item = QtWidgets.QTableWidgetItem(state_str)
                state_item.setBackground(self.state_bg_color(state_str))

                time_str = self.queue.userJobs[user][id]["time"]
                timelimit_str = self.queue.userJobs[user][id]["timelimit"]

                time_value = self.time_to_decimal(time_str)
                timelimit_value = self.time_to_decimal(timelimit_str)

                percent_value = int(100*time_value/timelimit_value)

                self.running_session_table.setItem(row, 2, state_item)

                progress_bar = QtWidgets.QProgressBar(self)
                progress_bar.setValue(percent_value)

                self.running_session_table.setCellWidget(row, 3, progress_bar)

                self.running_session_table.setItem(row, 4, QtWidgets.QTableWidgetItem(
                    str(self.queue.userJobs[user][id]["time"])))
                self.running_session_table.setItem(row, 5, QtWidgets.QTableWidgetItem(
                    str(self.queue.userJobs[user][id]["timelimit"])))
                self.running_session_table.setItem(row, 6, QtWidgets.QTableWidgetItem(
                    str(self.queue.userJobs[user][id]["nodes"])))
                self.running_session_table.setItem(row, 7, QtWidgets.QTableWidgetItem(
                    str(self.queue.userJobs[user][id]["nodelist"])))

                row += 1

            self.running_session_table.resizeColumnsToContents()

    def get_selected_job_list(self):
        """Get selected job list from table selection."""

        selected_ranges = self.running_session_table.selectedRanges()

        job_list = []

        for selected_range in selected_ranges:
            start_row = int(selected_range.topRow())
            end_row = int(selected_range.bottomRow())

            for row in range(start_row, end_row+1):
                job_id = self.running_session_table.item(row, 0).text()
                job_list.append(int(job_id))

        return job_list


    def on_action_show_all_jobs_triggered(self):
        """Toggle showing all jobs event method."""

        self.update_table()
        self.processing_progress.setVisible(False)


    def on_action_cancel_job_triggered(self):
        """Cancel selected job event method."""

        selected_jobs = self.get_selected_job_list()

        for job_id in selected_jobs:
            self.slurm.cancel_job_with_id(job_id)

        self.update_table()
        self.processing_progress.setVisible(False)

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


    def on_action_refresh_triggered(self):
        """Refresh button event method."""
        self.update_table()
        self.processing_progress.setVisible(False)

    def on_action_auto_refresh_triggered(self):
        """Auto refresh button event method."""

        if self.action_auto_refresh.isChecked():
            self.refresh_timer.start()
        else:
            self.refresh_timer.stop()

    def on_refresh_timer_timeout(self):
        """Refresh timer event method."""

        self.update_table()
        self.processing_progress.setVisible(False)

    def on_session_table_itemDoubleClicked(self, item):
        self.on_action_job_info_triggered()

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

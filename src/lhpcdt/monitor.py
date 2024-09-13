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

import os, math, sys
import getpass
from datetime import datetime

from PyQt5 import Qt, QtCore, QtGui, QtWidgets, uic

from . import jobs
from . import lrms
from . import remote
from . import settings
from . import config
from . import resources
from . import ui_session_manager as ui

from subprocess import Popen, PIPE, STDOUT

def time_to_decimal(time_string):
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


class QueueTableDelegate(QtWidgets.QStyledItemDelegate):
    """Delegate class for drawing progress bars."""
    def __init__(self, parent=None):
        super(QueueTableDelegate, self).__init__(parent)

    def paint(self, painter, option, index):
     
        if index.column()==5:

            value = index.data()

            painter.save()
            full_rect = QtCore.QRect(option.rect)
            rect = option.rect
            rect.adjust(5, 5, -5, -5)

            bar_length = int(rect.width()*value/100.0)
            rect_width = rect.width()

            #painter.setPen(QtCore.Qt.black)

            rect.adjust(0, 0, -rect_width+bar_length, 0)

            self.bar_gradient = QtGui.QLinearGradient(rect.left(), rect.top(), rect.right(), rect.bottom())
            self.bar_gradient.setColorAt(0.0, QtGui.QColor(50, 200, 50))
            self.bar_gradient.setColorAt(1.0, QtGui.QColor(180, 255, 180))
            self.bar_brush = QtGui.QBrush(self.bar_gradient)
            painter.setPen(QtGui.QPen(QtGui.QColor(20, 150, 20)))
            painter.setBrush(self.bar_brush)
          
            painter.drawRect(rect)
            painter.setPen(QtGui.QPen(QtGui.QColor(0,0,0)))
            painter.drawText(full_rect, QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter, "%d" % (int(value))+"%")

            painter.restore()
        else:
            QtWidgets.QStyledItemDelegate.paint(self, painter, option, index)


class QueueSortFilterProxyModel(QtCore.QSortFilterProxyModel):
    """Proxy model class for enabling queue sorting."""
    def __init__(self, parent, state_filter="", user_filter="", show_progress=True):
        super().__init__(parent)
        self.state_filter = state_filter
        self.user_filter = user_filter
        self.show_progress = show_progress
        self.search_text = ""

    def lessThan(self, left, right):
        """Sorting comparison function."""
        left_data = self.sourceModel().data(left)
        right_data = self.sourceModel().data(right)
        return left_data < right_data

    def search_filter(self, job_id, flag):
        if self.search_text == "":
            return flag
        else:
            if flag:
                model = self.sourceModel()
                values = model.job_dict[job_id]
                for key, value in values.items():
                    if self.search_text in str(value):
                        return True
                return False
            else:
                return flag

    def filterAcceptsRow(self, source_row, source_parent):
        """Filter function."""
        model = self.sourceModel()
        job_id = model.job_keys[source_row]
        if self.state_filter == "" and self.user_filter == "":
            return self.search_filter(job_id, True)
        else:
            if self.state_filter == "" and self.user_filter != "":
                return self.search_filter(job_id, (model.job_dict[job_id]["user"] == self.user_filter))
            elif self.state_filter != "" and self.user_filter == "":
                return self.search_filter(job_id, (model.job_dict[job_id]["state"] == self.state_filter))
            elif self.state_filter != "" and self.user_filter != "":
                if model.job_dict[job_id]["state"] == self.state_filter:
                    return self.search_filter(job_id, model.job_dict[job_id]["user"] == self.user_filter)
                else:
                    return False
            else:
                return False

    def filterAcceptsColumn(self, source_column, source_parent):
        if not self.show_progress and source_column == 5:
            return False
        else:
            return True

class QueueTableModel(QtCore.QAbstractTableModel):
    """Queue table model for use with QTableView"""
    def __init__(self, data, max_nodes=-1, max_cpus=-1):
        super(QueueTableModel, self).__init__()

        self.__data = data
        self.__headers = ["Id", "Partition", "Name", "User", "Account",
                          "Progress", "Start", "Left", "Nodes", "CPUs", "Nodelist/Reason"]
        self.__column_keys = ["", "state, partition", "name", "user",
                              "account", "timestart", "timeleft", "nodes", "cpus", "nodelist"]
        self.__job_keys = list(self.__data.keys())

        self.colors = ["#FFF878", "#FEED73", "#FDE16D", "#FCD668", "#FBCA62", "#FABF5D", "#F9B458", "#F8A852", "#F79D4D", "#F69147", "#F58642"]


        self.__max_nodes = max_nodes
        self.__max_cpus = max_cpus

    @property
    def job_keys(self):
        return self.__job_keys

    @property
    def job_dict(self):
        return self.__data

    @property
    def max_nodes(self):
        return self.__max_nodes

    @max_nodes.setter
    def max_nodes(self, nodes):
        self.__max_nodes = nodes

    @property
    def max_cpus(self):
        return self.__max_cpus

    @max_cpus.setter
    def max_cpus(self, cpus):
        self.__max_cpus = cpus

    def headerData(self, section, orientation, role):
        """Return table headers"""
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                return str(self.__headers[section])

            if orientation == QtCore.Qt.Vertical:
                return str(section)

    def reason_to_string(self, reason):
        if "(Priority)" in reason:
            return "Waiting for higher priority jobs."
        elif "(Resources)" in reason:
            return "Waiting for resources to become free."
        elif "(AssocGrpCpuLimit)" in reason:
            return "Account resource limit reached (CPU)."
        elif "(DependencyNeverSatisfied)" in reason:
            return "Job dependenies can't be resolved."
        elif "(Dependency)" in reason:
            return "Job waiting for dependency."
        elif "(BadConstraints)" in reason:
            return "Job requirements can't be satisfied."
        elif "(QOSJobLimit)" in reason:
            return "The job's QOS has reached its maximum job count."
        elif "(QOSResourceLimit)" in reason:
            return "The job's QOS has reached some resource limit."
        elif "(QOSTimeLimit)" in reason:
            return "The job's QOS has reached its time limit."
        elif "(ReqNodeNotAvail)" in reason:
            return "Some node specifically required by the job is not currently available."
        elif "(AssociationJobLimit)" in reason:
            return "The job's association has reached its maximum job count."
        elif "(AssociationResourceLimit)" in reason:
            return "The job's association has reached some resource limit."
        elif "(AssociationTimeLimit)" in reason:
            return "The job's association has reached its time limit."
        else:
            return reason



    def data(self, index, role=QtCore.Qt.DisplayRole):
        """Return table data"""
        if role == QtCore.Qt.DisplayRole:

            job_key = self.__job_keys[index.row()]

            job_values = self.__data[job_key]

            value = ""

            if index.column() == 0:
                return str(job_key)

            if index.column() == 1:
                return str(job_values["partition"])

            if index.column() == 2:
                return str(job_values["name"])

            if index.column() == 3:
                return str(job_values["user"])

            if index.column() == 4:
                return str(job_values["account"])

            if index.column() == 5:
                time_str = job_values["time"]
                timelimit_str = job_values["timelimit"]

                time_value = time_to_decimal(time_str)
                timelimit_value = time_to_decimal(timelimit_str)

                percent_value = int(100*time_value/timelimit_value)            

                return float(percent_value)

            if index.column() == 6:
                return str(job_values["timestart"])

            if index.column() == 7:
                return str(job_values["timeleft"])

            if index.column() == 8:
                return int(job_values["nodes"])

            if index.column() == 9:
                return int(job_values["cpus"])

            if index.column() == 10:
                return self.reason_to_string(str(job_values["nodelist"]))

            return ""

        if role == QtCore.Qt.BackgroundColorRole:
            
            job_key = self.__job_keys[index.row()]
            job_values = self.__data[job_key]

            if index.column() == 8:
                nodes = int(job_values["nodes"])
                return QtGui.QColor(self.colors[int(math.floor((len(self.colors)-1)*nodes/self.max_nodes))])
            elif index.column() == 9:
                cpus = int(job_values["cpus"])
                return QtGui.QColor(self.colors[int(math.floor((len(self.colors)-1)*cpus/self.max_cpus))])
            elif index.column() == 10:
                if "(Priority)" in job_values["nodelist"]:
                    return QtGui.QColor(50, 200, 50)
                elif "(Resources)" in job_values["nodelist"]:
                    return QtGui.QColor(50, 230, 50)
                elif "(AssocGrpCpuLimit)" in job_values["nodelist"]:
                    return QtGui.QColor(220, 220, 50)
                elif "(DependencyNeverSatisfied)" in job_values["nodelist"]:
                    return QtGui.QColor(220, 50, 50)
                else:
                    return None
            else:
                return None

        if role == QtCore.Qt.TextAlignmentRole:
            if index.column() == 0:
                return QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight

            if index.column() == 1:
                return QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft

            if index.column() == 2:
                return QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft

            if index.column() == 3:
                return QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft

            if index.column() == 4:
                return QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft

            if index.column() == 6:
                return QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight

            if index.column() == 7:
                return QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight

            if index.column() == 8:
                return QtCore.Qt.AlignVCenter | QtCore.Qt.AlignCenter

            if index.column() == 9:
                return QtCore.Qt.AlignVCenter | QtCore.Qt.AlignCenter

            if index.column() == 10:
                return QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft

            return QtCore.Qt.AlignVCenter | QtCore.Qt.AlignCenter





    def rowCount(self, index):
        """Return table rows"""
        return len(self.__data.keys())

    def columnCount(self, index):
        """Return table columns"""
        return 11


class SessionWindow(QtWidgets.QMainWindow, ui.Ui_MainWindow):
    """Session Window class"""

    def __init__(self, parent=None):
        super(SessionWindow, self).__init__(parent)
        self.setupUi(self)

        self.slurm = lrms.Slurm()

        if not self.slurm.check_environment():
            QtWidgets.QMessageBox.information(
                self, "GfxLauncher", "SLURM not available. Please contact support.")
            sys.exit(1)

        self.queue = lrms.Queue()

        self.tool_path = settings.LaunchSettings.create().tool_path

        self.refresh_timer = QtCore.QTimer()
        self.refresh_timer.setInterval(15000)
        self.refresh_timer.timeout.connect(self.on_refresh_timer_timeout)

        self.job_info_window = None

        self.use_progress_control = False

        self.search_panel.setVisible(False)

        self.update_table()
        self.processing_progress.setVisible(False)

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

        #print(self.queue.jobs)
        #print(self.queue.max_nodes)
        #print(self.queue.max_cpus)

        # Get user information

        user = getpass.getuser()

        # Test tableview

        self.queue_model = QueueTableModel(self.queue.jobs, self.queue.max_nodes, self.queue.max_cpus)

        if self.action_show_all_jobs.isChecked():
            self.running_model = QueueSortFilterProxyModel(self, "RUNNING")
            self.running_model.setSourceModel(self.queue_model)
            self.waiting_model = QueueSortFilterProxyModel(self, "PENDING", show_progress=False)
            self.waiting_model.setSourceModel(self.queue_model)
        else:
            self.running_model = QueueSortFilterProxyModel(
                self, "RUNNING", user)
            self.running_model.setSourceModel(self.queue_model)
            self.waiting_model = QueueSortFilterProxyModel(
                self, "PENDING", user, show_progress=False)
            self.waiting_model.setSourceModel(self.queue_model)

        self.running_table_view.setModel(self.running_model)
        self.running_table_view.setItemDelegate(QueueTableDelegate())
        self.running_table_view.setSortingEnabled(True)
        self.running_table_view.resizeColumnsToContents()

        self.waiting_table_view.setModel(self.waiting_model)
        self.waiting_table_view.setSortingEnabled(True)
        self.waiting_table_view.resizeColumnsToContents()

        return

    def get_selected_job_list(self):
        """Get selected job list from table selection."""

        if self.queue_tabs.currentIndex() == 0:
            selected_indexes = self.running_table_view.selectedIndexes()
            selected_model = self.running_model
        else:
            selected_indexes = self.waiting_table_view.selectedIndexes()
            selected_model = self.waiting_model
        
        selected_rows = []

        for selected_index in selected_indexes:
            selected_rows.append(selected_index.row())

        # Extract unique rows

        selected_rows = list(set(selected_rows))

        # Extract job ids

        job_list = []

        for row in selected_rows:
            job_id = selected_model.index(row, 0).data()
            job_list.append(int(job_id))

        return job_list

    @QtCore.pyqtSlot()
    def on_action_show_all_jobs_triggered(self):
        """Toggle showing all jobs event method."""

        self.update_table()
        self.processing_progress.setVisible(False)

    @QtCore.pyqtSlot()
    def on_action_search_triggered(self):
        if not self.action_search.isChecked():
            self.running_model.search_text = ""
            self.waiting_model.search_text = ""
            self.running_model.invalidateFilter()
            self.waiting_model.invalidateFilter()
            self.search_combo.setCurrentText("")

        self.search_panel.setVisible(self.action_search.isChecked())

    @QtCore.pyqtSlot(str)
    def on_search_combo_currentTextChanged(self, text):
        self.running_model.search_text = text
        self.waiting_model.search_text = text
        self.running_model.invalidateFilter()
        self.waiting_model.invalidateFilter()

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

        if len(selected_jobs) > 1:
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

        if len(self.job_info_dict.keys()) > 0:
            self.job_properties.setRowCount(len(self.job_info_dict.keys()))
        else:
            self.job_properties.setRowCount(0)
            return

        row = 0
        for prop, value in self.job_info_dict.items():
            self.job_properties.setItem(
                row, 0, QtWidgets.QTableWidgetItem(str(prop)))
            self.job_properties.setItem(
                row, 1, QtWidgets.QTableWidgetItem(str(value)))
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
                if len(value_pair.split("=")) == 2:
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

class MonitorWindow(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(MonitorWindow, self).__init__(parent)
        self.tool_path = settings.LaunchSettings.create().tool_path

        if len(settings.LaunchSettings.create().args) > 1:
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

        if len(self.remote_probe.gpu_usage) >= 1:
            self.progressGPU1.setEnabled(True)
            self.progressGPU1.setValue(self.remote_probe.gpu_usage[0])
        if len(self.remote_probe.gpu_usage) >= 2:
            self.progressGPU2.setEnabled(True)
            self.progressGPU2.setValue(self.remote_probe.gpu_usage[1])
        if len(self.remote_probe.gpu_usage) >= 3:
            self.progressGPU3.setEnabled(True)
            self.progressGPU3.setValue(self.remote_probe.gpu_usage[2])
        if len(self.remote_probe.gpu_usage) >= 4:
            self.progressGPU4.setEnabled(True)
            self.progressGPU4.setValue(self.remote_probe.gpu_usage[3])
        if len(self.remote_probe.gpu_usage) >= 5:
            self.progressGPU5.setEnabled(True)
            self.progressGPU5.setValue(self.remote_probe.gpu_usage[4])
        if len(self.remote_probe.gpu_usage) >= 6:
            self.progressGPU6.setEnabled(True)
            self.progressGPU6.setValue(self.remote_probe.gpu_usage[4])
        if len(self.remote_probe.gpu_usage) >= 7:
            self.progressGPU7.setEnabled(True)
            self.progressGPU7.setValue(self.remote_probe.gpu_usage[7])
        if len(self.remote_probe.gpu_usage) >= 8:
            self.progressGPU8.setEnabled(True)
            self.progressGPU8.setValue(self.remote_probe.gpu_usage[8])

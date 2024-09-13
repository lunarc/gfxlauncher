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
from . import ui_node_window as ui  

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


class NodeTableDelegate(QtWidgets.QStyledItemDelegate):
    """Delegate class for drawing progress bars."""
    def __init__(self, parent=None):
        super(NodeTableDelegate, self).__init__(parent)

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


class NodeSortFilterProxyModel(QtCore.QSortFilterProxyModel):
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

        try:
            return float(left_data) < float(right_data)
        except ValueError:
            pass

        try:
            return int(left_data) < int(right_data)
        except ValueError:
            pass

        return left_data < right_data

    def search_filter(self, node_id, flag):
        if self.search_text == "":
            return flag
        else:
            if flag:
                model = self.sourceModel()
                print(node_id)
                values = model.node_dict[node_id]
                for key, value in values.items():
                    if self.search_text in str(value):
                        return True
                return False
            else:
                return flag

    def filterAcceptsRow(self, source_row, source_parent):
        """Filter function."""

        model = self.sourceModel()
        node_id = model.node_keys[source_row]

        return self.search_filter(node_id, True)

        

    def filterAcceptsColumn(self, source_column, source_parent):
        return True
    
class NodeTableModel(QtCore.QAbstractTableModel):
    """Queue table model for use with QTableView"""
    def __init__(self, data):
        super(NodeTableModel, self).__init__()

        self.__data = data

        self.__headers = ['Node', 'State', 'CPULoad', 'CPUAlloc', 'CPUTot', 'AllocMem', 'FreeMem',  'RealMemory', 'CoresPerSocket', 'ThreadsPerCore', 'AvailableFeatures', 'Gres',  'Partitions']

        self.__column_keys = self.__headers
        self.__node_keys = list(self.__data.keys())
        self.colors = ["#FFF878", "#FEED73", "#FDE16D", "#FCD668", "#FBCA62", "#FABF5D", "#F9B458", "#F8A852", "#F79D4D", "#F69147", "#F58642"]

        self.__max_values = {}

        self.update_max_values()

    def update_max_values(self):
        """Update maximum values for progress bars"""

        for header in self.__headers:  
            self.__max_values[header] = 0

        for node_key in self.__data.keys():
            value = self.__data[node_key]["CPULoad"]

            try:
                if float(value) > self.__max_values["CPULoad"]:
                    self.__max_values["CPULoad"] = float(value)
            except ValueError:
                pass

    @property
    def max_values(self):
        return self.__max_values


    def headerData(self, section, orientation, role):
        """Return table headers"""
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                return str(self.__headers[section])

            if orientation == QtCore.Qt.Vertical:
                return str(section)



    def data(self, index, role=QtCore.Qt.DisplayRole):
        """Return table data"""
        if role == QtCore.Qt.DisplayRole:

            node_key = self.__node_keys[index.row()]
            node_values = self.__data[node_key]

            value = ""

            if index.column() == 0:
                return str(node_key)
            else:
                try:
                    return str(node_values[self.__column_keys[index.column()]])
                except KeyError:
                    return "N/A"


        if role == QtCore.Qt.BackgroundColorRole:
            
            node_key = self.__node_keys[index.row()]
            node_values = self.__data[node_key]

            if index.column() == 1:
                state = node_values["State"]
                if state == "IDLE":
                    return QtGui.QColor(0, 200, 0)
                elif state == "IDLE+RESERVED":
                    return QtGui.QColor(0, 170, 0)
                elif state == "IDLE+PLANNED":
                    return QtGui.QColor(0, 170, 0)
                elif state == "ALLOCATED":
                    return QtGui.QColor(200, 100, 0)
                elif state == "DOWN":
                    return QtGui.QColor(140, 140, 140)
                elif state == "DOWN+NOT_RESPONDING":
                    return QtGui.QColor(140, 140, 140)
                elif state == "DOWN+INVALID_REG":
                    return QtGui.QColor(140, 140, 140)
                elif state == "MIXED":
                    return QtGui.QColor(200, 200, 0)
                elif state == "MIXED+RESERVED":
                    return QtGui.QColor(170, 170, 0)
                elif state == "RESERVED":
                    return QtGui.QColor(0, 50, 200)
                else:
                    return None
                
            elif index.column() == 2:
                try:
                    cpuload = float(node_values["CPULoad"])
                    return QtGui.QColor(self.colors[int(math.floor((len(self.colors)-1)*cpuload/self.max_values["CPULoad"]))])
                except ValueError:
                    return None
            else:
                return None

        if role == QtCore.Qt.TextAlignmentRole:

            if index.column() == 0:
                return QtCore.Qt.AlignVCenter | QtCore.Qt.AlignCenter
            elif index.column() == 10 or index.column() == 11 or index.column() == 12:
                return QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft
            else:
                return QtCore.Qt.AlignVCenter | QtCore.Qt.AlignCenter

    @property
    def node_keys(self):
        return self.__node_keys
    
    @property
    def headers(self):
        return self.__headers
    
    @property
    def node_dict(self):
        return self.__data


    def rowCount(self, index):
        """Return table rows"""
        return len(self.__data.keys())

    def columnCount(self, index):
        """Return table columns"""
        return len(self.__headers)


class NodeWindow(QtWidgets.QMainWindow, ui.Ui_MainWindow):
    """Session Window class"""

    def __init__(self, parent=None):
        super(NodeWindow, self).__init__(parent)
        self.setupUi(self)

        self.slurm = lrms.Slurm()

        if not self.slurm.check_environment():
            QtWidgets.QMessageBox.information(
                self, "GfxLauncher", "SLURM not available. Please contact support.")
            sys.exit(1)

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

        nodes = self.slurm.query_nodes()

        #print(self.queue.jobs)
        #print(self.queue.max_nodes)
        #print(self.queue.max_cpus)

        # Test tableview

        self.node_model = NodeTableModel(nodes)
        self.node_proxy_model = NodeSortFilterProxyModel(self)
        self.node_proxy_model.setSourceModel(self.node_model)
        self.node_proxy_model.setFilterKeyColumn(1)

        self.node_view_table.setModel(self.node_proxy_model)
        #self.node_view_table.setItemDelegate(NodeTableDelegate())
        self.node_view_table.setSortingEnabled(True)
        self.node_view_table.resizeColumnsToContents()
        self.node_view_table.sortByColumn(0, QtCore.Qt.AscendingOrder)


        return

    @QtCore.pyqtSlot()
    def on_action_show_all_jobs_triggered(self):
        """Toggle showing all jobs event method."""

        self.update_table()
        self.processing_progress.setVisible(False)

    @QtCore.pyqtSlot()
    def on_action_search_triggered(self):
        if not self.action_search.isChecked():
            self.node_proxy_model.search_text = ""
            self.node_proxy_model.invalidateFilter()
            self.search_combo.setCurrentText("")

        self.search_panel.setVisible(self.action_search.isChecked())

    @QtCore.pyqtSlot(str)
    def on_search_combo_currentTextChanged(self, text):
        self.node_proxy_model.search_text = text
        self.node_proxy_model.invalidateFilter()

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



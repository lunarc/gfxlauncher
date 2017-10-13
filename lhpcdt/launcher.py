"""LUNARC HPC Desktop Launcher Module"""

import os
import sys
import getpass
from datetime import datetime

from PyQt4 import QtCore, QtGui, uic

import jobs
import lrms
import remote
import settings


class WriteStream(object):
    """Class for synchronised stream writing"""

    def __init__(self, queue):
        self.queue = queue

    def write(self, text):
        self.queue.put(text)


class OutputReceiver(QtCore.QObject):
    """Receiver thread for synchronised access to queued output"""
    mysignal = QtCore.pyqtSignal(str)

    def __init__(self, queue, *args, **kwargs):
        QtCore.QObject.__init__(self, *args, **kwargs)
        self.queue = queue

    @QtCore.pyqtSlot()
    def run(self):
        while True:
            text = self.queue.get()
            self.mysignal.emit(text)


class SubmitThread(QtCore.QThread):
    """Job submission thread"""
    NO_ERROR = 0
    SUBMIT_FAILED = 1

    def __init__(self, job, cmd="xterm", opengl=False, vglrun=True):
        QtCore.QThread.__init__(self)

        self.job = job
        self.cmd = cmd
        self.opengl = opengl

        self.ssh = remote.SSH()
        self.vgl = remote.VGLConnect()
        self.vgl.vglrun = vglrun
        self.slurm = lrms.Slurm()

        self.error_status = SubmitThread.NO_ERROR

    def run(self):
        """Main thread method"""

        print("Submitting job...")

        if not self.slurm.submit(self.job):
            print("Failed to submit job.")
            self.error_status = SubmitThread.SUBMIT_FAILED
            return
        else:
            print("Job %d submitted." % self.job.id)

        print("Waiting for job to start...")
        self.slurm.wait_for_start(self.job)
        self.slurm.job_status(self.job)
        print("Job has started on node %s." % self.job.nodes)

        print("Starting graphical application on node.")

        if self.opengl:
            print("Executing command on node (OpenGL)...")
            self.vgl.execute(self.job.nodes, self.cmd)
            print("Completed.")
        else:
            print("Executing command on node...")
            self.ssh.execute(self.job.nodes, self.cmd)
            print("Completed.")


class SessionWindow(QtGui.QWidget):
    """Session Window class"""

    def __init__(self, parent=None):
        super(SessionWindow, self).__init__(parent)
        self.slurm = lrms.Slurm()
        self.queue = lrms.Queue()

        uic.loadUi("../session_manager.ui", self)

        self.update_table()

    def update_table(self):
        print("update_table")

        self.queue.update()

        user = getpass.getuser()

        self.sessionTable.setColumnCount(9)

        if user in self.queue.userJobs:
            self.sessionTable.setRowCount(
                len(self.queue.userJobs[user].keys()))
        else:
            self.sessionTable.setRowCount(0)
            return

        self.sessionTable.setColumnCount(9)
        self.sessionTable.setHorizontalHeaderLabels(
            ["Id", "Name", "State", "Time",
             "Requested", "Count", "Nodes", "", ""]
            )

        row = 0
        for id in self.queue.userJobs[user].keys():
            self.sessionTable.setItem(row, 0, QtGui.QTableWidgetItem(str(id)))
            self.sessionTable.setItem(row, 1, QtGui.QTableWidgetItem(
                str(self.queue.userJobs[user][id]["name"])))
            self.sessionTable.setItem(row, 2, QtGui.QTableWidgetItem(
                str(self.queue.userJobs[user][id]["state"])))
            self.sessionTable.setItem(row, 3, QtGui.QTableWidgetItem(
                str(self.queue.userJobs[user][id]["time"])))
            self.sessionTable.setItem(row, 4, QtGui.QTableWidgetItem(
                str(self.queue.userJobs[user][id]["timelimit"])))
            self.sessionTable.setItem(row, 5, QtGui.QTableWidgetItem(
                str(self.queue.userJobs[user][id]["nodes"])))
            self.sessionTable.setItem(row, 6, QtGui.QTableWidgetItem(
                str(self.queue.userJobs[user][id]["nodelist"])))

            cancelButton = QtGui.QPushButton("Cancel")
            cancelButton.clicked.connect(self.cancel_button_clicked)
            infoButton = QtGui.QPushButton("Info")
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


class GfxLaunchWindow(QtGui.QMainWindow):
    """Main launch window user interface"""

    def __init__(self, parent=None):
        """Launch window constructor"""
        super(GfxLaunchWindow, self).__init__(parent)

        # Initialise properties

        self.slurm = lrms.Slurm()
        self.args = settings.LaunchSettings.create().args
        self.tool_path = settings.LaunchSettings.create().tool_path

        # Setup default launch properties

        self.init_defaults()

        # Get changes from command line

        self.get_defaults_from_cmdline()

        # Where can we find the user interface definitions (ui-files)

        ui_path = os.path.join(self.tool_path, "ui")

        # Load appropriate user interface

        if self.simplified:
            uic.loadUi(os.path.join(ui_path, "mainwindow_simplified.ui"), self)
        else:
            uic.loadUi(os.path.join(ui_path, "mainwindow.ui"), self)

        # Update controls to reflect parameters

        self.update_controls()

        # Setup timer callback for updating job status

        self.statusTimer = QtCore.QTimer()
        self.statusTimer.timeout.connect(self.on_status_timeout)

    def time_to_decimal(self, time_string):
        """Time to decimal conversion routine"""
        h = "0"
        m = "0"
        s = "0"

        if len(time_string.split(':')) == 2:
            (m, s) = time_string.split(':')
        elif len(time_string.split(':')) == 3:
            (h, m, s) = time_string.split(':')

        return int(h) * 3600 + int(m) * 60 + int(s)

    def init_defaults(self):
        """Basic property defaults"""
        self.time = "00:30:00"
        self.memory = "2048"
        self.count = 1
        self.exclusive = False
        self.vgl = False
        self.vglrun = False
        self.account = "erik-test"
        self.part = "erik"
        self.cmd = "xterm"
        self.title = "Lunarc HPC Desktop Launcher"
        self.simplified = False
        self.running = False
        self.job = None

    def get_defaults_from_cmdline(self):
        """Get properties from command line"""
        self.memory = self.args.memory
        self.count = self.args.count
        self.exclusive = self.args.exclusive
        self.vgl = self.args.useVGL
        self.vglrun = self.args.use_vglrun
        self.account = self.args.account
        self.cmd = self.args.cmdLine
        self.time = self.args.time
        self.title = self.args.title
        self.part = self.args.part
        self.simplified = self.args.simplified

    def update_properties(self):
        """Get properties from user interface"""
        if not self.simplified:
            self.time = self.wallTimeEdit.text()
            self.memory = self.memoryEdit.text()
            self.count = self.cpuCountSpin.value()
            self.exclusive = self.exclusiveCheck.isChecked()
            self.vgl = self.openGLCheck.isChecked()
            self.account = self.accountEdit.text()
            self.cmd = self.executableEdit.text()
            self.part = self.partitionCombo.currentText()
        else:
            self.time = self.wallTimeEdit.text()

    def update_controls(self):
        """Update user interface from properties"""

        self.slurm.query_partitions()

        if self.running:
            self.cancelButton.setEnabled(True)
            self.startButton.setEnabled(False)
            self.oneHourRadio.setEnabled(False)
            self.twoHourRadio.setEnabled(False)
            self.sixHourRadio.setEnabled(False)
            self.twelveHourRadio.setEnabled(False)
            self.twentyFourHourRadio.setEnabled(False)
            self.wallTimeEdit.setEnabled(False)
            self.usageBar.setEnabled(True)
            p = self.runningFrame.palette()
            p.setColor(self.runningFrame.backgroundRole(), QtCore.Qt.green)
            self.runningFrame.setPalette(p)
        else:
            self.cancelButton.setEnabled(False)
            self.startButton.setEnabled(True)
            self.oneHourRadio.setEnabled(True)
            self.twoHourRadio.setEnabled(True)
            self.sixHourRadio.setEnabled(True)
            self.twelveHourRadio.setEnabled(True)
            self.twentyFourHourRadio.setEnabled(True)
            self.wallTimeEdit.setEnabled(True)
            self.usageBar.setEnabled(False)
            self.usageBar.setValue(0)
            p = self.runningFrame.palette()
            p.setColor(self.runningFrame.backgroundRole(), QtCore.Qt.gray)
            self.runningFrame.setPalette(p)

        if not self.simplified:
            default_part_idx = -1
            i = 0

            for partition in self.slurm.partitions:
                self.partitionCombo.addItem(partition)
                if self.part == partition:
                    default_part_idx = i
                i += 1

            if default_part_idx != -1:
                self.partitionCombo.setCurrentIndex(default_part_idx)

        if not self.simplified:
            self.memoryEdit.setText(str(self.memory))
            self.cpuCountSpin.setValue(int(self.count))
            self.exclusiveCheck.setChecked(self.exclusive)
            self.openGLCheck.setChecked(self.vgl)
            self.accountEdit.setText(self.account)
            self.executableEdit.setText(self.cmd)
            self.wallTimeEdit.setText(str(self.time))
        else:
            self.wallTimeEdit.setText(str(self.time))

        if self.args.title != "":
            self.setWindowTitle(self.args.title)

    def closeEvent(self, event):
        """Handle window close event"""
        if self.job is not None:
            self.slurm.cancel_job(self.job)
        event.accept()  # let the window close

    def on_submit_finished(self):
        """Event called from submit thread when job has been submitted"""
        self.running = True
        self.statusTimer.start(5000)
        self.update_controls()

    def on_status_timeout(self):
        """Status timer callback. Updates job status."""
        if self.job is not None:
            if self.slurm.is_running(self.job):
                timeRunning = self.time_to_decimal(self.job.timeRunning)
                timeLimit = self.time_to_decimal(self.job.timeLimit)
                percent = 100 * timeRunning / timeLimit
                self.usageBar.setValue(int(percent))
            else:
                self.running = False
                self.statusTimer.stop()
                self.usageBar.setValue(0)
                self.update_controls()

    @QtCore.pyqtSlot()
    def on_startButton_clicked(self):
        """Submit placeholder job"""

        self.update_properties()

        self.job = jobs.PlaceHolderJob()
        self.job.account = str(self.account)
        self.job.partition = str(self.part)
        self.job.time = str(self.time)
        self.job.memory = int(self.memory)
        self.job.nodeCount = int(self.count)
        self.job.exclusive = self.exclusive
        self.job.update()

        self.submitThread = SubmitThread(self.job, self.cmd, self.vgl, self.vglrun)
        self.submitThread.finished.connect(self.on_submit_finished)
        self.submitThread.start()

        self.startButton.setEnabled(False)

    @QtCore.pyqtSlot()
    def on_closeButton_clicked(self):
        """User asked to close window"""

        if self.job is not None:
            self.slurm.cancel_job(self.job)
        self.close()

    @QtCore.pyqtSlot()
    def on_cancelButton_clicked(self):
        """Cancel running job"""

        if self.job is not None:
            self.slurm.cancel_job(self.job)

        self.running = False
        self.job = None
        self.statusTimer.stop()
        self.update_controls()

    @QtCore.pyqtSlot(str)
    def on_append_text(self, text):
        """Callback for to update status output from standard output"""
        self.statusText.moveCursor(QtGui.QTextCursor.End)
        self.statusText.insertPlainText(text)

    @QtCore.pyqtSlot()
    def on_oneHourRadio_clicked(self):
        """Set walltime"""

        self.wallTimeEdit.setText("00:60:00")

    @QtCore.pyqtSlot()
    def on_twoHourRadio_clicked(self):
        """Set walltime"""

        self.wallTimeEdit.setText("02:00:00")

    @QtCore.pyqtSlot()
    def on_sixHourRadio_clicked(self):
        """Set walltime"""

        self.wallTimeEdit.setText("06:00:00")

    @QtCore.pyqtSlot()
    def on_twelveHourRadio_clicked(self):
        """Set walltime"""

        self.wallTimeEdit.setText("12:00:00")

    @QtCore.pyqtSlot()
    def on_twentyFourHourRadio_clicked(self):
        """Set walltime"""

        self.wallTimeEdit.setText("24:00:00")

"""LUNARC HPC Desktop Launcher Module"""

import os
import getpass
from datetime import datetime

from PyQt4 import QtCore, QtGui, uic

import jobs
import lrms
import remote
import settings
import config


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
        self.active_connection = None

    def run(self):
        """Main thread method"""

        print("Starting session...")

        if not self.slurm.submit(self.job):
            print("Failed to start session.")
            self.error_status = SubmitThread.SUBMIT_FAILED
            return
        else:
            print("Session %d submitted." % self.job.id)

        print("Waiting for session to start...")
        self.slurm.wait_for_start(self.job)
        self.slurm.job_status(self.job)
        print("Session has started on node %s." % self.job.nodes)

        print("Starting graphical application on node.")

        if self.opengl:
            print("Executing command on node (OpenGL)...")
            self.vgl.execute(self.job.nodes, self.cmd)
            self.active_connection = self.vgl
        else:
            print("Executing command on node...")
            self.ssh.execute(self.job.nodes, self.cmd)
            self.active_connection = self.ssh


class MonitorWindow(QtGui.QWidget):
    def __init__(self, parent = None):
        super(MonitorWindow, self).__init__(parent)
        self.tool_path = settings.LaunchSettings.create().tool_path
        self.hostname = settings.LaunchSettings.create().args[1]

        ui_path = os.path.join(self.tool_path, "ui")

        # Load appropriate user interface

        uic.loadUi(os.path.join(ui_path, "monitor.ui"), self)

        self.remote_probe = remote.StatusProbe()
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


class SessionWindow(QtGui.QWidget):
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

class SplashWindow(QtGui.QWidget):
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
        screen = QtGui.QApplication.desktop().screenNumber(QtGui.QApplication.desktop().cursor().pos())
        centerPoint = QtGui.QApplication.desktop().screenGeometry(screen).center()
        frameGm.moveCenter(centerPoint)
        self.move(frameGm.topLeft())

    def on_timeout(self):
        self.statusTimer.stop()
        self.close()

    def on_close_button_clicked(self):
        self.statusTimer.stop()
        self.close()


class GfxLaunchWindow(QtGui.QMainWindow):
    """Main launch window user interface"""

    def __init__(self, parent=None):
        """Launch window constructor"""
        super(GfxLaunchWindow, self).__init__(parent)

        # Initialise properties

        self.slurm = lrms.Slurm()
        self.args = settings.LaunchSettings.create().args
        self.tool_path = settings.LaunchSettings.create().tool_path
        self.copyright_info = settings.LaunchSettings.create().copyright_info
        self.copyright_short_info = settings.LaunchSettings.create().copyright_short_info
        self.version_info = settings.LaunchSettings.create().version_info

        self.config = config.GfxConfig.create()

        self.slurm.query_partitions()
        self.features = self.slurm.query_features(self.config.default_part)

        # Setup default launch properties

        self.init_defaults()

        # Get changes from command line

        self.get_defaults_from_cmdline()

        # Check for available project

        if not self.has_project():
            QtGui.QMessageBox.information(self, self.title, "No project allocation found. Please apply for a project in SUPR.")

        # Where can we find the user interface definitions (ui-files)

        ui_path = os.path.join(self.tool_path, "ui")

        # Load appropriate user interface

        if self.simplified:
            uic.loadUi(os.path.join(ui_path, "mainwindow_simplified.ui"), self)
        else:
            uic.loadUi(os.path.join(ui_path, "mainwindow_advanced.ui"), self)

        # Update controls to reflect parameters

        self.update_controls()

        # Setup timer callback for updating job status

        self.statusTimer = QtCore.QTimer()
        self.statusTimer.timeout.connect(self.on_status_timeout)

        self.versionLabel.setText(self.copyright_short_info % self.version_info)

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

    def has_project(self):
        """Check for user in grantfile"""

        user = getpass.getuser()

        grant_filename = self.config.grantfile

        if self.config.grantfile_base!="":
            grant_filename = self.config.grantfile_base % self.part
        
        grant_file = lrms.GrantFile(grant_filename)

        for project in grant_file.projects.keys():
            if user in grant_file.projects[project]["users"]:
                print("Found user %s in project %s in grantfile %s" % (user, project, grant_filename))
                self.account = project
                return True

        return False


    def init_defaults(self):
        """Basic property defaults"""
        self.time = "00:30:00"
        self.memory = "2048"
        self.count = 1
        self.exclusive = False
        self.vgl = False
        self.vglrun = False
        self.account = self.config.default_account
        self.part = self.config.default_part
        self.cmd = "xterm"
        self.title = "Lunarc HPC Desktop Launcher"
        self.simplified = False
        self.running = False
        self.job = None
        self.selected_feature = ""

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
        self.time = self.wallTimeEdit.currentText()

        if not self.simplified:
            self.memory = self.memoryEdit.text()
            self.count = self.cpuCountSpin.value()
            self.exclusive = self.exclusiveCheck.isChecked()
            self.account = self.accountEdit.text()
            self.part = self.partitionCombo.currentText()

        if self.featureCombo.currentIndex() != -1:
            self.selected_feature = self.filtered_features[self.featureCombo.currentIndex()]
        else:
            self.selected_feature = ""

        #self.vgl = self.openGLCheck.isChecked()
        #self.cmd = self.executableEdit.text()

    def update_controls(self):
        """Update user interface from properties"""

        self.slurm.query_partitions()

        self.filtered_features = []
        self.filtered_features.append("")

        self.featureCombo.clear()
        self.featureCombo.addItem("None")

        for feature in self.features:
            if feature.find("mem") != -1:
                if self.config.feature_descriptions.has_key(feature.lower()):
                    self.featureCombo.addItem(self.config.feature_descriptions[feature.lower()])
                else:
                    self.featureCombo.addItem(feature)
                self.filtered_features.append(feature)
            elif feature.find("gpu") != -1:
                if self.config.feature_descriptions.has_key(feature.lower()):
                    self.featureCombo.addItem(self.config.feature_descriptions[feature.lower()])
                else:
                    self.featureCombo.addItem(feature)
                self.filtered_features.append(feature)

        selected_index = -1
        selected_count = 0

        for feature in self.filtered_features:
            if feature == self.selected_feature:
                selected_index = selected_count
            selected_count += 1

        if selected_index != -1:
            self.featureCombo.setCurrentIndex(selected_index)
        else:
            self.featureCombo.setCurrentIndex(0)

        if self.running:
            self.cancelButton.setEnabled(True)
            self.startButton.setEnabled(False)
            #self.oneHourRadio.setEnabled(False)
            #self.twoHourRadio.setEnabled(False)
            #self.sixHourRadio.setEnabled(False)
            #self.twelveHourRadio.setEnabled(False)
            #self.twentyFourHourRadio.setEnabled(False)
            self.usageBar.setEnabled(True)
            p = self.runningFrame.palette()
            p.setColor(self.runningFrame.backgroundRole(), QtCore.Qt.green)
            self.runningFrame.setPalette(p)
            self.wallTimeEdit.setEnabled(False)

            if not self.simplified:
                self.cpuCountSpin.setEnabled(False)
                self.memoryEdit.setEnabled(False)
                self.exclusiveCheck.setEnabled(False)
                self.accountEdit.setEnabled(False)
                self.partitionCombo.setEnabled(False)
    
        else:
            self.cancelButton.setEnabled(False)
            self.startButton.setEnabled(True)
            #self.oneHourRadio.setEnabled(True)
            #self.twoHourRadio.setEnabled(True)
            #self.sixHourRadio.setEnabled(True)
            #self.twelveHourRadio.setEnabled(True)
            #self.twentyFourHourRadio.setEnabled(True)
            self.usageBar.setEnabled(False)
            self.usageBar.setValue(0)
            p = self.runningFrame.palette()
            p.setColor(self.runningFrame.backgroundRole(), QtCore.Qt.gray)
            self.runningFrame.setPalette(p)
            self.wallTimeEdit.setEnabled(True)

            if not self.simplified:
                self.cpuCountSpin.setEnabled(True)
                self.memoryEdit.setEnabled(True)
                self.exclusiveCheck.setEnabled(True)
                self.accountEdit.setEnabled(True)
                self.partitionCombo.setEnabled(True)
            

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
            #self.openGLCheck.setChecked(self.vgl)
            self.accountEdit.setText(self.account)
            #self.executableEdit.setText(self.cmd)
            self.wallTimeEdit.setEditText(str(self.time))
        else:
            self.wallTimeEdit.setEditText(str(self.time))
            self.projectEdit.setText(str(self.account))

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
        self.active_connection = self.submitThread.active_connection

        if self.submitThread.error_status == SubmitThread.SUBMIT_FAILED:
            QtGui.QMessageBox.about(self, self.title, "Session start failed.")
            self.running = False
            self.statusTimer.stop()
            self.update_controls()
            self.active_connection = None

    def on_status_timeout(self):
        """Status timer callback. Updates job status."""
        if self.job is not None:
            if self.slurm.is_running(self.job):
                timeRunning = self.time_to_decimal(self.job.timeRunning)
                timeLimit = self.time_to_decimal(self.job.timeLimit)
                percent = 100 * timeRunning / timeLimit
                self.usageBar.setValue(int(percent))

                if not self.active_connection.is_active():
                    print("Active connection closed. Terminating session.")
                    self.running = False
                    self.statusTimer.stop()
                    self.usageBar.setValue(0)
                    self.update_controls()
                    if self.job is not None:
                        self.slurm.cancel_job(self.job)
                    
            else:
                print("Session completed.")
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
        self.job.nodeCount = self.count
        self.job.partition = str(self.part)
        self.job.time = str(self.time)
        self.job.memory = int(self.memory)
        self.job.nodeCount = int(self.count)
        self.job.exclusive = self.exclusive
        if self.selected_feature != "":
            self.job.add_constraint(self.selected_feature)
        self.job.update()

        print(self.job)

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
        now = datetime.now()        
        self.statusText.moveCursor(QtGui.QTextCursor.End)
        if text!="\n":
            self.statusText.insertPlainText(now.strftime("[%H:%M:%S] ") + text)
        else:
            self.statusText.insertPlainText(text)

        self.statusText.moveCursor(QtGui.QTextCursor.StartOfLine)

#    @QtCore.pyqtSlot(int)
#    def on_featureCombo_currentIndexChanged(self, idx):
#        """Handle feature selection"""
#
#        self.selected_feature = self.filtered_features[idx]
#        print(self.selected_feature)
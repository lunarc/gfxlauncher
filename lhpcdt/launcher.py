#!/bin/env python
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

"""
LUNARC HPC Desktop Launcher Module

This module implements the main user interface of the application 
launcher.
"""

import os, sys, time, glob, getpass
from datetime import datetime

from PyQt5 import Qt, QtCore, QtGui, QtWidgets, uic

from . import jobs
from . import lrms
from . import remote
from . import settings
from . import config
from . import resource_win

from subprocess import Popen, PIPE, STDOUT


class WriteStream(object):
    """Class for synchronised stream writing"""

    def __init__(self, queue):
        self.queue = queue

    def write(self, text):
        self.queue.put(text)

    def flush(self):
        pass


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

    def __init__(self, job, cmd="xterm", opengl=False, vglrun=True, only_submit=False, vgl_path=""):
        QtCore.QThread.__init__(self)

        self.job = job
        self.cmd = cmd
        self.opengl = opengl
        self.only_submit = only_submit

        self.ssh = remote.SSH()

        self.vgl = remote.VGLConnect()
        self.vgl.vglrun = vglrun

        if vgl_path!="":
            self.vgl_path = vgl_path

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

        if not self.only_submit:

            print("Starting graphical application on node.")

            if self.opengl:
                print("Executing command on node (OpenGL)...")

                self.vgl.execute(self.job.nodes, self.cmd)
                self.active_connection = self.vgl
            else:
                print("Executing command on node...")

                self.ssh.execute(self.job.nodes, self.cmd)
                self.active_connection = self.ssh


class GfxLaunchWindow(QtWidgets.QMainWindow):
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
        self.rdp = None

        self.reconnect_nb_button = None
        self.reconnect_vm_button = None

        # Read configuration

        self.config = config.GfxConfig.create()

        if not self.config.is_ok:
            print("Please check configuration.")
            sys.exit(1)

        # Parse partition and feature excludes

        self.feature_ignore = self.config.feature_ignore[1:-1]
        self.feature_exclude_set = set(self.feature_ignore.split(","))

        self.part_ignore = self.config.part_ignore[1:-1]
        self.part_exclude_set = set(self.part_ignore.split(","))

        # Setup default launch properties

        self.init_defaults()

        # Get changes from command line

        self.get_defaults_from_cmdline()

        # Query partition features

        self.slurm.query_partitions(exclude_set=self.part_exclude_set)

        self.features = self.slurm.query_features(self.part, self.feature_exclude_set)
        self.selected_part = self.part

        # Check for available project

        if not self.has_project() and not self.args.ignore_grantfile:
            QtWidgets.QMessageBox.information(
                self, self.title, "No project allocation found. Please apply for a project in SUPR.")

        # Where can we find the user interface definitions (ui-files)

        ui_path = os.path.join(self.tool_path, "ui")

        # Load appropriate user interface

        uic.loadUi(os.path.join(ui_path, "mainwindow_simplified.ui"), self)

        # Update controls to reflect parameters

        self.update_controls()

        # Setup timer callback for updating job status

        self.statusTimer = QtCore.QTimer()
        self.statusTimer.timeout.connect(self.on_status_timeout)

        self.status_output.setText(
            self.copyright_short_info % self.version_info)

        # Setup timer for autostart

        self.autostart_timer = QtCore.QTimer()
        self.autostart_timer.timeout.connect(self.on_autostart_timeout)
        
        if self.autostart:
            self.autostart_timer.start(2000)

        # Hide detail tabs

        self.launcherTabs.setHidden(True)
        self.adjustSize()

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

    def has_project(self):
        """Check for user in grantfile"""

        if self.args.ignore_grantfile:
            return False

        if self.user == "":
            user = getpass.getuser()
        else:
            user = self.user

        grant_filename = self.config.grantfile

        #if self.config.grantfile_base != "":
        #    grant_filename = self.config.grantfile_base % self.part

        self.grantfile_list = []

        # --- If we have a explicit grantfile use that only.

        if self.grant_filename != "":

            print("Explicit grantfile %s used." % self.grant_filename)

            grant_filename = self.grant_filename
            self.grantfile_list.append(lrms.GrantFile(grant_filename))
        else:
            # --- No explicit grantfile given. Search for grantfiles

            if self.config.grantfile_dir != "":

                # --- Grant file directory given. Search it for grantfiles

                print("Searching for grantfiles in %s." % self.config.grantfile_dir)

                grant_files = glob.glob(self.config.grantfile_dir+'/grantfile.*')

                for grant_filename in grant_files:
                    if (not '~' in grant_filename) and (len(grant_filename.split("."))==2):
                        suffix = grant_filename.split('.')[1]
                        if self.config.grantfile_suffix=='':
                            print("Parsing grantfile: %s" % grant_filename)
                            self.grantfile_list.append(lrms.GrantFile(grant_filename))
                        elif self.config.grantfile_suffix == suffix:
                            print("Parsing grantfile (suffix match): %s" % grant_filename)
                            self.grantfile_list.append(lrms.GrantFile(grant_filename))
            else:

                # --- Do we have a grantile_base directive?

                grant_filename = self.config.grantfile_base % self.part
                if os.path.exists(grant_filename):
                    self.grantfile_list.append(lrms.GrantFile(grant_filename))

        self.active_projects = []
                
        if len(self.grantfile_list)>0:

            for grant_file in self.grantfile_list:
                self.active_projects += grant_file.query_active_projects(user)

            if len(self.active_projects) > 0:
                self.account = self.active_projects[0]
                return True
            else:
                return False
        else:
            return False

    def init_defaults(self):
        """Basic property defaults"""

        self.time = "00:30:00"
        self.memory = "2048"
        self.count = 1
        self.exclusive = False
        self.vgl = False
        self.vglrun = False
        self.vgl_path = self.config.vgl_path
        self.account = self.config.default_account
        self.part = self.config.default_part
        self.grant_filename = ""
        self.cmd = "xterm"
        self.title = "Lunarc HPC Desktop Launcher"
        self.simplified = True
        self.running = False
        self.job = None
        self.selected_feature = ""
        self.selected_part = self.part
        self.only_submit = False
        self.job_type = ""
        self.job_name = "lhpc"
        self.tasks_per_node = 1
        self.cpus_per_task = 1
        self.no_requeue = False
        self.user = ""
        self.notebook_module = self.config.notebook_module
        self.jupyterlab_module = self.config.jupyterlab_module
        self.autostart = False
        self.locked = False
        self.group = ""

    def get_defaults_from_cmdline(self):
        """Get properties from command line"""

        self.memory = self.args.memory
        self.count = self.args.count
        self.exclusive = self.args.exclusive
        self.vgl = self.args.useVGL
        self.vglrun = self.args.use_vglrun
        self.part = self.args.part
        self.account = self.args.account
        self.grant_filename = self.args.grant_filename
        self.cmd = self.args.cmdLine
        self.time = self.args.time
        self.title = self.args.title
        self.simplified = True
        self.only_submit = self.args.only_submit
        self.job_type = self.args.job_type
        self.job_name = self.args.job_name
        self.tasks_per_node = self.args.tasks_per_node
        self.cpus_per_task = self.args.cpus_per_task
        self.no_requeue = self.args.no_requeue
        self.user = self.args.user
        self.notebook_module = self.args.notebook_module
        self.jupyterlab_module = self.args.jupyterlab_module
        self.autostart = self.args.autostart
        self.locked = self.args.locked
        self.group = self.args.group

    def update_status_panel(self, text):
        self.status_output.setText(text)

    def reset_status_panel(self):
        self.status_output.setText(
            self.copyright_short_info % self.version_info)

    def update_properties(self):
        """Get properties from user interface"""
        self.time = self.wallTimeEdit.currentText()

        if self.featureCombo.currentIndex() != -1:
            self.selected_feature = self.filtered_features[self.featureCombo.currentIndex(
            )]
        else:
            self.selected_feature = ""

        if self.partCombo.currentIndex() != -1:
            self.selected_part = self.filtered_parts[self.partCombo.currentIndex(
            )]
        else:
            self.selected_part = ""

        self.part = self.selected_part

    def update_feature_combo(self):
        """Update only feature combo box."""

        self.features = self.slurm.query_features(self.selected_part, self.feature_exclude_set)

        self.filtered_features = []
        self.filtered_features.append("")

        self.featureCombo.clear()
        self.featureCombo.addItem("None")

        for feature in self.features:
            if feature.lower() in self.config.feature_descriptions:
                self.featureCombo.addItem(
                    self.config.feature_descriptions[feature.lower()])
            else:
                self.featureCombo.addItem(feature)
            self.filtered_features.append(feature)

    def update_controls(self):
        """Update user interface from properties"""

        if self.job_type == "":
            self.launcherTabs.removeTab(2)

        self.slurm.query_partitions(exclude_set=self.part_exclude_set)

        self.update_feature_combo()

        if self.partCombo.count()==0:

            self.filtered_parts = []
            self.filtered_parts.append("")

            self.partCombo.clear()
            self.partCombo.addItem("None")

            for part in self.slurm.partitions:
                descr = part                
                if part.lower() in self.config.partition_descriptions:
                    descr = self.config.partition_descriptions[part.lower()]

                if self.group == "" or (part in self.config.part_groups[self.group]):
                    self.partCombo.addItem(descr)
                    self.filtered_parts.append(part)

        if self.projectCombo.count()==0:

            self.projectCombo.clear()
            for project in self.active_projects:
                self.projectCombo.addItem(project)

            self.projectCombo.setCurrentIndex(0)

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

        selected_index = -1
        selected_count = 0

        for part in self.filtered_parts:
            if part == self.selected_part:
                selected_index = selected_count
            selected_count += 1

        if selected_index != -1:
            self.partCombo.setCurrentIndex(selected_index)
        else:
            self.partCombo.setCurrentIndex(0)

        if self.running:
            self.cancelButton.setEnabled(True)
            self.startButton.setEnabled(False)
            self.usageBar.setEnabled(True)
            p = self.runningFrame.palette()
            p.setColor(self.runningFrame.backgroundRole(), QtCore.Qt.green)
            self.runningFrame.setPalette(p)
            self.wallTimeEdit.setEnabled(False)
        else:
            if not self.locked:
                self.cancelButton.setEnabled(False)
                self.startButton.setEnabled(True)
                self.usageBar.setEnabled(False)
                self.usageBar.setValue(0)
                p = self.runningFrame.palette()
                p.setColor(self.runningFrame.backgroundRole(), QtCore.Qt.gray)
                self.runningFrame.setPalette(p)
                self.wallTimeEdit.setEnabled(True)

        self.wallTimeEdit.setEditText(str(self.time))
        #self.projectEdit.setText(str(self.account))

        if self.args.title != "":
            self.setWindowTitle(self.args.title)

    def enableExtrasPanel(self):
        """Clear user interface components in extras panel"""

        self.extraControlsLayout.setEnabled(True)

        if not self.reconnect_vm_button is None:
            self.reconnect_vm_button.setEnabled(True)
        if not self.reconnect_nb_button is None:
            self.reconnect_nb_button.setEnabled(True)

    def disableExtrasPanel(self):
        """Clear user interface components in extras panel"""

        self.extraControlsLayout.setEnabled(False)

        if not self.reconnect_vm_button is None:
            self.reconnect_vm_button.setEnabled(False)
        if not self.reconnect_nb_button is None:
            self.reconnect_nb_button.setEnabled(False)

    def closeEvent(self, event):
        """Handle window close event"""

        if self.job is not None:
            self.slurm.cancel_job(self.job)

        if self.rdp!=None:
            self.rdp.terminate()

        event.accept()  # let the window close

    def submit_job(self):
        """Submit placeholder job"""

        self.update_properties()

        self.disableExtrasPanel()

        # Note - This should be modularised

        if self.job_type == "":

            # Create a standard placeholder job

            self.job = jobs.PlaceHolderJob()

        elif self.job_type == "notebook":

            # Create a Jupyter notbook job

            self.job = jobs.JupyterNotebookJob(notebook_module=self.notebook_module)
            self.job.on_notebook_url_found = self.on_notebook_url_found

            # Create extra user interface controls for reconnection

            if self.extraControlsLayout.count() == 0:
                self.reconnect_nb_button = QtWidgets.QPushButton(
                    'Reconnect to notebook', self)
                self.reconnect_nb_button.setEnabled(True)
                self.reconnect_nb_button.clicked.connect(
                    self.on_reconnect_notebook)
                self.extraControlsLayout.addWidget(self.reconnect_nb_button)

            self.launcherTabs.setCurrentIndex(2)

        elif self.job_type == "jupyterlab":

            # Create a Jupyter lab job

            self.job = jobs.JupyterLabJob(jupyterlab_module=self.jupyterlab_module)
            self.job.on_notebook_url_found = self.on_notebook_url_found

            # Create extra user interface controls for reconnection

            if self.extraControlsLayout.count() == 0:
                self.reconnect_nb_button = QtWidgets.QPushButton(
                    'Reconnect to Lab', self)
                self.reconnect_nb_button.setEnabled(True)
                self.reconnect_nb_button.clicked.connect(
                    self.on_reconnect_notebook)
                self.extraControlsLayout.addWidget(self.reconnect_nb_button)

            self.launcherTabs.setCurrentIndex(2)

        elif self.job_type == "vm":

            # Create a VM job

            self.job = jobs.VMJob()
            self.job.on_vm_available = self.on_vm_available

            # Create extra user interface for reconnection to VM.

            if self.extraControlsLayout.count() == 0:
                self.reconnect_vm_button = QtWidgets.QPushButton(
                    'Connect to desktop', self)
                self.reconnect_vm_button.setEnabled(False)
                self.reconnect_vm_button.clicked.connect(self.on_reconnect_vm)
                self.extraControlsLayout.addStretch(1)
                self.extraControlsLayout.addWidget(self.reconnect_vm_button)
                self.extraControlsLayout.addStretch(1)

            self.launcherTabs.setCurrentIndex(2)

        else:
            QtWidgets.QMessageBox.about(
                self, self.title, "Session start failed.")
            return

        # Setup job parameters

        self.job.name = self.job_name
        self.job.account = str(self.projectCombo.currentText())
        self.job.partition = str(self.selected_part)
        self.job.time = str(self.time)
        if self.job_type != "vm":
            self.job.memory = int(self.memory)
            self.job.nodeCount = int(self.count)
            self.job.exclusive = self.exclusive
            self.job.tasksPerNode = int(self.tasks_per_node)
        if self.selected_feature != "":
            self.job.add_constraint(self.selected_feature)
        self.job.update()

        # Create a job submission thread

        self.submitThread = SubmitThread(
            self.job, self.cmd, self.vgl, self.vglrun, self.only_submit, self.vgl_path)
        self.submitThread.finished.connect(self.on_submit_finished)
        self.submitThread.start()

        # Make sure we only manage a single job ;)

        self.startButton.setEnabled(False)


    def on_submit_finished(self):
        """Event called from submit thread when job has been submitted"""

        self.running = True
        self.statusTimer.start(5000)
        self.update_controls()
        self.active_connection = self.submitThread.active_connection

        if self.submitThread.error_status == SubmitThread.SUBMIT_FAILED:
            QtWidgets.QMessageBox.about(
                self, self.title, "Session start failed.")
            self.running = False
            self.statusTimer.stop()
            self.update_controls()
            self.active_connection = None

    def on_notebook_url_found(self, url):
        """Callback when notebook url has been found."""

        self.reset_status_panel()

        Popen("firefox %s" % url, shell=True)

        self.enableExtrasPanel()

    def on_vm_available(self, hostname):
        """Start an RDP session to host"""

        self.reset_status_panel()

        if (hostname!="0.0.0.0") and (hostname!="0.0.0.1"):

            print("Starting RDP: " + hostname)

            self.rdp = remote.XFreeRDP(hostname)
            self.rdp.xfreerdp_path = self.config.xfreerdp_path
            self.rdp.execute()

            self.enableExtrasPanel()
        else:
            if hostname == "0.0.0.0":
                QtWidgets.QMessageBox.information(
                    self, self.title, "An error occured when allocating the Windows session. Try launching the session again. If the problem persists contact support.")

            if hostname == "0.0.0.1":
                QtWidgets.QMessageBox.information(
                    self, self.title, "A windows session was not currently available. Try launching the session again later. If the problem persists contact support.")             

            self.close()


    def on_status_timeout(self):
        """Status timer callback. Updates job status."""

        if self.job is not None:

            # Check job status

            if self.slurm.is_running(self.job):
                timeRunning = self.time_to_decimal(self.job.timeRunning)
                timeLimit = self.time_to_decimal(self.job.timeLimit)
                percent = 100 * timeRunning / timeLimit
                self.usageBar.setValue(int(percent))

                if self.only_submit:

                    # Update status panel

                    self.update_status_panel(self.job.processing_description)

                    # Handle job processing, if any

                    if self.job.process_output:
                        print("Checking job output.")
                        output_lines = self.slurm.job_output(self.job)
                        self.job.do_process_output(output_lines)
                    if self.job.update_processing:
                        self.job.do_update_processing()

                else:

                    # Check for non-active sessions

                    if not self.active_connection.is_active():
                        print("Active connection closed. Terminating session.")
                        self.running = False
                        self.statusTimer.stop()
                        self.usageBar.setValue(0)
                        self.update_controls()
                        if self.job is not None:
                            self.slurm.cancel_job(self.job)

            else:

                # Session has completed. Update UI

                print("Session completed.")
                self.running = False
                self.statusTimer.stop()
                self.usageBar.setValue(0)
                self.update_controls()
                self.disableExtrasPanel()
                
                QtWidgets.QMessageBox.information(
                    self, self.title, "Your application was closed as the session time expired.")


    def on_autostart_timeout(self):
        """Automatically submit jobn"""
        self.autostart_timer.stop()
        self.submit_job()

    def on_reconnect_notebook(self):
        """Reopen connection to notebook."""

        if self.job != None:
            Popen("firefox %s" % self.job.notebook_url, shell=True)

    def on_reconnect_vm(self):
        """Reopen connection to vm"""

        if self.job != None:
            if self.rdp != None:
                self.rdp.terminate()

            self.rdp = remote.XFreeRDP(self.job.hostname)
            self.rdp.xfreerdp_path = self.config.xfreerdp_path
            self.rdp.execute()

    @QtCore.pyqtSlot(int)
    def on_partCombo_currentIndexChanged(self, idx):
        if idx!=0:
            self.selected_part = self.filtered_parts[idx]
        self.update_feature_combo()
        

    @QtCore.pyqtSlot(int)
    def on_launcherTabs_currentChanged(self, idx):
        if idx == 1:
            self.update_properties()

            # Note - This should be modularised

            if self.job_type == "":

                # Create a standard placeholder job

                job = jobs.PlaceHolderJob()

            elif self.job_type == "notebook":

                # Create a Jupyter notbook job

                job = jobs.JupyterNotebookJob()

            elif self.job_type == "jupyterlab":

                # Create a Jupyter notbook job

                job = jobs.JupyterLabJob()

            elif self.job_type == "vm":

                # Create a VM job

                job = jobs.VMJob()

            # Setup job parameters

            job.name = self.job_name
            job.account = str(self.projectCombo.currentText())
            job.partition = str(self.selected_part)
            job.time = str(self.time)
            if self.job_type != "vm":
                job.memory = int(self.memory)
                job.nodeCount = int(self.count)
                job.exclusive = self.exclusive
                job.tasksPerNode = int(self.tasks_per_node)
            if self.selected_feature != "":
                job.add_constraint(self.selected_feature)
            job.update()

            self.batchScriptText.clear()
            self.batchScriptText.insertPlainText(str(job))

    @QtCore.pyqtSlot()
    def on_resourceDetailsButton_clicked(self):
        """Open resources specification window"""

        self.resource_window = resource_win.ResourceSpecWindow(self)
        self.resource_window.setGeometry(self.x()+self.width(), self.y(), self.resource_window.width(), self.resource_window.height())
        self.resource_window.show()

    @QtCore.pyqtSlot()
    def on_startButton_clicked(self):
        """Submit job"""

        self.submit_job()

    @QtCore.pyqtSlot()
    def on_closeButton_clicked(self):
        """User asked to close window"""

        if self.job is not None:
            self.slurm.cancel_job(self.job)

        if self.rdp != None:
            self.rdp.terminate()

        self.close()

    @QtCore.pyqtSlot()
    def on_cancelButton_clicked(self):
        """Cancel running job"""

        if self.job is not None:
            self.slurm.cancel_job(self.job)

        if self.rdp != None:
            self.rdp.terminate()


        self.running = False
        self.job = None
        self.statusTimer.stop()
        self.update_controls()

        self.disableExtrasPanel()

        if self.locked:
            print("Closing launcher")
            self.close()

    @QtCore.pyqtSlot()
    def on_showDetails_clicked(self):
        """Show details on job and script"""

        # Hide detail tabs

        if self.launcherTabs.isHidden():
            self.launcherTabs.setHidden(False)
        else:
            self.launcherTabs.setHidden(True)
            self.resize(0,0)
            self.adjustSize()

    @QtCore.pyqtSlot()
    def on_helpButton_clicked(self):
        """Open help page if set"""

        if self.config.help_url!="":
            Popen("firefox %s" % self.config.help_url, shell=True)


    @QtCore.pyqtSlot(str)
    def on_append_text(self, text):
        """Callback for to update status output from standard output"""

        now = datetime.now()
        self.statusText.moveCursor(QtGui.QTextCursor.End)
        if text != "\n":
            self.statusText.insertPlainText(now.strftime("[%H:%M:%S] ") + text)
        else:
            self.statusText.insertPlainText(text)

        self.statusText.moveCursor(QtGui.QTextCursor.StartOfLine)

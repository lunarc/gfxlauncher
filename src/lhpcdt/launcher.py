#!/bin/env python
#
# LUNARC HPC Desktop On-Demand graphical launch tool
# Copyright (C) 2017-2025 LUNARC, Lund University
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

import os, sys, time, glob, getpass, shutil

try:
    import grp
except:
    pass

from datetime import datetime

from PyQt5 import Qt, QtCore, QtGui, QtWidgets, uic

from . import jobs
from . import job_ui
from . import lrms
from . import remote
from . import settings
from . import config
from . import resource_win
from . import conda_utils as cu
from . import user_config
from . import ui_main_window_simplified as ui

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
        self.running = True

    @QtCore.pyqtSlot()
    def run(self):
        while self.running:
            text = self.queue.get()
            self.mysignal.emit(text)


class SubmitThread(QtCore.QThread):
    """Job submission thread"""
    NO_ERROR = 0
    SUBMIT_FAILED = 1

    def __init__(self, job, cmd="xterm", opengl=False, vglrun=True, vgl_path=""):
        QtCore.QThread.__init__(self)

        self.job = job
        self.cmd = cmd
        self.opengl = opengl

        self.ssh = remote.SSH()

        self.vgl = remote.VGLConnect()
        self.vgl.vglrun = vglrun

        if vgl_path != "":
            self.vgl_path = vgl_path

        self.slurm = lrms.Slurm()
        self.verbose = False
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


class TunnelThread(QtCore.QThread):
    """Job submission thread"""
    NO_ERROR = 0
    SUBMIT_FAILED = 1

    def __init__(self, ssh_tunnel):
        QtCore.QThread.__init__(self)

        self.error_status = SubmitThread.NO_ERROR
        self.ssh_tunnel = ssh_tunnel
        self.connected = False

    def disconnect(self):
        self.connected = False

    def run(self):
        """Main thread method"""

        self.ssh_tunnel.execute()
        self.connected = True

        while self.connected and self.ssh_tunnel.is_active():
            time.sleep(1)

class GfxLaunchWindow(QtWidgets.QMainWindow, ui.Ui_MainWindow):
    """Main launch window user interface"""

    def __init__(self, parent=None):
        """Launch window constructor"""
        super(GfxLaunchWindow, self).__init__(parent)

        self.setupUi(self)

        self.__console_output = sys.stdout
        self.__redirect_thread = None
        self.error_log = []

        print("Initialising launch window...")

        # Initialise properties

        self.slurm = lrms.Slurm()
        self.slurm.verbose = False
        self.args = settings.LaunchSettings.create().args
        self.tool_path = settings.LaunchSettings.create().tool_path
        self.copyright_info = settings.LaunchSettings.create().copyright_info
        self.copyright_short_info = settings.LaunchSettings.create().copyright_short_info
        self.version_info = settings.LaunchSettings.create().version_info
        self.rdp = None
        self.job = None

        # SSH/VGL handling

        self.connection_after_thread = True

        self.reconnect_nb_button = None
        self.reconnect_vm_button = None

        # Read configuration

        self.config = config.GfxConfig.create()

        if not self.config.is_ok:
            QtWidgets.QMessageBox.information(self, 'Error', self.config.errors)
            sys.exit(1)

        # Set up user configuration

        self.user_config = user_config.UserConfig()
        self.user_config.setup()

        # Parse partition and feature excludes

        self.feature_ignore = self.config.feature_ignore[1:-1]

        if self.feature_ignore == "":
            self.feature_exclude_set = set()
        else:
            self.feature_exclude_set = set(self.feature_ignore.split(","))

        self.part_ignore = self.config.part_ignore[1:-1]

        if self.part_ignore == "":
            self.part_exclude_set = set()
        else:
            self.part_exclude_set = set(self.part_ignore.split(","))     

        print("Ignoring features   : "+','.join(list(self.feature_exclude_set)))
        print("Ignoring partitions : "+','.join(list(self.part_exclude_set)))

        # Setup default launch properties

        self.init_defaults() 

        # Get changes from command line

        self.get_defaults_from_cmdline()

        # Check for valid SLURM installation

        if not self.slurm.check_environment():
            QtWidgets.QMessageBox.information(
                self, self.title, "SLURM not available. Please contact support.")
            sys.exit(1)

        # Query partition features

        self.slurm.query_partitions(exclude_set=self.part_exclude_set)

        available_parts = []

        if (self.group != ""):
            if (self.group in self.config.part_groups):
                available_parts = self.config.part_groups[self.group]

        if (len(available_parts) == 0) and (self.part!=None):
            available_parts.append(self.part)

        available_parts = list(set(available_parts))

        print("Available parts     : "+','.join(available_parts))

        if len(available_parts)!=0:
            if not self.part in available_parts:
                self.part = available_parts[0]

        self.features = self.slurm.query_features(
            self.part, self.feature_exclude_set)

        self.selected_part = self.part

        print("Selected part       : "+str(self.part))
        print("With features       : "+','.join(self.features))

        # Check for available project

        if not self.has_project() and not self.args.ignore_grantfile:
            QtWidgets.QMessageBox.information(
                self, self.title, "No project allocation found. Please apply for a project in SUPR.")

        # Check if the restrict is set and check for correct user group.

        restricted_group = self.args.restrict.strip('"')

        if restricted_group != "":
            groups = [grp.getgrgid(g).gr_name for g in os.getgroups()]

            if not restricted_group in groups:
                QtWidgets.QMessageBox.information(
                    self, self.title, "This application is licensed. Please contact support to get access.")
                
                sys.exit(1)

        if self.silent:
            self.enable_silent_ui()

        if self.group in self.config.part_groups_defaults:
            if "tasks" in self.config.part_groups_defaults[self.group]:
                self.tasks_per_node = self.config.part_groups_defaults[self.group]["tasks"]
            if "memory" in self.config.part_groups_defaults[self.group]:
                if self.config.part_groups_defaults[self.group]["memory"]>0:
                    self.memory = self.config.part_groups_defaults[self.group]["memory"]
            if "exclusive" in self.config.part_groups_defaults[self.group]:
                self.exclusive = self.config.part_groups_defaults[self.group]["exclusive"]

        # Update controls to reflect parameters

        self.update_controls()

        # Setup timer callback for updating job status

        self.status_timer = QtCore.QTimer()
        self.status_timer.timeout.connect(self.on_status_timeout)

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

    @property
    def console_output(self):
        return self.__console_output

    @console_output.setter
    def console_output(self, output):
        self.__console_output = output

    def console_write(self, text):
        self.console_output.write(text+"\n")

    def dump_error_log(self):
        """Dump errors on standard output"""
        self.stop_redirect()
        for line in self.error_log:
            self.__console_output.write(line+"\n")

    @property
    def redirect_thread(self):
        return self.__redirect_thread

    @redirect_thread.setter
    def redirect_thread(self, thread):
        self.__redirect_thread = thread

    def stop_redirect(self):
        if self.__redirect_thread != None:
            self.__redirect_thread.running = False
            print("Stopping redirection")


    def enable_silent_ui(self):
        """Hides controls for running in silent mode."""

        msg = "Below shows the amount of time allocated for running this application.\n\n" +\
              "Closing this window will close the running application.\n\n" +\
              "Walltime allocated:\n%s (HH:MM:SS) " % self.time

        self.walltime_group.setVisible(False)
        self.resource_group.setVisible(False)
        self.feature_group.setVisible(False)
        self.project_group.setVisible(False)
        self.application_req_label.setText(msg)
        self.helpButton.setVisible(False)
        # self.application_req_label.setVisible(False)
        self.sep_first.setVisible(False)
        self.sep_before_buttons.setVisible(False)
        self.sep_after_buttons.setVisible(False)
        self.startButton.setVisible(False)
        self.showDetails.setVisible(False)
        self.cancelButton.setVisible(False)
        self.setMaximumHeight(250)

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

        if self.config.use_sacctmgr:

            # Querying SLURM directly to find active projects as an alternative to grant files.

            acctmgr = lrms.AccountManager()
            self.active_projects = acctmgr.query_active_projects(user)

            if len(self.active_projects) > 0:
                self.account = self.active_projects[0]
                return True
            else:
                return False

        else:

            grant_filename = self.config.grantfile

            # if self.config.grantfile_base != "":
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

                    print("Searching for grantfiles in %s." %
                        self.config.grantfile_dir)

                    grant_files = glob.glob(
                        self.config.grantfile_dir+'/grantfile.*')

                    for grant_filename in grant_files:
                        if (not '~' in grant_filename) and (len(grant_filename.split(".")) == 2):
                            suffix = grant_filename.split('.')[1]
                            if self.config.grantfile_suffix == '':
                                print("Parsing grantfile: %s" % grant_filename)
                                self.grantfile_list.append(
                                    lrms.GrantFile(grant_filename))
                            elif self.config.grantfile_suffix == suffix:
                                print("Parsing grantfile (suffix match): %s" %
                                    grant_filename)
                                self.grantfile_list.append(
                                    lrms.GrantFile(grant_filename))
                else:

                    # --- Do we have a grantile_base directive?

                    grant_filename = self.config.grantfile_base % self.part
                    if os.path.exists(grant_filename):
                        self.grantfile_list.append(lrms.GrantFile(grant_filename))

            self.active_projects = []

            if len(self.grantfile_list) > 0:

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
        self.reservation = ""
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
        self.jupyter_use_localhost = self.config.jupyter_use_localhost
        self.use_conda_env = False
        self.conda_env = ""

        self.ssh_tunnel = None
        self.autostart = False
        self.locked = False
        self.group = ""
        self.silent = False
        self.browser_command = self.config.browser_command

        self.default_memory = self.config.default_memory
        self.default_exclusive = self.config.default_exclusive
        self.default_tasks = self.config.default_tasks

    def get_defaults_from_cmdline(self):
        """Get properties from command line"""

        self.memory = str(self.args.memory)
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

        if self.args.job_name == "lhpc":
            self.job_name = "lhpc_"+"_".join(self.args.title.strip().lower().split())
        else:
            self.job_name = self.args.job_name

        #self.job_name = self.args.job_name
            
        print("job name args : ", self.args.job_name)
        print("job name is   : ", self.job_name)
        
        self.tasks_per_node = self.args.tasks_per_node
        self.cpus_per_task = self.args.cpus_per_task
        self.no_requeue = self.args.no_requeue
        self.user = self.args.user
        if self.args.notebook_module!="":
            self.notebook_module = self.args.notebook_module
        else:
            self.notebook_module = self.config.notebook_module

        if self.args.jupyterlab_module!="":
            self.jupyterlab_module = self.args.jupyterlab_module
        else:
            self.jupyterlab_module = self.config.jupyterlab_module

        self.autostart = self.args.autostart
        self.locked = self.args.locked
        self.group = self.args.group
        self.silent = self.args.silent

        if self.silent:
            self.autostart = True

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

        self.features = self.slurm.query_features(
            self.selected_part, self.feature_exclude_set)

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

        if self.job_type != "notebook" and self.job_type!="jupyterlab":
            self.show_job_settings_button.setVisible(False)

        self.slurm.query_partitions(exclude_set=self.part_exclude_set)

        self.update_feature_combo()

        if self.partCombo.count() == 0:

            self.filtered_parts = []
            self.filtered_parts.append("")

            self.partCombo.clear()
            self.partCombo.addItem("None")

            for part in self.slurm.partitions:
                descr = part

                #print(part.lower())
                #print(self.config.partition_descriptions)

                if part.lower() in self.config.partition_descriptions:
                    descr = self.config.partition_descriptions[part.lower()]

                if self.group == "" or (part in self.config.part_groups[self.group]):
                    self.partCombo.addItem(descr)
                    self.filtered_parts.append(part)

        if self.projectCombo.count() == 0:

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
            if (part == self.selected_part):
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
        # self.projectEdit.setText(str(self.account))

        if self.args.part_disable:
            self.partCombo.setEnabled(False)
            self.resource_group.setVisible(False)

        if self.args.feature_disable:
            self.featureCombo.setEnabled(False)
            self.feature_group.setVisible(False)

        if self.args.title != "":
            self.setWindowTitle(self.args.title)

        plain_text_usage = "Default usage. "
        
        if self.exclusive:
            plain_text_usage = "Full node. "
        else:
            if int(self.tasks_per_node)>0:
                plain_text_usage = f"{self.tasks_per_node} tasks / node. "

        if int(self.memory)>0:
            plain_text_usage += f"{self.memory} MB / task."

        self.node_usage_label.setText(plain_text_usage)


    def enable_extras_panel(self): 
        """Clear user interface components in extras panel"""

        self.extraControlsLayout.setEnabled(True)

        if not self.reconnect_vm_button is None:
            self.reconnect_vm_button.setEnabled(True)
        if not self.reconnect_nb_button is None:
            self.reconnect_nb_button.setEnabled(True)

    def disable_extras_panel(self):
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

        if self.rdp != None:
            self.rdp.terminate()

        event.accept()  # let the window close

    def submit_job(self):
        """Submit placeholder job"""

        self.update_properties()

        self.disable_extras_panel()

        # Note - This should be modularised

        if self.job_type == "":

            # Create a standard placeholder job

            self.job = jobs.PlaceHolderJob()

            self.only_submit = False

        elif self.job_type == "notebook":

            # Create a Jupyter notbook job

            self.only_submit = True

            self.job = jobs.JupyterNotebookJob(
                notebook_module=self.notebook_module, use_localhost=self.jupyter_use_localhost, conda_env=self.conda_env)
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

            self.only_submit = True

            self.job = jobs.JupyterLabJob(
                jupyterlab_module=self.jupyterlab_module, use_localhost=self.jupyter_use_localhost, conda_env=self.conda_env)
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

            self.only_submit = True

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
        self.job.output = self.user_config.job_output_file_path
        self.job.reservation = self.reservation
        if self.job_type != "vm":
            self.job.memory = int(self.memory)
            self.job.nodeCount = int(self.count)
            self.job.exclusive = self.exclusive
            self.job.tasksPerNode = int(self.tasks_per_node)
        if self.selected_feature != "":
            self.job.add_constraint(self.selected_feature)
        self.job.update()

        # Create a job submission thread

        self.submit_thread = SubmitThread(
            self.job, self.cmd, self.vgl, self.vglrun, self.vgl_path)
        self.submit_thread.finished.connect(self.on_submit_finished)
        self.submit_thread.start()

        # Make sure we only manage a single job ;)

        self.startButton.setEnabled(False)

    def launch_browser(self, url):
        """Open a configured browser for the url."""

        browser_path = shutil.which(self.browser_command)

        if browser_path is not None:
            Popen("%s %s" % (browser_path, url), shell=True)
            return True
        else:
            return False

    def on_submit_finished(self):
        """Event called from submit thread when job has been submitted"""

        self.running = True
        self.status_timer.start(5000)
        self.update_controls()
        self.active_connection = self.submit_thread.active_connection

        # Handle submibssion failure

        if self.submit_thread.error_status == SubmitThread.SUBMIT_FAILED:
            QtWidgets.QMessageBox.about(
                self, self.title, "Session start failed.")
            self.running = False
            self.status_timer.stop()
            self.update_controls()
            self.active_connection = None
            return

        if not self.only_submit:

            print("Starting graphical application on node.")

            self.retry_connection = True

            if self.vgl:
                print("Executing command on node (OpenGL)...")

                if self.active_connection is not None:
                    self.active_connection.terminate()
                self.active_connection = remote.VGLConnect()
                self.active_connection.vgl_path = self.config.vgl_path
                print("Command line:", self.cmd)
                self.active_connection.execute(self.job.nodes, self.cmd)

                print("Command completed...")
            else:
                print("Executing command on node...")

                if self.active_connection is not None:
                    self.active_connection.terminate()
                self.active_connection = remote.SSH()
                print("Command line:", self.cmd)
                self.active_connection.execute(self.job.nodes, self.cmd)
                
                print("Command completed...")


    def on_notebook_url_found(self, url):
        """Callback when notebook url has been found."""

        self.reset_status_panel()

        if self.jupyter_use_localhost:

            # Setup a tunnel to notebook server running on localhost on the node.

            if self.ssh_tunnel is not None:
                self.ssh_tunnel.terminate()

            self.ssh_tunnel = remote.SSHForwardTunnel(dest_server="localhost", remote_port=self.job.notebook_port, server_hostname=self.job.nodes)
            self.ssh_tunnel.execute()

            # Update the job url to use the localhost port.

            fixed_url = url.replace("8888", str(self.ssh_tunnel.local_port))
            self.job.notebook_url = fixed_url

            if not self.launch_browser(self.job.notebook_url):
                QtWidgets.QMessageBox.information(
                    self, self.title, "A suitable browser couldn't be found. The notebook instance can be found at:\n\n%s" % self.job.notebook_url )
        else:
            if not self.launch_browser(url):
                QtWidgets.QMessageBox.information(
                    self, self.title, "A suitable browser couldn't be found. The notebook instance can be found at:\n\n%s" % url )

        self.enable_extras_panel()

    def on_vm_available(self, hostname):
        """Start an RDP session to host"""

        self.reset_status_panel()

        if (hostname != "0.0.0.0") and (hostname != "0.0.0.1"):

            print("Starting RDP: " + hostname)

            self.rdp = remote.XFreeRDP(hostname)
            self.rdp.xfreerdp_path = self.config.xfreerdp_path
            self.rdp.execute()

            self.enable_extras_panel()
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
                        print("No active connection.")

                        self.running = False
                        self.status_timer.stop()

                        if self.retry_connection:
                            if (self.active_connection.re_execute_count<3):
                                print("Reconnecting. Attempt %d of 3..." % (self.active_connection.re_execute_count+1))
                                self.active_connection.execute_again()
                                self.running = True
                                self.status_timer.start()
                                return
                            else:
                                print("Giving up reconnection.")

                        print("Terminating job...")

                        self.usageBar.setValue(0)
                        self.update_controls()
                        if self.job is not None:
                            self.slurm.cancel_job(self.job)
                    else:
                        self.retry_connection = False
                        print("Connection is active.")

            else:

                # Session has completed. Update UI

                print("Session completed.")
                self.running = False
                self.status_timer.stop()
                self.usageBar.setValue(0)
                self.update_controls()
                self.disable_extras_panel()

                QtWidgets.QMessageBox.information(
                    self, self.title, "Your application was closed as the session time expired.")

    def on_autostart_timeout(self):
        """Automatically submit jobn"""
        self.autostart_timer.stop()
        self.submit_job()

    def on_reconnect_notebook(self):
        """Reopen connection to notebook."""

        if self.job != None:
            if not self.launch_browser(self.job.notebook_url):
                QtWidgets.QMessageBox.information(
                    self, self.title, "A suitable browser couldn't be found. The notebook instance can be found at:\n\n%s" % self.job.notebook_url )

        #Popen("firefox %s" % self.job.notebook_url, shell=True)

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
        if idx != 0:
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

                job = jobs.JupyterNotebookJob(notebook_module = self.notebook_module, use_localhost=self.jupyter_use_localhost, conda_env=self.conda_env)

            elif self.job_type == "jupyterlab":

                # Create a Jupyter notbook job

                job = jobs.JupyterLabJob(jupyterlab_module = self.jupyterlab_module, use_localhost=self.jupyter_use_localhost, conda_env=self.conda_env)

            elif self.job_type == "vm":

                # Create a VM job

                job = jobs.VMJob()

            # Setup job parameters

            job.name = self.job_name
            job.account = str(self.projectCombo.currentText())
            job.partition = str(self.selected_part)
            job.reservation = self.reservation
            job.time = str(self.time)
            job.output = self.user_config.job_output_file_path
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
        self.resource_window.setGeometry(self.x(
        )+self.width(), self.y(), self.resource_window.width(), self.resource_window.height())
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

        if self.ssh_tunnel is not None:
            self.ssh_tunnel.terminate()

        self.close()

    @QtCore.pyqtSlot()
    def on_cancelButton_clicked(self):
        """Cancel running job"""

        if self.job is not None:
            self.slurm.cancel_job(self.job)

        if self.rdp != None:
            self.rdp.terminate()

        if self.ssh_tunnel is not None:
            self.ssh_tunnel.terminate()
            self.ssh_tunnel = None

        self.running = False
        self.job = None
        self.status_timer.stop()
        self.update_controls()

        self.disable_extras_panel()

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
            self.resize(0, 0)
            self.adjustSize()

    @QtCore.pyqtSlot()
    def on_helpButton_clicked(self):
        """Open help page if set"""

        if self.config.help_url != "":

            if not self.launch_browser(self.config.help_url):
                QtWidgets.QMessageBox.information(
                    self, self.title, "A suitable browser couldn't be found. Documentation can be found at:\n\n%s" % self.config.help_url )
           
        # Popen("firefox %s" % self.config.help_url, shell=True)

    @QtCore.pyqtSlot(str)
    def on_append_text(self, text):
        """Callback for to update status output from standard output"""

        now = datetime.now()
        self.statusText.moveCursor(QtGui.QTextCursor.End)
        if text != "\n":
            self.statusText.insertPlainText(now.strftime("[%H:%M:%S] ") + text)
            self.error_log.append(text)
        else:
            self.statusText.insertPlainText(text)
            self.error_log.append(text)

        self.statusText.moveCursor(QtGui.QTextCursor.StartOfLine)

    @QtCore.pyqtSlot()
    def on_show_job_settings_button_clicked(self):
        """Open help page if set"""
        
        self.job_ui_window = job_ui.JupyterNotebookJobPropWindow(self)
        self.job_ui_window.python_module = self.jupyterlab_module
        self.job_ui_window.use_custom_anaconda_env = self.use_conda_env
        self.job_ui_window.custom_anaconda_env = self.conda_env

        self.job_ui_window.setGeometry(self.x(
        )+self.width(), self.y(), self.job_ui_window.width(), self.job_ui_window.height())

        self.job_ui_window.exec()

        self.jupyterlab_module = self.job_ui_window.python_module
        self.notebook_module = self.job_ui_window.python_module
        self.use_conda_env = self.job_ui_window.use_custom_anaconda_env
        self.conda_env = self.job_ui_window.custom_anaconda_env

        print(self.jupyterlab_module)
        print(self.notebook_module)
        print(self.use_conda_env)
        print(self.conda_env)

        


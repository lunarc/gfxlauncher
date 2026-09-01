#!/bin/env python
#
# LUNARC HPC Desktop On-Demand graphical launch tool
# Copyright (C) 2017-2026 LUNARC, Lund University
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

import os, sys, time, glob, getpass, shutil, tempfile, html, json

try:
    import grp
except:
    pass

from datetime import datetime
from pathlib import Path

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

    status_update = QtCore.pyqtSignal(str)

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

        start_time = self.slurm.query_start_time(self.job)
        if start_time:
            self.status_update.emit(f"Job queued — estimated start: {start_time}")
        else:
            self.status_update.emit("Job queued — waiting for resources...")

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

        # Walltime limits

        

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
        self.conda_env = self.config.conda_use_env
        self.use_conda_env = self.conda_env != ""
        self.jupyter_working_dir = ""
        self.jupyter_extra_args = ""
        self.jupyter_start_timeout = self.config.jupyter_start_timeout

        self.rstudio_module = self.config.rstudio_module
        self.rstudio_working_dir = ""
        self.rstudio_extra_args = ""

        self.ollama_module = self.config.ollama_module
        self.ollama_model = self.config.ollama_model
        self.ollama_models_dir = self.config.ollama_models_dir
        self.ollama_extra_args = ""
        self.pull_progress_bar = None

        self.codemodel_module = self.config.codemodel_module
        self.codemodel_model = self.config.codemodel_model
        self.codemodel_models_dir = self.config.codemodel_models_dir
        self.codemodel_extra_args = ""
        self.codemodel_info_window = None

        self.processing_started_at = 0.0
        self.processing_timeout_warned = False

        self.ssh_tunnel = None
        self.autostart = False
        self.locked = False
        self.group = ""
        self.silent = False
        self.browser_command = self.config.browser_command
        self._browser_redirect_file = None

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

        if self.args.rstudio_module!="":
            self.rstudio_module = self.args.rstudio_module
        else:
            self.rstudio_module = self.config.rstudio_module

        if self.args.ollama_module!="":
            self.ollama_module = self.args.ollama_module
        else:
            self.ollama_module = self.config.ollama_module

        if self.args.ollama_model!="":
            self.ollama_model = self.args.ollama_model
        else:
            self.ollama_model = self.config.ollama_model

        if self.args.ollama_models_dir!="":
            self.ollama_models_dir = self.args.ollama_models_dir
        else:
            self.ollama_models_dir = self.config.ollama_models_dir

        if self.args.codemodel_module!="":
            self.codemodel_module = self.args.codemodel_module
        else:
            self.codemodel_module = self.config.codemodel_module

        if self.args.codemodel_model!="":
            self.codemodel_model = self.args.codemodel_model
        else:
            self.codemodel_model = self.config.codemodel_model

        if self.args.codemodel_models_dir!="":
            self.codemodel_models_dir = self.args.codemodel_models_dir
        else:
            self.codemodel_models_dir = self.config.codemodel_models_dir

        self.autostart = self.args.autostart
        self.locked = self.args.locked
        self.group = self.args.group
        self.silent = self.args.silent

        if self.silent:
            self.autostart = True

    def on_update_status_panel(self, text):
        self.status_output.setText(text)

    def reset_status_panel(self):
        self.status_output.setText(
            self.copyright_short_info % self.version_info)
        
    def check_walltime(self, walltime, max_walltime):
        """
        Check if a walltime exceeds a maximum walltime and return the maximum if it does.
        
        Args:
            walltime (str): A time string in 'hh:mm:ss' format
            max_walltime (str): The maximum allowed time in 'hh:mm:ss' format
            
        Returns:
            str: Either the original walltime if it's within the max, or the max_walltime if exceeded
            
        Examples:
            >>> check_walltime('02:30:00', '03:00:00')
            '02:30:00'
            >>> check_walltime('04:15:30', '03:00:00')
            '03:00:00'
        """
        # Convert time strings to seconds for comparison
        def to_seconds(time_str):
            hours, minutes, seconds = map(int, time_str.split(':'))
            return hours * 3600 + minutes * 60 + seconds
        
        # Convert both times to seconds
        walltime_seconds = to_seconds(walltime)
        max_walltime_seconds = to_seconds(max_walltime)
        
        # If walltime exceeds max, return max_walltime
        if walltime_seconds > max_walltime_seconds:
            return max_walltime
        else:
            return walltime

    def update_properties(self):
        """Get properties from user interface"""
        self.time = self.wallTimeEdit.currentText()

        if self.selected_part in self.config.walltime_max:
            self.time = self.check_walltime(self.time, self.config.walltime_max[self.selected_part])
        else:
            self.time = self.check_walltime(self.time, self.config.walltime_max["default"])

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

        if self.job_type not in ("notebook", "jupyterlab", "rstudio", "ollama", "codemodel"):
            self.show_job_settings_button.setVisible(False)

        self.update_model_info_label()

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

        # Update walltime combo box


        self.wallTimeEdit.clear()

        if self.selected_part in self.config.walltime_limits:
            for walltime in self.config.walltime_limits[self.selected_part]:
                self.wallTimeEdit.addItem(walltime)
        else:
            for walltime in self.config.walltime_limits["default"]:
                self.wallTimeEdit.addItem(walltime)

        print("Updating walltime: ", self.time)
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

    def update_model_info_label(self):
        """Show which model an Ollama chat job will use, since it's
        otherwise only visible after opening the job settings dialog."""

        if self.job_type == "ollama":
            self.model_info_label.setText("Model: %s" % self.ollama_model)
        elif self.job_type == "codemodel":
            self.model_info_label.setText("Model: %s" % self.codemodel_model)
        else:
            self.model_info_label.setText("")

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

        if self.running:
            reply = QtWidgets.QMessageBox.question(
                self, self.title,
                "Closing will stop your running session and any unsaved work will be lost.\n\nAre you sure?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.No)
            if reply != QtWidgets.QMessageBox.Yes:
                event.ignore()
                return

        if self.job is not None:
            self.slurm.cancel_job(self.job)

        if self.ssh_tunnel is not None:
            self.ssh_tunnel.terminate()

        if self.rdp is not None:
            self.rdp.terminate()

        if self._browser_redirect_file is not None:
            try:
                os.remove(self._browser_redirect_file)
            except FileNotFoundError:
                pass
            self._browser_redirect_file = None

        event.accept()

    def _make_job(self):
        """Create and return the appropriate job object for the current job_type, or None on error."""

        if self.job_type == "":
            return jobs.PlaceHolderJob()
        elif self.job_type == "notebook":
            return jobs.JupyterNotebookJob(
                notebook_module=self.notebook_module,
                use_localhost=self.jupyter_use_localhost,
                conda_env=self.conda_env if self.use_conda_env else "",
                conda_source_env=self.config.conda_source_env,
                working_dir=self.jupyter_working_dir,
                extra_args=self.jupyter_extra_args)
        elif self.job_type == "jupyterlab":
            return jobs.JupyterLabJob(
                jupyterlab_module=self.jupyterlab_module,
                use_localhost=self.jupyter_use_localhost,
                conda_env=self.conda_env if self.use_conda_env else "",
                conda_source_env=self.config.conda_source_env,
                working_dir=self.jupyter_working_dir,
                extra_args=self.jupyter_extra_args)
        elif self.job_type == "rstudio":
            return jobs.RStudioJob(
                rstudio_module=self.rstudio_module,
                conda_env=self.conda_env if self.use_conda_env else "",
                conda_source_env=self.config.conda_source_env,
                working_dir=self.rstudio_working_dir,
                extra_args=self.rstudio_extra_args)
        elif self.job_type == "ollama":
            return jobs.OllamaChatJob(
                ollama_module=self.ollama_module,
                model=self.ollama_model,
                models_dir=self.ollama_models_dir,
                extra_args=self.ollama_extra_args)
        elif self.job_type == "codemodel":
            return jobs.CodeModelJob(
                codemodel_module=self.codemodel_module,
                model=self.codemodel_model,
                models_dir=self.codemodel_models_dir,
                extra_args=self.codemodel_extra_args)
        elif self.job_type == "vm":
            return jobs.VMJob()
        return None

    def _configure_job(self, job):
        """Apply current UI settings to a job object."""

        job.name = self.job_name
        job.account = str(self.projectCombo.currentText())
        job.partition = str(self.selected_part)
        job.time = str(self.time)
        job.output = self.user_config.job_output_file_path
        job.reservation = self.reservation
        if self.job_type != "vm":
            job.memory = int(self.memory)
            job.nodeCount = int(self.count)
            job.exclusive = self.exclusive
            job.tasksPerNode = int(self.tasks_per_node)
        if self.selected_feature != "":
            job.add_constraint(self.selected_feature)
        job.update()

    def submit_job(self):
        """Submit job"""

        self.update_properties()
        self.disable_extras_panel()

        self.job = self._make_job()

        if self.job is None:
            QtWidgets.QMessageBox.about(self, self.title, "Session start failed.")
            return

        if self.job_type == "":
            self.only_submit = False

        elif self.job_type == "notebook":
            self.only_submit = True
            self.job.on_notebook_url_found = self.on_notebook_url_found
            if self.extraControlsLayout.count() == 0:
                self.reconnect_nb_button = QtWidgets.QPushButton('Reconnect to notebook', self)
                self.reconnect_nb_button.setFixedSize(self.show_job_settings_button.size())
                self.reconnect_nb_button.setEnabled(True)
                self.reconnect_nb_button.clicked.connect(self.on_reconnect_notebook)
                self.extraControlsLayout.addStretch(1)
                self.extraControlsLayout.addWidget(self.reconnect_nb_button)
            self.launcherTabs.setCurrentIndex(2)

        elif self.job_type == "jupyterlab":
            self.only_submit = True
            self.job.on_notebook_url_found = self.on_notebook_url_found
            if self.extraControlsLayout.count() == 0:
                self.reconnect_nb_button = QtWidgets.QPushButton('Reconnect to Lab', self)
                self.reconnect_nb_button.setFixedSize(self.show_job_settings_button.size())
                self.reconnect_nb_button.setEnabled(True)
                self.reconnect_nb_button.clicked.connect(self.on_reconnect_notebook)
                self.extraControlsLayout.addStretch(1)
                self.extraControlsLayout.addWidget(self.reconnect_nb_button)
            self.launcherTabs.setCurrentIndex(2)

        elif self.job_type == "rstudio":
            self.only_submit = True
            self.job.on_notebook_url_found = self.on_notebook_url_found
            if self.extraControlsLayout.count() == 0:
                self.reconnect_nb_button = QtWidgets.QPushButton('Reconnect to RStudio', self)
                self.reconnect_nb_button.setFixedSize(self.show_job_settings_button.size())
                self.reconnect_nb_button.setEnabled(True)
                self.reconnect_nb_button.clicked.connect(self.on_reconnect_notebook)
                self.extraControlsLayout.addStretch(1)
                self.extraControlsLayout.addWidget(self.reconnect_nb_button)
            self.launcherTabs.setCurrentIndex(2)

        elif self.job_type == "ollama":
            self.only_submit = True
            self.job.on_notebook_url_found = self.on_notebook_url_found
            self.job.on_pull_progress = self.on_pull_progress
            self.job.on_account_created = self.on_chat_account_created
            if self.extraControlsLayout.count() == 0:
                self.pull_progress_bar = QtWidgets.QProgressBar(self)
                self.pull_progress_bar.setRange(0, 100)
                self.pull_progress_bar.setFormat("Downloading model: %p%")
                # Without a minimum width and a stretch factor, this ends up
                # squeezed to roughly button-sized by the QHBoxLayout it
                # shares with reconnect_nb_button below, and the format text
                # gets clipped. The stretch factor also means this - not the
                # button - claims any extra space in the row as the window
                # is resized.
                self.pull_progress_bar.setMinimumWidth(220)
                self.extraControlsLayout.addWidget(self.pull_progress_bar, 1)

                self.reconnect_nb_button = QtWidgets.QPushButton('Reconnect to Chat', self)
                self.reconnect_nb_button.setFixedSize(self.show_job_settings_button.size())
                self.reconnect_nb_button.setEnabled(True)
                self.reconnect_nb_button.clicked.connect(self.on_reconnect_notebook)
                self.extraControlsLayout.addWidget(self.reconnect_nb_button)
            self.launcherTabs.setCurrentIndex(2)

        elif self.job_type == "codemodel":
            self.only_submit = True
            self.job.on_notebook_url_found = self.on_notebook_url_found
            self.job.on_pull_progress = self.on_pull_progress
            if self.extraControlsLayout.count() == 0:
                self.pull_progress_bar = QtWidgets.QProgressBar(self)
                self.pull_progress_bar.setRange(0, 100)
                self.pull_progress_bar.setFormat("Downloading model: %p%")
                self.pull_progress_bar.setMinimumWidth(220)
                self.extraControlsLayout.addWidget(self.pull_progress_bar, 1)

                self.reconnect_nb_button = QtWidgets.QPushButton('Show VS Code connection info', self)
                self.reconnect_nb_button.setFixedSize(self.show_job_settings_button.size())
                self.reconnect_nb_button.setEnabled(True)
                self.reconnect_nb_button.clicked.connect(self.on_reconnect_notebook)
                self.extraControlsLayout.addWidget(self.reconnect_nb_button)
            self.launcherTabs.setCurrentIndex(2)

        elif self.job_type == "vm":
            self.only_submit = True
            self.job.on_vm_available = self.on_vm_available
            if self.extraControlsLayout.count() == 0:
                self.reconnect_vm_button = QtWidgets.QPushButton('Connect to desktop', self)
                self.reconnect_vm_button.setEnabled(False)
                self.reconnect_vm_button.clicked.connect(self.on_reconnect_vm)
                self.extraControlsLayout.addStretch(1)
                self.extraControlsLayout.addWidget(self.reconnect_vm_button)
                self.extraControlsLayout.addStretch(1)
            self.launcherTabs.setCurrentIndex(2)

        self._configure_job(self.job)

        self.submit_thread = SubmitThread(
            self.job, self.cmd, self.vgl, self.vglrun, self.vgl_path)
        self.submit_thread.finished.connect(self.on_submit_finished)
        self.submit_thread.status_update.connect(self.on_update_status_panel)
        self.submit_thread.start()

        self.startButton.setEnabled(False)

    def _write_browser_redirect(self, url):
        """Write a local HTML redirect page for url and return its path.

        Secrets such as a Jupyter ?token=... must never end up as a browser
        process argument: argv is visible to any other user on a shared
        login node via `ps`/`/proc`. Instead we hand the browser a private,
        token-free local file that redirects to the real url client-side -
        the same trick Jupyter itself uses for its own auto-opened browser
        (jpserver-<pid>-open.html).
        """

        redirect_dir = os.path.join(os.path.expanduser("~"), ".lhpc", "browser")
        os.makedirs(redirect_dir, mode=0o700, exist_ok=True)
        os.chmod(redirect_dir, 0o700)

        # Best-effort sweep of stale files a prior crashed session left
        # behind (closeEvent normally removes the one it created).
        stale_cutoff = time.time() - 86400
        for stale_path in glob.glob(os.path.join(redirect_dir, "*.html")):
            try:
                if os.path.getmtime(stale_path) < stale_cutoff:
                    os.remove(stale_path)
            except FileNotFoundError:
                pass

        if self._browser_redirect_file is not None:
            try:
                os.remove(self._browser_redirect_file)
            except FileNotFoundError:
                pass
            self._browser_redirect_file = None

        fd, path = tempfile.mkstemp(suffix=".html", dir=redirect_dir)

        safe_url = html.escape(url, quote=True)
        js_url = json.dumps(url).replace("</", "<\\/")

        with os.fdopen(fd, "w") as f:
            f.write(
                "<!DOCTYPE html>\n"
                "<html><head><meta charset=\"utf-8\">\n"
                "<meta http-equiv=\"refresh\" content=\"0;url=%s\">\n"
                "<script>location.replace(%s);</script>\n"
                "</head><body>\n"
                "<p>Redirecting... if nothing happens, click "
                "<a href=\"%s\">here</a>.</p>\n"
                "</body></html>\n"
                % (safe_url, js_url, safe_url)
            )

        self._browser_redirect_file = path

        return path

    def launch_browser(self, url):
        """Open a configured browser for the url."""

        browser_path = shutil.which(self.browser_command)

        if browser_path is not None:
            redirect_path = self._write_browser_redirect(url)
            Popen([browser_path, Path(redirect_path).as_uri()])
            return True
        else:
            return False

    def on_submit_finished(self):
        """Event called from submit thread when job has been submitted"""

        self.running = True
        self.status_timer.start(5000)
        self.update_controls()
        self.active_connection = self.submit_thread.active_connection

        # Handle submission failure

        if self.submit_thread.error_status == SubmitThread.SUBMIT_FAILED:
            QtWidgets.QMessageBox.about(
                self, self.title, "Session start failed.")
            self.running = False
            self.status_timer.stop()
            self.update_controls()
            self.active_connection = None
            return

        self.on_update_status_panel(f"Running on node: {self.job.nodes}")

        self.processing_started_at = time.time()
        self.processing_timeout_warned = False

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


    def on_pull_progress(self, percent):
        """Callback while a chat job's model is downloading."""

        if self.pull_progress_bar is not None:
            self.pull_progress_bar.setValue(percent)

    def on_chat_account_created(self, email):
        """Callback fired only the run OllamaChatJob's wrapper script has
        just provisioned a fresh Open WebUI account (see jobs.py's
        OllamaChatJob.on_account_created) - never on a run that reused an
        existing one. Shows the generated password once, before the browser
        opens to the login screen, since it's only ever written to
        ~/.lhpc/ollama-chat-credentials and never appears in job output."""

        cred_path = os.path.join(os.path.expanduser("~"), ".lhpc", "ollama-chat-credentials")

        password = None
        try:
            with open(cred_path) as f:
                for line in f:
                    if line.startswith("password="):
                        password = line[len("password="):].strip()
                        break
        except FileNotFoundError:
            pass

        if password is None:
            QtWidgets.QMessageBox.information(
                self, self.title,
                "A chat account was created for %s, but its password "
                "couldn't be read back from %s." % (email, cred_path))
            return

        QtWidgets.QMessageBox.information(
            self, self.title,
            "A chat account has been created for you:\n\n"
            "Email: %s\nPassword: %s\n\n"
            "Use these to log in once the chat interface opens. They are "
            "saved to %s for future reference." % (email, password, cred_path))

    def on_notebook_url_found(self, url):
        """Callback when notebook url has been found."""

        self.reset_status_panel()

        if self.job_type in ("ollama", "codemodel") and self.pull_progress_bar is not None:
            # Just hiding it isn't enough: a hidden widget contributes zero
            # size to its QHBoxLayout, so its stretch=1 slot (jobs.py's
            # addWidget(self.pull_progress_bar, 1) call) would vanish along
            # with it, and reconnect_nb_button - which was only sitting at
            # the row's right edge because that stretch was pushing it
            # there - would snap left instead. Swapping in a plain stretch
            # of the same weight at the same layout position keeps the
            # button's position stable regardless of whether the bar was
            # ever there.
            index = self.extraControlsLayout.indexOf(self.pull_progress_bar)
            self.extraControlsLayout.removeWidget(self.pull_progress_bar)
            self.pull_progress_bar.setParent(None)
            self.extraControlsLayout.insertStretch(index, 1)
            self.pull_progress_bar = None

        if self.job.use_localhost:

            # Setup a tunnel to notebook server running on localhost on the node.

            if self.ssh_tunnel is not None:
                self.ssh_tunnel.terminate()

            self.ssh_tunnel = remote.SSHForwardTunnel(dest_server="localhost", remote_port=self.job.notebook_port, server_hostname=self.job.nodes)
            self.ssh_tunnel.execute()

            # Update the job url to use the localhost port.

            remote_port = jobs.find_remote_port(url)
            fixed_url = url.replace(f":{remote_port}", f":{self.ssh_tunnel.local_port}", 1)
            self.job.notebook_url = fixed_url

            if self.job_type == "codemodel":
                self.show_codemodel_info(self.job.notebook_url)
            elif not self.launch_browser(self.job.notebook_url):
                QtWidgets.QMessageBox.information(
                    self, self.title, "A suitable browser couldn't be found. The notebook instance can be found at:\n\n%s" % self.job.notebook_url )
        else:
            if self.job_type == "codemodel":
                self.show_codemodel_info(url)
            elif not self.launch_browser(url):
                QtWidgets.QMessageBox.information(
                    self, self.title, "A suitable browser couldn't be found. The notebook instance can be found at:\n\n%s" % url )

        self.enable_extras_panel()

    def show_codemodel_info(self, url):
        """Show (or refresh) the non-modal dialog with the code model's
        tunneled endpoint and a ready-to-paste Continue config snippet."""

        if self.codemodel_info_window is None:
            self.codemodel_info_window = job_ui.CodeModelInfoWindow(self)

        self.codemodel_info_window.set_endpoint(url, self.codemodel_model)
        self.codemodel_info_window.show()
        self.codemodel_info_window.raise_()
        self.codemodel_info_window.activateWindow()

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

                remaining = max(0, timeLimit - timeRunning)
                h = remaining // 3600
                m = (remaining % 3600) // 60
                s = remaining % 60
                self.usageBar.setFormat(f"{h}:{m:02d}:{s:02d} remaining (%p%)")

                if self.only_submit:

                    # Update status panel

                    still_waiting = self.job.process_output or self.job.update_processing

                    if still_waiting:
                        elapsed = int(time.time() - self.processing_started_at)
                        self.on_update_status_panel(
                            "%s (%ds)" % (self.job.processing_description, elapsed))

                        if elapsed > self.jupyter_start_timeout and not self.processing_timeout_warned:
                            self.processing_timeout_warned = True
                            QtWidgets.QMessageBox.warning(
                                self, self.title,
                                "%s hasn't responded after %d seconds.\n\n"
                                "This can happen if the selected module or environment failed to load. "
                                "Check the status log below for details, or press Cancel to stop the session.\n\n"
                                "gfxlaunch will keep waiting in the background." % (
                                    self.job.processing_description.rstrip("."), self.jupyter_start_timeout))
                    else:
                        self.on_update_status_panel(self.job.processing_description)

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
                        self.usageBar.setFormat("Usage %p%")
                        self.reset_status_panel()
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
                self.usageBar.setFormat("Usage %p%")
                self.reset_status_panel()
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
            if self.job_type == "codemodel":
                self.show_codemodel_info(self.job.notebook_url)
            elif not self.launch_browser(self.job.notebook_url):
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
            job = self._make_job()
            if job is None:
                return
            self._configure_job(job)
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

        if self.ssh_tunnel is not None:
            self.ssh_tunnel.terminate()

        self.close()

    @QtCore.pyqtSlot()
    def on_cancelButton_clicked(self):
        """Cancel running job"""

        if self.running:
            reply = QtWidgets.QMessageBox.question(
                self, self.title,
                "Stopping the session will close your running application and any unsaved work will be lost.\n\nAre you sure?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.No)
            if reply != QtWidgets.QMessageBox.Yes:
                return

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
        self.usageBar.setFormat("Usage %p%")
        self.reset_status_panel()
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

        if self.job_type == "rstudio":
            self.job_ui_window = job_ui.RStudioJobPropWindow(self)
            self.job_ui_window.module = self.rstudio_module
            self.job_ui_window.use_custom_anaconda_env = self.use_conda_env
            self.job_ui_window.custom_anaconda_env = self.conda_env
            self.job_ui_window.working_dir = self.rstudio_working_dir
            self.job_ui_window.extra_args = self.rstudio_extra_args

            self.job_ui_window.setGeometry(self.x(
            )+self.width(), self.y(), self.job_ui_window.width(), self.job_ui_window.height())

            self.job_ui_window.exec()

            self.rstudio_module = self.job_ui_window.module
            self.use_conda_env = self.job_ui_window.use_custom_anaconda_env
            self.conda_env = self.job_ui_window.custom_anaconda_env
            self.rstudio_working_dir = self.job_ui_window.working_dir
            self.rstudio_extra_args = self.job_ui_window.extra_args

            print(self.rstudio_module)
            print(self.use_conda_env)
            print(self.conda_env)
            return

        if self.job_type == "ollama":
            self.job_ui_window = job_ui.OllamaJobPropWindow(self)
            self.job_ui_window.popular_models = self.config.ollama_popular_models
            self.job_ui_window.model = self.ollama_model
            # $HOME (and any other shell vars) in the config/CLI value are
            # meant to be expanded by bash inside the SLURM job (jobs.py
            # exports this as a literal job-script line) - expand them here
            # too just for display, so the field shows a real path rather
            # than a literal "$HOME/...".
            self.job_ui_window.models_dir = os.path.expandvars(self.ollama_models_dir)
            self.job_ui_window.extra_args = self.ollama_extra_args

            self.job_ui_window.setGeometry(self.x(
            )+self.width(), self.y(), self.job_ui_window.width(), self.job_ui_window.height())

            self.job_ui_window.exec()

            self.ollama_model = self.job_ui_window.model
            self.ollama_models_dir = self.job_ui_window.models_dir
            self.ollama_extra_args = self.job_ui_window.extra_args
            self.update_model_info_label()
            return

        if self.job_type == "codemodel":
            self.job_ui_window = job_ui.CodeModelJobPropWindow(self)
            self.job_ui_window.popular_models = self.config.codemodel_popular_models
            self.job_ui_window.model = self.codemodel_model
            self.job_ui_window.models_dir = os.path.expandvars(self.codemodel_models_dir)
            self.job_ui_window.extra_args = self.codemodel_extra_args

            self.job_ui_window.setGeometry(self.x(
            )+self.width(), self.y(), self.job_ui_window.width(), self.job_ui_window.height())

            self.job_ui_window.exec()

            self.codemodel_model = self.job_ui_window.model
            self.codemodel_models_dir = self.job_ui_window.models_dir
            self.codemodel_extra_args = self.job_ui_window.extra_args
            self.update_model_info_label()
            return

        self.job_ui_window = job_ui.JupyterNotebookJobPropWindow(self)
        self.job_ui_window.python_module = self.jupyterlab_module
        self.job_ui_window.use_custom_anaconda_env = self.use_conda_env
        self.job_ui_window.custom_anaconda_env = self.conda_env
        self.job_ui_window.working_dir = self.jupyter_working_dir
        self.job_ui_window.extra_args = self.jupyter_extra_args

        self.job_ui_window.setGeometry(self.x(
        )+self.width(), self.y(), self.job_ui_window.width(), self.job_ui_window.height())

        self.job_ui_window.exec()

        self.jupyterlab_module = self.job_ui_window.python_module
        self.notebook_module = self.job_ui_window.python_module
        self.use_conda_env = self.job_ui_window.use_custom_anaconda_env
        self.conda_env = self.job_ui_window.custom_anaconda_env
        self.jupyter_working_dir = self.job_ui_window.working_dir
        self.jupyter_extra_args = self.job_ui_window.extra_args

        print(self.jupyterlab_module)
        print(self.notebook_module)
        print(self.use_conda_env)
        print(self.conda_env)

        


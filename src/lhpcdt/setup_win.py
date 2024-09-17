#
# LUNARC HPC Desktop On-Demand graphical launch tool
# Copyright (C) 2017-2024 LUNARC, Lund University
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
"""LUNARC HPC Desktop Setup Guide"""

from PyQt5 import Qt, QtCore, QtGui, QtWidgets, uic

from . import jobs
from . import lrms
from . import remote
from . import settings
from . import config
from . import resources
from . import ui_setup_window as ui  
from . import basic_config

from subprocess import Popen, PIPE, STDOUT

class SetupWindow(QtWidgets.QWidget, ui.Ui_setup_form):
    """Session Window class"""

    def __init__(self, parent=None):
        super(SetupWindow, self).__init__(parent)
        self.setupUi(self)

        self.config = basic_config.BasicConfig()

        print("update_controls")
        self.update_controls()

    def update_controls(self):
        """Update controls"""
        self.update_general()
        self.update_slurm()
        self.update_menus()
        self.update_vgl()
        self.update_jupyter()

    def update_general(self):
        """Update general settings"""
        self.script_dir_edit.setText(self.config.script_dir)
        #self.install_dir_edit.setText(self.config.install_dir)
        self.help_url_edit.setText(self.config.help_url)
        self.browser_cmd_edit.setText(self.config.browser_cmd)

    def update_slurm(self):
        """Update SLURM settings"""
        self.default_part_edit.setText(self.config.default_part)
        self.default_account_edit.setText(self.config.default_account)
        self.default_tasks_edit.setText(str(self.config.default_tasks))
        self.default_memory_edit.setText(str(self.config.default_memory))

    def update_menus(self):
        """Update menu settings"""
        self.menu_prefix_edit.setText(self.config.menu_prefix)
        self.desktop_entry_prefix_edit.setText(self.config.desktop_entry_prefix)

    def update_vgl(self):
        """Update VGL settings"""
        self.vgl_bin_edit.setText(self.config.vgl_bin)
        self.vgl_path_edit.setText(self.config.vgl_path)

    def update_jupyter(self):
        """Update Jupyter settings"""
        self.notebook_module_edit.setText(self.config.notebook_module)
        self.jupyterlab_module_edit.setText(self.config.jupyterlab_module)
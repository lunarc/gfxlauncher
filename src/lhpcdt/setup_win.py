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

from . import ui_setup_window as ui
from subprocess import Popen, PIPE, STDOUT
from . import basic_config
from . import resources
from . import config
from . import settings
from . import remote
from . import lrms
from . import jobs
from PyQt5 import Qt, QtCore, QtGui, QtWidgets, uic


class SetupWindow(QtWidgets.QMainWindow, ui.Ui_MainWindow):
    """
    SetupWindow is a QMainWindow that provides a graphical interface for configuring
    various settings related to the application.
    """
    def __init__(self, parent=None):
        """
        Initializes the SetupWindow instance.

        Args:
            parent (optional): The parent widget of this window. Defaults to None.

        Attributes:
            config (basic_config.BasicConfig): An instance of BasicConfig to manage configuration settings.
        """
        super(SetupWindow, self).__init__(parent)

        self.setupUi(self)
        self.config = basic_config.BasicConfig()
        self.query_slurm()
        self.update_controls()

    def query_slurm(self):
        """
        Query the SLURM scheduler for partition information.

        This method uses the `sinfo` command to query the SLURM scheduler for partition information.
        It then parses the output to extract the partition names and descriptions.
        The partition names and descriptions are stored in the `config` attribute.

        Returns:
            None
        """
        slurm = lrms.Slurm()
        slurm.query_partitions()
        self.config.partitions = slurm.partitions

        for part in self.config.partitions:
            print(part)
            features = slurm.query_features(part)
            print(features)

        print(self.config.partitions)

    @QtCore.pyqtSlot()
    def on_script_dir_button_clicked(self):
        """
        Handles the event when the script directory button is clicked.

        This method opens a file dialog to allow the user to select a directory.
        If a directory is selected, it updates the script directory configuration
        and sets the text of the script directory edit widget. Finally, it updates
        the controls based on the new configuration.

        Returns:
            None
        """
        selected_dir = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Select script directory", self.config.script_dir)
        if selected_dir != "":
            self.config.script_dir = selected_dir
            self.script_dir_edit.setText(self.config.script_dir)

        self.update_controls()

    @QtCore.pyqtSlot()
    def on_browser_cmd_button_clicked(self):
        """
        Handles the event when the browser command button is clicked.

        This method opens a file dialog to allow the user to select a browser command.
        If a command is selected, it updates the browser command configuration
        and sets the text of the browser command edit widget.

        Returns:
            None
        """
        selected_cmd, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Select browser command", self.config.browser_cmd)
        if selected_cmd != "":
            self.config.browser_cmd = selected_cmd
            self.browser_cmd_edit.setText(self.config.browser_cmd)

    @QtCore.pyqtSlot()
    def on_exit_button_clicked(self):
        """
        Handles the event when the exit button is clicked.

        This method is triggered when the user clicks the exit button in the GUI.
        It closes the current window.
        """
        self.close()

    @QtCore.pyqtSlot()
    def on_create_button_clicked(self):
        """
        Handles the event when the save button is clicked.

        Opens a file dialog to select the location and name for saving the configuration file.
        If a valid filename is provided, it saves the current configuration to the specified file.

        Returns:
            None
        """
        config_filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save configuration file", "gfxlauncher.conf", "Configuration files (*.conf)")
        if config_filename != "":
            self.config.save(config_filename)

    def update_controls(self):
        """
        Update various controls by calling specific update methods.

        This method sequentially updates the following components:
        - General settings
        - SLURM configurations
        - Menus
        - VirtualGL settings
        - Jupyter configurations

        Each component has its own dedicated update method which is called in turn.
        """
        self.update_general()
        self.update_slurm()
        self.update_menus()
        self.update_vgl()
        self.update_jupyter()

    def update_general(self):
        """
        Update the general settings in the user interface with values from the configuration.
        """
        self.script_dir_edit.setText(self.config.script_dir)
        #self.install_dir_edit.setText(self.config.install_dir)
        self.help_url_edit.setText(self.config.help_url)
        self.browser_cmd_edit.setText(self.config.browser_cmd)

    def update_slurm(self):
        """
        Update the SLURM settings in the UI with the current configuration values.
        """
        self.default_part_edit.setText(self.config.default_part)
        self.default_account_edit.setText(self.config.default_account)
        self.default_tasks_edit.setText(str(self.config.default_tasks))
        self.default_memory_edit.setText(str(self.config.default_memory))

    def update_menus(self):
        """
        Update the menu settings by setting the text of the menu prefix and 
        desktop entry prefix edit fields based on the current configuration.

        This method retrieves the `menu_prefix` and `desktop_entry_prefix` 
        from the `config` attribute and updates the corresponding text fields 
        in the user interface.

        Returns:
            None
        """
        self.menu_prefix_edit.setText(self.config.menu_prefix)
        self.desktop_entry_prefix_edit.setText(self.config.desktop_entry_prefix)

    def update_vgl(self):
        """
        Update the VirtualGL (VGL) settings in the user interface.

        This method sets the text of the VGL binary and VGL path edit fields
        to the corresponding values from the configuration.
        """
        self.vgl_bin_edit.setText(self.config.vgl_bin)
        self.vgl_path_edit.setText(self.config.vgl_path)

    def update_jupyter(self):
        """
        Update Jupyter settings by setting the text of the notebook and JupyterLab module edit fields.

        This method updates the text fields for the notebook and JupyterLab modules
        based on the current configuration settings.
        """
        self.notebook_module_edit.setText(self.config.notebook_module)
        self.jupyterlab_module_edit.setText(self.config.jupyterlab_module)


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = SetupWindow()
    window.show()
    sys.exit(app.exec_())

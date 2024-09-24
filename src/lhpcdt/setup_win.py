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
        self.config_tabs.setCurrentIndex(0)
        self.config = basic_config.BasicConfig()
        self.update_controls()

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
        self.update_partitions()
        self.update_features()
        self.update_groups()
        self.update_group_parts()
        self.update_group_defaults()
        self.update_config_preview()

    def update_general(self):
        """
        Update the general settings in the user interface with values from the configuration.
        """
        self.script_dir_edit.setText(self.config.script_dir)
        # self.install_dir_edit.setText(self.config.install_dir)
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
        self.desktop_entry_prefix_edit.setText(
            self.config.desktop_entry_prefix)

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

    def update_partitions(self):
        """
        Update the partition settings in the user interface.

        This method updates the partition settings in the user interface by
        setting the text of the partition combo box to the partition names
        stored in the configuration.
        """
        self.all_part_list.clear()
        self.all_part_list.addItems(self.config.partitions.keys())
        self.all_part_group_list.clear()
        self.all_part_group_list.addItems(self.config.partitions.keys())

    def update_features(self):
        """
        Update the feature settings in the user interface.

        This method updates the feature settings in the user interface by
        setting the text of the feature combo box to the feature names
        stored in the configuration.
        """
        self.feature_list.clear()
        self.feature_list.addItems(self.config.features.keys())

    def update_groups(self):
        """
        Update the partition group settings in the user interface.

        This method updates the partition group settings in the user interface by
        setting the text of the partition group combo box to the partition group names
        stored in the configuration.
        """
        self.group_list.clear()
        self.group_list.addItems(self.config.groups.keys())

        self.group_default_list.clear()
        self.group_default_list.addItems(self.config.groups.keys())

    def update_group_parts(self):
        """
        Update the partition group settings in the user interface.

        This method updates the partition group settings in the user interface by
        setting the text of the partition group combo box to the partition group names
        stored in the configuration.
        """
        if not self.group_list.currentItem():
            return

        group_name = self.group_list.currentItem().text()
        if group_name:
            self.group_part_list.clear()
            self.group_part_list.addItems(self.config.groups[group_name])

    def update_group_defaults(self):
        """
        Update the partition group settings in the user interface.

        This method updates the partition group settings in the user interface by
        setting the text of the partition group combo box to the partition group names
        stored in the configuration.
        """
        if not self.group_default_list.currentItem():
            return
        
        self.group_default_tasks_edit.setText("")
        self.group_default_memory_edit.setText("")
        self.group_default_exclusive_check.setChecked(False)

        group_name = self.group_default_list.currentItem().text()
        if group_name in self.config.group_defaults:
            if "tasks" in self.config.group_defaults[group_name]:
                self.group_default_tasks_edit.setText(str(self.config.group_defaults[group_name]['tasks']))
            if "memory" in self.config.group_defaults[group_name]:
                self.group_default_memory_edit.setText(str(self.config.group_defaults[group_name]['memory']))
            if "exclusive" in self.config.group_defaults[group_name]:
                self.group_default_exclusive_check.setChecked(self.config.group_defaults[group_name]['exclusive'])

    def update_config_preview(self):
        """
        Update the configuration preview in the user interface.

        This method generates a preview of the configuration file based on the
        current settings and displays it in the text edit widget.
        """
        self.config_preview_edit.setPlainText(str(self.config))

    @QtCore.pyqtSlot()
    def on_apply_group_defaults_button_clicked(self):
        """
        Handles the event when the apply group defaults button is clicked.

        This method applies the default settings to the selected partition group.
        """
        group_name = self.group_default_list.currentItem().text()
        if group_name:
            tasks = self.group_default_tasks_edit.text()
            memory = self.group_default_memory_edit.text()
            exclusive = self.group_default_exclusive_check.isChecked()

            if group_name not in self.config.group_defaults:
                self.config.group_defaults[group_name] = {}

            if tasks:
                self.config.group_defaults[group_name]['tasks'] = int(tasks)
            if memory:
                self.config.group_defaults[group_name]['memory'] = int(memory)
            self.config.group_defaults[group_name]['exclusive'] = exclusive

            self.update_controls()

    @QtCore.pyqtSlot()
    def on_group_default_list_itemSelectionChanged(self):
        """
        Handles the event when an item in the partition group list is selected.

        This method updates the partition list for the selected partition group.
        """
        self.update_group_defaults()

    @QtCore.pyqtSlot()
    def on_new_action_triggered(self):
        """
        Handles the event when the New action is triggered.

        This method creates a new configuration instance and updates the controls.
        """
        self.config = basic_config.BasicConfig()
        self.update_controls()

    @QtCore.pyqtSlot()
    def on_open_action_triggered(self):
        """
        Handles the event when the Open action is triggered.

        This method opens a file dialog to select a configuration file.
        If a valid file is selected, it loads the configuration from the file
        and updates the controls.
        """
        config_filename, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Open configuration file", "", "Configuration files (*.conf)")
        if config_filename != "":
            self.config.load(config_filename)
            self.update_controls()

    @QtCore.pyqtSlot()
    def on_save_action_triggered(self):
        """
        Handles the event when the Save action is triggered.

        This method opens a file dialog to select a location to save the configuration file.
        If a valid location is selected, it saves the current configuration to the file.
        """
        config_filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save configuration file", "gfxlauncher.conf", "Configuration files (*.conf)")
        if config_filename != "":
            self.config.save(config_filename)

    @QtCore.pyqtSlot()
    def on_save_as_action_triggered(self):
        """
        Handles the event when the Save As action is triggered.

        This method opens a file dialog to select a location to save the configuration file.
        If a valid location is selected, it saves the current configuration to the file.
        """
        config_filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save configuration file", "gfxlauncher.conf", "Configuration files (*.conf)")
        if config_filename != "":
            self.config.save(config_filename)

    @QtCore.pyqtSlot()
    def on_exit_action_triggered(self):
        """
        Handles the event when the Exit action is triggered.

        This method closes the current window.
        """
        self.close()

    @QtCore.pyqtSlot()
    def on_copy_action_triggered(self):
        """
        Handles the event when the Copy action is triggered.

        This method copies the contents of the configuration preview to the clipboard.
        """
        clipboard = QtWidgets.QApplication.clipboard()
        clipboard.setText(self.config_preview_edit.toPlainText())

    @QtCore.pyqtSlot()
    def on_config_action_triggered(self):
        """
        Handles the event when the Configuration action is triggered.

        This method opens the configuration window.
        """
        self.config_tabs.setCurrentIndex(9)

    @QtCore.pyqtSlot()
    def on_group_list_itemSelectionChanged(self):
        """
        Handles the event when an item in the partition group list is selected.

        This method updates the partition list for the selected partition group.
        """
        self.update_group_parts()

    @QtCore.pyqtSlot()
    def on_add_group_button_clicked(self):
        """
        Handles the event when the add partition to group button is clicked.

        This method adds the selected partition to the selected partition group.
        """
        print("Add partition to group")
        group_name, ok = QtWidgets.QInputDialog.getText(
            self, "Create partition group", "Group alias")
        if ok and group_name:
            self.config.groups[group_name] = []
            self.update_controls()

    @QtCore.pyqtSlot()
    def on_remove_group_button_clicked(self):
        """
        Handles the event when the remove group button is clicked.

        This method removes the selected partition group from the configuration.
        """
        group_name = self.group_list.currentItem().text()
        del self.config.groups[group_name]
        self.update_controls()

    @QtCore.pyqtSlot()
    def on_add_part_group_button_clicked(self):
        """
        Handles the event when the add partition group button is clicked.

        This method adds the selected partition to the selected partition group.
        """
        print("Add partition to group")
        if not self.all_part_group_list.currentItem():
            return
        if not self.group_list.currentItem():
            return

        print("Add partition to group - OK")

        part_name = self.all_part_group_list.currentItem().text()
        group_name = self.group_list.currentItem().text()

        if part_name in self.config.groups[group_name]:
            return

        self.config.groups[group_name].append(part_name)
        self.update_controls()

    @QtCore.pyqtSlot()
    def on_remove_part_group_button_clicked(self):
        """
        Handles the event when the remove partition from group button is clicked.

        This method removes the selected partition from the selected partition group.
        """
        part_name = self.all_part_group_list.currentItem().text()
        group_name = self.group_list.currentItem().text()

        if part_name and group_name:
            self.config.partition_groups[group_name].remove(part_name)
            self.update_controls()

    @QtCore.pyqtSlot()
    def on_feature_list_itemSelectionChanged(self):
        """
        Handles the event when an item in the feature list is selected.

        This method updates the feature description edit widget with the description
        of the selected feature.
        """
        selected_feature = self.feature_list.currentItem().text()
        self.feature_descr_edit.setText(self.config.features[selected_feature])

    @QtCore.pyqtSlot()
    def on_all_part_list_itemSelectionChanged(self):
        """
        Handles the event when an item in the partition list is selected.

        This method updates the partition description edit widget with the description
        of the selected partition.
        """
        selected_part = self.all_part_list.currentItem().text()
        self.part_descr_edit.setText(self.config.partitions[selected_part])

    @QtCore.pyqtSlot()
    def on_part_descr_assign_button_clicked(self):
        """
        Handles the event when the assign button for partition description is clicked.

        This method assigns the description to the selected partition based on the
        text entered in the partition description edit widget.
        """
        part_name = self.all_part_list.currentItem().text()
        part_descr = self.part_descr_edit.text()
        self.config.partitions[part_name] = part_descr
        self.update_controls()

    @QtCore.pyqtSlot()
    def on_feature_descr_assign_button_clicked(self):
        """
        Handles the event when the assign button for feature description is clicked.

        This method assigns the description to the selected feature based on the
        text entered in the feature description edit widget.
        """
        feature_name = self.feature_list.currentItem().text()
        feature_descr = self.feature_descr_edit.text()
        self.config.features[feature_name] = feature_descr
        self.update_controls()

    @QtCore.pyqtSlot()
    def on_config_tabs_currentChanged(self, idx):
        """
        Handles the event when the current tab in the configuration window changes.

        This method updates the controls based on the new tab that is selected.
        """
        self.update_controls()

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


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = SetupWindow()
    window.show()
    sys.exit(app.exec_())

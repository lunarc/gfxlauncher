#!/bin/env python

import os, sys

from PyQt5 import Qt, QtCore, QtGui, QtWidgets, uic

from . import lmod
from . import settings
from . import config
from . import ui_lmod_query as ui

from subprocess import Popen, PIPE, STDOUT

def execute_with_output(command):
    process = Popen(command, shell=True, stdout=PIPE)
    output, error = process.communicate()
    return output

class LmodQueryWindow(QtWidgets.QWidget, ui.Ui_LmodQueryWindow):
    """Resource specification window"""

    def __init__(self, parent=None):
        """Resource window constructor"""

        super(LmodQueryWindow, self).__init__(parent, QtCore.Qt.Window)
        self.setupUi(self)

        self.tool_path = settings.LaunchSettings.create().tool_path

        self.config = config.GfxConfig.create()

        self.parent = parent

        self.lmod = lmod.LmodDB(self.config.modules_json_file)

        self.current_module = ""
        self.current_version = ""

        self.on_search_edit_textChanged("")

    @QtCore.pyqtSlot(str)
    def on_search_edit_textChanged(self, search_string):
        
        self.module_list.clear()
        self.version_list.clear()
        self.alt_list.clear()
        self.parent_list.clear()


        self.current_module = ""
        self.current_version = ""

        sorted_modules = self.lmod.find_modules(search_string)
        sorted_modules.sort()

        for module in sorted_modules:
            self.module_list.addItem(module)

    @QtCore.pyqtSlot(int)
    def on_module_list_currentRowChanged(self, idx):
        print("Selected:", idx)

        if idx>=0:

            self.alt_list.clear()
            self.parent_list.clear()

            self.current_module = self.module_list.item(idx).text()
            self.version_list.clear()

            self.versions = self.lmod.find_versions(self.current_module)
            self.version_info = self.lmod.find_version_info(self.current_module)
            self.description = self.lmod.find_description(self.current_module)
            self.default_version = self.lmod.find_default_version(self.current_module)

            self.module_help_text.clear()
            self.module_help_text.insertPlainText(self.description)

            #default_version = self.lmod.module_tree[self.current_module]["default_version"]

            self.version_list.clear()

            for version in self.versions:
                if version == self.default_version:
                    self.version_list.addItem(version)
                    self.version_list.item(self.version_list.count()-1).setForeground(QtCore.Qt.red)
                else:
                    self.version_list.addItem(version)


    @QtCore.pyqtSlot(int)
    def on_version_list_currentRowChanged(self, idx):
        print("Version selected:", idx)

        self.alt_list.clear()
        self.parent_list.clear()
        self.module_cmds_text.clear()
        
        if idx>=0:

            self.current_version = self.version_list.item(idx).text()

            self.current_alternatives = self.lmod.find_parents(self.current_module, self.current_version)

            print(self.current_alternatives)

            self.alt_list.clear()
            if len(self.current_alternatives)>0:
                for i in range(len(self.current_alternatives)):
                    short_form = ""
                    for parent in self.current_alternatives[i]:
                        print(parent)
                        short_form += parent.split("/")[0] + "/"

                    short_form = short_form[:-1]
                    self.alt_list.addItem("%s" % (short_form))
            else:
                self.module_cmds_text.insertPlainText("module load %s/%s" % (self.current_module, self.current_version))



    @QtCore.pyqtSlot(int)
    def on_alt_list_currentIndexChanged(self, idx):

        if idx>=0:

            self.current_alternative = self.current_alternatives[idx]

            self.parent_list.clear()
            self.module_cmds_text.clear()

            for parent in self.current_alternatives[idx]:
                self.parent_list.addItem(parent)
                self.module_cmds_text.insertPlainText("module load %s\n" % parent)

            self.module_cmds_text.insertPlainText("module load %s/%s\n" % (self.current_module, self.current_version))

    @QtCore.pyqtSlot()
    def on_start_term_button_clicked(self):
        cmds = str(self.module_cmds_text.toPlainText())
        cmd_list = cmds.split("\n")

        if len(cmd_list)>1:
            cmd_list.insert(0, "ml purge")
            cmd_row = ";".join(cmd_list)
            print("%smate-terminal" % (cmd_row))
            execute_with_output("%smate-terminal" % (cmd_row))
        else:
            execute_with_output("ml purge;%s;mate-terminal" % (cmds.strip()))

    @QtCore.pyqtSlot()
    def on_copy_cmds_button_clicked(self):
        self.module_cmds_text.selectAll()
        self.module_cmds_text.copy()

if __name__ == "__main__":

    app = QtWidgets.QApplication(sys.argv)

    # Show user interface
    
    form = LmodQueryWindow()
    form.show()

    # Start main application loop

    app.exec_()

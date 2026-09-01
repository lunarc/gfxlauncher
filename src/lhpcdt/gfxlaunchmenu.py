#!/usr/bin/env python
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

"""Interactive launcher menu built from gfxmenu run scripts."""

import argparse
import logging
import os
import subprocess
import sys

from PyQt5 import QtCore, QtGui, QtWidgets

from lhpcdt import config
from lhpcdt.gfxmenu import load_script_database

gfxlaunchmenu_version = "0.9.31"


def script_title(script):
    title = script.variables.get("title", "").strip()
    if title:
        return title
    return os.path.splitext(os.path.basename(script.filename))[0]


def script_category(script, fallback="general"):
    category = script.variables.get("category", "").strip()
    return category or fallback


def normalise_script_database(script_db):
    normalised = {}

    for category, scripts in script_db.items():
        category_name = category or "general"
        normalised[category_name] = sorted(
            scripts,
            key=lambda item: script_title(item).lower()
        )

    return dict(sorted(normalised.items(), key=lambda item: item[0].lower()))


class GfxLaunchMenuWindow(QtWidgets.QWidget):

    def __init__(self, cfg, script_db=None, dryrun=False, parent=None):
        super().__init__(parent)

        self._cfg = cfg
        self._dryrun = dryrun
        self._script_db = normalise_script_database(script_db or {})

        self._build_ui()
        self._populate_categories()
        self._update_summary()

    def _build_ui(self):
        self.setWindowTitle("GFX Launcher Menu")
        self.resize(800, 500)

        outer_layout = QtWidgets.QVBoxLayout(self)

        self.summary_label = QtWidgets.QLabel(self)
        summary_font = self.summary_label.font()
        summary_font.setPointSize(summary_font.pointSize() + 1)
        summary_font.setBold(True)
        self.summary_label.setFont(summary_font)
        outer_layout.addWidget(self.summary_label)

        self.search_edit = QtWidgets.QLineEdit(self)
        self.search_edit.setPlaceholderText("Filter applications by title, category or script name")
        self.search_edit.textChanged.connect(self._populate_applications)
        outer_layout.addWidget(self.search_edit)

        self.splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal, self)
        self.splitter.setChildrenCollapsible(False)
        outer_layout.addWidget(self.splitter, 1)

        self.category_list = QtWidgets.QListWidget(self.splitter)
        self.category_list.currentRowChanged.connect(self._populate_applications)

        self.application_list = QtWidgets.QListWidget(self.splitter)
        self.application_list.currentItemChanged.connect(self._update_details)
        self.application_list.itemDoubleClicked.connect(self._launch_selected_script)

        self.details_widget = QtWidgets.QWidget(self.splitter)
        details_layout = QtWidgets.QVBoxLayout(self.details_widget)

        form_layout = QtWidgets.QFormLayout()
        self.title_value = QtWidgets.QLabel("-")
        self.category_value = QtWidgets.QLabel("-")
        self.launch_mode_value = QtWidgets.QLabel("-")
        self.script_value = QtWidgets.QLabel("-")
        self.script_value.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        form_layout.addRow("Title", self.title_value)
        form_layout.addRow("Category", self.category_value)
        form_layout.addRow("Launch mode", self.launch_mode_value)
        form_layout.addRow("Script", self.script_value)
        details_layout.addLayout(form_layout)

        details_layout.addWidget(QtWidgets.QLabel("Launch command", self.details_widget))

        self.command_preview = QtWidgets.QPlainTextEdit(self.details_widget)
        self.command_preview.setReadOnly(True)
        self.command_preview.setLineWrapMode(QtWidgets.QPlainTextEdit.NoWrap)
        details_layout.addWidget(self.command_preview, 1)

        self.status_label = QtWidgets.QLabel("Ready.", self.details_widget)
        details_layout.addWidget(self.status_label)

        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 2)
        self.splitter.setStretchFactor(2, 3)
        
        self._details_visible = False
        self.details_widget.setVisible(False)

        button_layout = QtWidgets.QHBoxLayout()
        outer_layout.addLayout(button_layout)

        self.details_toggle_button = QtWidgets.QPushButton("Show details", self)
        self.details_toggle_button.clicked.connect(self._toggle_details)
        button_layout.addWidget(self.details_toggle_button)

        self.refresh_button = QtWidgets.QPushButton("Refresh", self)
        self.refresh_button.clicked.connect(self._refresh_scripts)
        button_layout.addWidget(self.refresh_button)

        self.copy_button = QtWidgets.QPushButton("Copy command", self)
        self.copy_button.clicked.connect(self._copy_command)
        self.copy_button.setEnabled(False)
        button_layout.addWidget(self.copy_button)

        button_layout.addStretch(1)

        self.launch_button = QtWidgets.QPushButton("Launch", self)
        self.launch_button.clicked.connect(self._launch_selected_script)
        self.launch_button.setEnabled(False)
        self.launch_button.setDefault(True)
        button_layout.addWidget(self.launch_button)

        close_button = QtWidgets.QPushButton("Close", self)
        close_button.clicked.connect(self.close)
        button_layout.addWidget(close_button)

    def _all_category_names(self):
        return list(self._script_db.keys())

    def _all_scripts(self):
        scripts = []
        for category in self._all_category_names():
            scripts.extend(self._script_db[category])
        return scripts

    def _current_category(self):
        item = self.category_list.currentItem()
        if item is None:
            return None
        return item.data(QtCore.Qt.UserRole)

    def _matches_filter(self, script, filter_text):
        if not filter_text:
            return True

        candidate = " ".join([
            script_title(script),
            script_category(script),
            os.path.basename(script.filename),
        ]).lower()

        return filter_text in candidate

    def _filtered_scripts(self):
        filter_text = self.search_edit.text().strip().lower()
        selected_category = self._current_category()

        if selected_category in (None, "__all__"):
            scripts = self._all_scripts()
        else:
            scripts = list(self._script_db.get(selected_category, []))

        return [script for script in scripts if self._matches_filter(script, filter_text)]

    def _populate_categories(self):
        current_category = self._current_category()

        self.category_list.blockSignals(True)
        self.category_list.clear()

        all_item = QtWidgets.QListWidgetItem("All applications")
        all_item.setData(QtCore.Qt.UserRole, "__all__")
        self.category_list.addItem(all_item)

        for category in self._all_category_names():
            label = "%s (%d)" % (category, len(self._script_db[category]))
            item = QtWidgets.QListWidgetItem(label)
            item.setData(QtCore.Qt.UserRole, category)
            self.category_list.addItem(item)

        row_to_select = 0
        if current_category:
            for row in range(self.category_list.count()):
                item = self.category_list.item(row)
                if item.data(QtCore.Qt.UserRole) == current_category:
                    row_to_select = row
                    break

        self.category_list.setCurrentRow(row_to_select)
        self.category_list.blockSignals(False)
        self._populate_applications()

    def _populate_applications(self, *args):
        current_script = self.selected_script()
        scripts = self._filtered_scripts()

        self.application_list.blockSignals(True)
        self.application_list.clear()

        selected_row = 0

        for index, script in enumerate(scripts):
            item = QtWidgets.QListWidgetItem(script_title(script))
            icon_name = script.variables.get("icon", "").strip()
            if icon_name:
                icon = QtGui.QIcon.fromTheme(icon_name)
                if not icon.isNull():
                    item.setIcon(icon)
            item.setData(QtCore.Qt.UserRole, script)
            self.application_list.addItem(item)

            if current_script is not None and current_script.filename == script.filename:
                selected_row = index

        self.application_list.blockSignals(False)

        if self.application_list.count() > 0:
            self.application_list.setCurrentRow(selected_row)
        else:
            self._update_details()

        self._update_summary(len(scripts))

    def _update_summary(self, filtered_count=None):
        total_categories = len(self._all_category_names())
        total_scripts = len(self._all_scripts())

        if filtered_count is None:
            filtered_count = total_scripts

        if filtered_count == total_scripts:
            self.summary_label.setText(
                "Interactive launch menu with %d applications in %d categories."
                % (total_scripts, total_categories)
            )
        else:
            self.summary_label.setText(
                "Showing %d of %d applications across %d categories."
                % (filtered_count, total_scripts, total_categories)
            )

    def selected_script(self):
        item = self.application_list.currentItem()
        if item is None:
            return None
        return item.data(QtCore.Qt.UserRole)

    def _update_details(self, *args):
        script = self.selected_script()
        has_script = script is not None

        self.copy_button.setEnabled(has_script)
        self.launch_button.setEnabled(has_script)

        if not has_script:
            self.title_value.setText("-")
            self.category_value.setText("-")
            self.launch_mode_value.setText("-")
            self.script_value.setText("-")
            self.command_preview.setPlainText("")
            self.status_label.setText("Ready.")
            return

        self.title_value.setText(script_title(script))
        self.category_value.setText(script_category(script))
        self.launch_mode_value.setText("Direct script" if script.no_launcher else "gfxlaunch")
        self.script_value.setText(script.filename)
        self.command_preview.setPlainText(script.launch_cmd)
        self.status_label.setText("Ready to launch %s." % script_title(script))

    def _copy_command(self, *args):
        script = self.selected_script()
        if script is None:
            return

        QtWidgets.QApplication.clipboard().setText(script.launch_cmd)
        self.status_label.setText("Copied launch command for %s." % script_title(script))

    def _refresh_scripts(self, *args):
        try:
            self._script_db = normalise_script_database(
                load_script_database(self._cfg, dryrun=self._dryrun)
            )
        except Exception as exc:
            QtWidgets.QMessageBox.critical(
                self,
                "Refresh failed",
                "Unable to reload launch scripts.\n\n%s" % exc,
            )
            return

        self._populate_categories()
        self.status_label.setText("Reloaded launch scripts.")

    def _launch_selected_script(self, *args):
        script = self.selected_script()
        if script is None:
            return

        command = script.launch_cmd

        try:
            subprocess.Popen(command, shell=True, start_new_session=True)
        except Exception as exc:
            QtWidgets.QMessageBox.critical(
                self,
                "Launch failed",
                "Unable to start %s.\n\n%s" % (script_title(script), exc),
            )
            return

        self.status_label.setText("Started %s." % script_title(script))

    def _toggle_details(self, *args):
        """Toggle visibility of the details panel."""
        self._details_visible = not self._details_visible
        self.details_widget.setVisible(self._details_visible)
        self.details_toggle_button.setText(
            "Hide details" if self._details_visible else "Show details"
        )


def launch_interactive_menu(cfg, script_db=None, dryrun=False):
    if script_db is None:
        script_db = load_script_database(cfg, dryrun=dryrun)

    app = QtWidgets.QApplication.instance()
    own_application = app is None

    if own_application:
        app = QtWidgets.QApplication(sys.argv)

    window = GfxLaunchMenuWindow(cfg, script_db=script_db, dryrun=dryrun)
    window.show()
    window.raise_()
    window.activateWindow()

    if own_application:
        return app.exec_()

    return window


def main():
    parser = argparse.ArgumentParser(description="Interactive launch menu for gfxlauncher")
    parser.add_argument("--config", help="Show configuration", action="store_true")
    parser.add_argument("--silent", help="Run without banner output", action="store_true")
    parser.add_argument("--verbose", help="Verbose logging", action="store_true")
    parser.add_argument("--dryrun", help="Dry-run script parsing", action="store_true")
    args = parser.parse_args()

    if not args.silent:
        print("LUNARC HPC Desktop - Interactive launch menu - Version %s" % gfxlaunchmenu_version)
        print("Written by Jonas Lindemann (jonas.lindemann@lunarc.lu.se)")
        print("Copyright (C) 2018-2025 LUNARC, Lund University")

    if args.verbose:
        logging.basicConfig(
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%d-%b-%y %H:%M:%S',
            level=logging.DEBUG,
        )

    cfg = config.GfxConfig.create()

    if args.config:
        cfg.print_config()
        return 0

    if not cfg.is_ok:
        print("Somehting is wrong with the configuration.")
        return 1

    return launch_interactive_menu(cfg, dryrun=args.dryrun)


if __name__ == "__main__":
    sys.exit(main())
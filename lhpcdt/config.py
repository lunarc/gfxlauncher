#!/bin/env python
#
# LUNARC HPC Desktop On-Demand graphical launch tool
# Copyright (C) 2017-2022 LUNARC, Lund University
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the  hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
Configuration module

This reads the configuration file and maintains a configuration singleton
for other parts of the application to access configuration options.
"""

import os
import configparser

from . singleton import *


@Singleton
class GfxConfig(object):
    """Launcher configuration"""

    def __init__(self, config_filename=""):

        self.__error_log = []

        self._default_props()

        self.config_filename = ""
        self.config_file_alt1 = "/etc/gfxlauncher.conf"
        self.config_file_alt2 = "/sw/pkg/rviz/etc/gfxlauncher.conf"
        self.config_file_alt3 = os.path.expanduser("~/etc/gfxlauncher.conf")

        if config_filename == "":
            if os.path.isfile(self.config_file_alt1):
                self.config_filename = self.config_file_alt1
            elif os.path.isfile(self.config_file_alt2):
                self.config_filename = self.config_file_alt2
            elif os.path.isfile(self.config_file_alt3):
                self.config_filename = self.config_file_alt3
        else:
            self.config_filename = config_filename

        if not self.parse_config_file():
            self.print_error("Couldn't parse configuration")
            self.is_ok = False
        else:
            self.is_ok = True

    def print_error(self, msg):
        """Print error message"""
        error_msg = "Error: %s" % msg
        print(error_msg)
        self.__error_log.append(error_msg)
    
    def clear_error_log(self):
        self.__error_log.clear()

    @property
    def errors(self):
        return '\n'.join(self.__error_log)

    def _default_props(self):
        """Assign default properties"""
        self.debug_mode = False
        self.script_dir = "/sw/pkg/rviz/sbin/run"
        self.default_part = "rviz"
        self.default_account = "rviz"
        self.grantfile = ""
        self.grantfile_base = ""
        self.grantfile_dir = ""
        self.grantfile_suffix = ""
        self.client_script_dir = "/home/bmjl/Development/gfxlauncher/scripts/client"
        self.applications_dir = "/home/bmjl/test-menu/share/applications"
        self.directories_dir = "/home/bmjl/test-menu/share/desktop-directories"
        self.menu_dir = "/home/bmjl/test-menu/etc/xdg/menus/applications-merged"
        self.menu_filename = "Lunarc-On-Demand.menu"
        self.help_url = ""
        self.browser_command = "firefox"


        self.vgl_path = "/sw/pkg/rviz/vgl/bin/latest"
        self.vgl_connect_template = '%s/vglconnect %s %s/%s'
        self.backend_node = "gfx0"
        self.simple_launch_template = 'gfxlaunch --vgl --title "%s" --partition %s --account %s --exclusive --tasks-per-node=-1 --cmd %s --simplified'
        self.adv_launch_template = 'gfxlaunch --vgl --title "%s" --partition %s --account %s --exclusive --cmd %s'
        self.submit_only_slurm_template = 'gfxlaunch --vgl --title "%s" --partition %s --account %s --only-submit --job=%s --simplified'
        self.direct_scripts = False
        self.feature_descriptions = {}
        self.partition_descriptions = {}
        self.only_submit = False
        self.feature_ignore = ""
        self.part_ignore = ""
        self.use_sacctmgr = True

        self.module_json_file = "/sw/pkg/rviz/share/modules.json"

        self.xfreerdp_path = "/sw/pkg/freerdp/2.0.0-rc4/bin"
        self.xfreerdp_cmdline = '%s /v:%s /u:$USER /d:ad.lunarc /sec:tls /cert-ignore /audio-mode:1 /gfx +gfx-progressive -bitmap-cache -offscreen-cache -glyph-cache +clipboard -themes -wallpaper /size:1280x1024 /dynamic-resolution /t:"LUNARC HPC Desktop Windows 10 (NVIDA V100)"'

        self.notebook_module = "Anaconda3"
        self.jupyterlab_module = "Anaconda3"

    def print_config(self):
        """Print configuration"""

        print("")
        print("-------------------------------")
        print("Graphics Launcher configuration")
        print("-------------------------------")

        print("")
        print("General settings")
        print("")
        print("script_dir = %s" % self.script_dir)
        print("client_script_dir = %s" % self.client_script_dir)
        print("only_submit = %s" % str(self.only_submit))
        print("modules_json_file = %s" % (self.module_json_file))
        print("help_url = %s" % self.help_url)

        print("")
        print("SLURM settings")
        print("")

        print("default_part = %s" % self.default_part)
        print("default_account = %s" % self.default_account)
        print("grantfile = %s" % self.grantfile)
        print("grantfile_base = %s" % self.grantfile)
        print("grantfile_dir = %s" % self.grantfile_dir)
        print("grantfile_suffix = %s" % self.grantfile_suffix)

        print("simple_launch_template = %s" % self.simple_launch_template)
        print("adv_launch_template = %s" % self.adv_launch_template)
        print("feature_ignore = %s" % self.feature_ignore)
        print("part_ignore = %s" % self.part_ignore)
        print("use_sacctmgr = %s" % self.use_sacctmgr)

        print("")
        print("Menu settings")
        print("")

        print("application_dir = %s" % self.applications_dir)
        print("directories_dir = %s" % self.directories_dir)
        print("menu_dir = %s" % self.menu_dir)
        print("menu_filename = %s" % self.menu_filename)

        print("")
        print("VGL settings")
        print("")

        print("vgl_path = %s" % self.vgl_path)
        print("backend_node = %s" % self.backend_node)
        print("vgl_connect_template = %s" % self.vgl_connect_template)

        print("")
        print("XFreeRDP settings")
        print("")

        print("xfreerdp_path = %s" % self.xfreerdp_path)

        print("")
        print("Jupyter/JupyterLab settings")
        print("")

        print("notebook_module = %s" % self.notebook_module)
        print("jupyterlab_module = %s" % self.jupyterlab_module)
        print("browser_command = %s" % self.browser_command)

    def _config_get(self, config, section, option, default_value=""):
        """Safe config retrieval"""

        if config.has_option(section, option):
            return config.get(section, option)
        else:
            return default_value

    def _config_getboolean(self, config, section, option, default_value=False):
        """Safe config retrieval"""

        if config.has_option(section, option):
            return config.getboolean(section, option)
        else:
            return default_value

    def parse_config_file(self):
        """Parse configuration file"""

        if not os.path.isfile(self.config_filename):
            self.print_error("Configuration file %s not found" %
                        self.config_filename)
            return False

        print("Using configuration file : %s" % self.config_filename)

        config = configparser.RawConfigParser()
        config.read(self.config_filename)

        # Check for correct sections

        try:
            self.script_dir = self._config_get(config, "general", "script_dir")
            self.client_script_dir = self._config_get(
                config, "general", "client_script_dir")
            self.debug_mode = self._config_getboolean(
                config, "general", "debug_mode")
            self.only_submit = self._config_getboolean(
                config, "general", "only_submit")
            self.modules_json_file = self._config_get(
                config, "general", "modules_json_file")
            self.help_url = self._config_get(
                config, "general", "help_url").replace('"', '')
            self.browser_command = self._config_get(
                config, "general", "browser_command")

            self.default_part = self._config_get(
                config, "slurm", "default_part")
            self.default_account = self._config_get(
                config, "slurm", "default_account")
            self.grantfile = self._config_get(config, "slurm", "grantfile")
            self.grantfile_base = self._config_get(
                config, "slurm", "grantfile_base")
            self.grantfile_dir = self._config_get(
                config, "slurm", "grantfile_dir")
            self.grantfile_suffix = self._config_get(
                config, "slurm", "grantfile_suffix")
            self.feature_ignore = self._config_get(
                config, "slurm", "feature_ignore")
            self.part_ignore = self._config_get(config, "slurm", "part_ignore")

            self.simple_launch_template = self._config_get(
                config, "slurm", "simple_launch_template")
            self.adv_launch_template = self._config_get(
                config, "slurm", "adv_launch_template")
            self.submit_only_slurm_template = self._config_get(
                config, "slurm", "submit_only_slurm_template")
            self.use_sacctmgr = self._config_getboolean(config, "slurm", "use_sacctmgr", False)

            self.applications_dir = self._config_get(
                config, "menus", "applications_dir")
            self.directories_dir = self._config_get(
                config, "menus", "directories_dir")
            self.menu_dir = self._config_get(config, "menus", "menu_dir")
            self.menu_filename = self._config_get(
                config, "menus", "menu_filename")
            self.direct_scripts = self._config_getboolean(
                config, "menus", "direct_scripts")

            self.vgl_path = self._config_get(config, "vgl", "vgl_path")
            self.backend_node = self._config_get(config, "vgl", "backend_node")
            self.vgl_connect_template = self._config_get(
                config, "vgl", "vglconnect_template")

            self.xfreerdp_path = self._config_get(
                config, "xfreerdp", "xfreerdp_path")

            self.notebook_module = self._config_get(
                config, "jupyter", "notebook_module")
            self.jupyterlab_module = self._config_get(
                config, "jupyter", "jupyterlab_module")

        except configparser.Error as e:
            self.print_error(e)
            return False

        # Check for feature descriptions

        try:
            slurm_options = config.options("slurm")
            for option in slurm_options:
                if option.find("feature_") != -1:
                    descr = self._config_get(config, "slurm", option)
                    feature = option.split("_")[1]
                    self.feature_descriptions[feature] = descr.strip('"')
        except configparser.Error as e:
            self.print_error(e)
            return False

        # Check for partition descriptions

        try:
            slurm_options = config.options("slurm")
            for option in slurm_options:
                if option.find("part_") != -1:
                    descr = self._config_get(config, "slurm", option)
                    partition = option.split("_")[1]
                    self.partition_descriptions[partition] = descr.strip('"')
        except configparser.Error as e:
            self.print_error(e)
            return False

        # Check for partition groups

        self.part_groups = {}

        try:
            slurm_options = config.options("slurm")
            for option in slurm_options:
                if option.find("group_") != -1:
                    parts = self._config_get(config, "slurm", option)
                    group = option.split("_")[1].strip()
                    partitions = parts.split(",")
                    self.part_groups[group] = []
                    for part in partitions:
                        self.part_groups[group].append(part.strip())

        except configparser.Error as e:
            self.print_error(e)
            return False

        return True

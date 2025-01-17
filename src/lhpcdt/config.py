#!/bin/env python
#
# LUNARC HPC Desktop On-Demand graphical launch tool
# Copyright (C) 2017-2024 LUNARC, Lund University
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

import os, sys
import configparser

from . singleton import *


@Singleton
class GfxConfig(object):
    """Launcher configuration"""

    def __init__(self, config_filename=""):

        self.__error_log = []

        self._default_props()

        self.config_filename = ""

        # Find where our application dir is located

        app_dir = os.path.dirname(os.path.abspath(sys.argv[0]))

        config_alt_loc = []
        config_alt_loc.append("/etc/gfxlauncher.conf")
        config_alt_loc.append(os.path.join(app_dir, "../etc/gfxlauncher.conf"))
        config_alt_loc.append(os.path.join(app_dir, "../ondemand-dt/etc/gfxlauncher.conf"))
        config_alt_loc.append(os.path.join(app_dir, "etc/gfxlauncher.conf"))
        config_alt_loc.append("/sw/pkg/ondemand-dt/etc/gfxlauncher.conf")
        config_alt_loc.append("/pdc/software/tools/thinlinc/etc/gfxlauncher.conf")
        config_alt_loc.append("/sw/pkg/rviz/etc/gfxlauncher.conf")

        if config_filename == "":

            # Set environment variable overrides default locations.

            if "GFXLAUNCHER_CONFIG" in os.environ:
                self.config_value = os.environ["GFXLAUNCHER_CONFIG"]
                if os.path.isfile(self.config_value):
                    self.config_filename = self.config_value
            else:
                for config_loc in config_alt_loc:
                    if os.path.isfile(os.path.expanduser(os.path.realpath(config_loc))):
                        self.config_filename = os.path.abspath(os.path.expanduser(config_loc))
                        break
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
        
        self.applications_direct_dir = "/home/bmjl/test-menu/share/applications"
        self.directories_direct_dir = "/home/bmjl/test-menu/share/desktop-directories"
        self.menu_direct_dir = "/home/bmjl/test-menu/etc/xdg/menus/applications-merged"
        self.menu_direct_filename = "Lunarc-On-Demand-Direct.menu"

        self.menu_location = "~/.config/menus/applications-merged"
        self.app_location = "~/.local/share/applications"
        self.dir_location = "~/.local/share/desktop-directories"
        self.ondemand_location = "~/.local/share/ondemand-dt"

        self.menu_prefix = "LUNARC - "
        self.desktop_entry_prefix = "gfx-"
        
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
        self.jupyter_use_localhost = False
        self.conda_source_env = ""
        self.conda_use_env = ""

        self.part_groups = {}
        self.part_groups_defaults = {}

        self.default_tasks = 1
        self.default_memory = 3000
        self.default_exclusive = False


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

        print("menu_location = %s" % self.menu_location)
        print("app_location = %s" % self.app_location)
        print("dir_location = %s" % self.dir_location)
        print("ondemand_location = %s" % self.ondemand_location)                

        print("menu_prefix = '%s'" % self.menu_prefix)
        print("desktop_entry_prefix = %s" % self.desktop_entry_prefix)

        # print("application_dir = %s" % self.applications_dir)
        # print("directories_dir = %s" % self.directories_dir)
        # print("menu_dir = %s" % self.menu_dir)
        # print("menu_filename = %s" % self.menu_filename)

        # print("application_direct_dir = %s" % self.applications_dir)
        # print("directories_direct_dir = %s" % self.directories_dir)
        # print("menu_direct_dir = %s" % self.menu_dir)
        # print("menu_direct_filename = %s" % self.menu_filename)


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
        print("jupyter_use_localhost = %s" % self.jupyter_use_localhost)
        print("conda_source_env = %s" % self.conda_source_env)
        print("conda_use_env = %s" % self.conda_use_env)

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
            self.install_dir = self._config_get(config, "general", "install_dir")

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
            self.menu_prefix = self._config_get(config, "menus", "menu_prefix").replace('"', '')
            self.desktop_entry_prefix = self._config_get(config, "menus", "desktop_entry_prefix").replace('"', '')

            self.menu_location = self._config_get(config, "menus", "menu_location", self.menu_location)
            self.app_location = self._config_get(config, "menus", "app_location", self.app_location)
            self.dir_location = self._config_get(config, "menus", "dir_location", self.dir_location)
            self.ondemand_location = self._config_get(config, "menus", "ondemand_location", self.ondemand_location)

            self.applications_direct_dir = self._config_get(
                config, "menus-direct", "applications_dir")
            self.directories_direct_dir = self._config_get(
                config, "menus-direct", "directories_dir")
            self.menu_direct_dir = self._config_get(config, "menus-direct", "menu_dir")
            self.menu_direct_filename = self._config_get(
                config, "menus-direct", "menu_filename")
            self.direct_scripts = self._config_getboolean(
                config, "menus-direct", "direct_scripts")

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
            self.conda_source_env = self._config_get(
                config, "jupyter", "conda_source_env")
            self.conda_use_env = self._config_get(
                config, "jupyter", "conda_use_env")

            self.jupyter_use_localhost = self._config_getboolean(config, "jupyter", "jupyter_use_localhost", False)

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
        self.part_groups_defaults = {}

        try:
            slurm_options = config.options("slurm")
            for option in slurm_options:
                if option.find("group_") != -1:
                    parts = self._config_get(config, "slurm", option)
                    if len(option.split("_"))==2:
                        group = option.split("_")[1].strip()
                        partitions = parts.split(",")
                        self.part_groups[group] = []
                        for part in partitions:
                            self.part_groups[group].append(part.strip())
                    elif len(option.split("_"))==3:
                        group = option.split("_")[1].strip()
                        directive = option.split("_")[2].split(" ")[0].strip()
                        
                        tasks = 1
                        memory = -1
                        exclusive = False

                        if not group in self.part_groups_defaults:
                            self.part_groups_defaults[group] = {}

                        if directive == "tasks":
                            self.part_groups_defaults[group]["tasks"] = int(parts)
                        if directive == "memory":
                            self.part_groups_defaults[group]["memory"] = int(parts)
                        if directive == "exclusive":
                            if parts.strip() == "yes":
                                exclusive = True
                            else:
                                exclusive = False
                            self.part_groups_defaults[group]["exclusive"] = exclusive
                  
        except configparser.Error as e:
            self.print_error(e)
            return False

        try:
            tasks = self._config_get(
                config, "slurm", "default_tasks", "1")
            memory = self._config_get(
                config, "slurm", "default_memory", "3000")
            exclusive = self._config_get(
                config, "slurm", "default_exclusive", "no")
            
            if exclusive == "yes":
                exclusive = True
            else:
                exclusive = False

            self.default_tasks = int(tasks)
            self.default_memory = int(memory)
            self.default_exclusive = exclusive
                  
        except configparser.Error as e:
            self.print_error(e)
            return False


        return True

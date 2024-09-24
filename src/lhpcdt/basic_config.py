#!/usr/bin/env python
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

from . import lrms

import configparser
import re
import string


class BasicConfig:
    """
    BasicConfig is a class that manages configuration settings for a specific application.

    Attributes:
        script_dir (str): Directory where scripts are located.
        install_dir (str): Directory where the application is installed.
        help_url (str): URL for the help documentation.
        browser_cmd (str): Command to open the browser.
        features (dict): Dictionary of features with their descriptions.
        partitions (dict): Dictionary of partitions with their descriptions.
        groups (dict): Dictionary of groups with their associated partitions.
        default_tasks (int): Default number of tasks.
        default_memory (int): Default memory allocation.
        default_exclusive (bool): Default exclusivity setting.
        default_part (str): Default partition.
        default_account (str): Default account.
        use_sacctmgr (bool): Flag to indicate if sacctmgr should be used.
        menu_prefix (str): Prefix for menu items.
        desktop_entry_prefix (str): Prefix for desktop entries.
        vgl_bin (str): Path to the vglconnect binary.
        vgl_path (str): Path to the vgl directory.
        notebook_module (str): Module for Jupyter Notebook.
        jupyterlab_module (str): Module for JupyterLab.
        __config (str): Internal string to store the configuration.

    Methods:
        clear(): Clears the internal configuration string.
        section(name): Adds a section header to the configuration.
        new_line(): Adds a new line to the configuration.
        var(name, value): Adds a variable to the configuration.
        str_var(name, value): Adds a string variable to the configuration.
        list_var(f, name, value): Adds a list variable to the configuration.
        create_config(): Creates the configuration string based on the attributes.
        save(filename): Saves the configuration to a file.
        __str__(): Returns the configuration as a string.
    """

    def __init__(self):
        """
        Initializes the configuration with default values for the GFX Launcher.
        """

        self.clear()
        self.init_defaults()
        self.query_slurm()

    def init_defaults(self):
        """
        Initializes the configuration with default values for the GFX Launcher.
        """
        self.script_dir = "/sw/pkg/ondemand-dt/run"
        self.install_dir = "/sw/pkg/gfxlauncher"
        self.help_url = "https://lunarc-documentation.readthedocs.io/en/latest/getting_started/gfxlauncher/"
        self.browser_cmd = "firefox"

        self.features = {
        }

        self.partitions = {
        }
        self.groups = {
        }

        self.group_defaults = {
        }

        self.default_tasks = 1
        self.default_memory = 5300
        self.default_exclusive = False
        self.default_part = ""
        self.default_account = ""

        self.use_sacctmgr = True

        self.menu_prefix = "Applications - "
        self.desktop_entry_prefix = "gfx-"

        self.vgl_bin = "/usr/bin/vglconnect"
        self.vgl_path = "/usr/bin"

        self.notebook_module = "Anaconda3"
        self.jupyterlab_module = "Anaconda3"

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

        for part in slurm.partitions:
            self.partitions[part] = ""

        for part in self.partitions:
            features = slurm.query_features(part)

            for feature in features:
                self.features[feature] = ""

    def clear(self):
        """
        Clears the current configuration by setting it to an empty string.
        """
        self.__config = ""

    def section(self, name):
        """
        Adds a new section header to the configuration.

        Args:
            name (str): The name of the section to be added.

        Returns:
            None
        """
        self.__config += f"[{name}]\n"

    def new_line(self):
        """
        Appends a new line character to the existing configuration string.

        This method modifies the internal configuration string by adding a newline
        character ("\n") at the end. It does not return any value.

        Returns:
            None
        """
        self.__config += "\n"

    def var(self, name, value):
        """
        Adds a configuration variable to the internal configuration string.

        Args:
            name (str): The name of the configuration variable.
            value (str): The value of the configuration variable.
        """
        if value != "":
            self.__config += f"{name} = {value}\n"

    def str_var(self, name, value):
        """
        Adds a string variable to the configuration.

        Args:
            name (str): The name of the variable.
            value (str): The value of the variable.
        """
        if value != "":
            self.__config += f"{name} = \"{value}\"\n"

    def bool_var(self, name, value):
        """
        Adds a boolean variable to the configuration.

        Args:
            name (str): The name of the variable.
            value (bool): The value of the variable.
        """
        if value:
            self.__config += f"{name} = yes\n"
        else:
            self.__config += f"{name} = no\n"

    def list_var(self, f, name, value):
        """
        Appends a formatted string to the configuration.

        This method takes a function `f`, a string `name`, and a list `value`. 
        It applies the function `f` to each element in the list `value`, joins 
        the results with a comma, and appends the formatted string to the 
        configuration attribute `__config`.

        Args:
            f (function): A function to apply to each element in the list `value`.
            name (str): The name to be used in the formatted string.
            value (list): A list of elements to be processed by the function `f`.

        Returns:
            None
        """

        group_str = ", ".join([f(x) for x in value])
        self.__config += f"{name} = {group_str}\n"

    def create_config(self):
        """
        Generates and clears the configuration settings for various sections including 
        general, slurm, menus, vgl, and jupyter. This method organizes the configuration 
        into sections and assigns values to various configuration variables.

        Sections:
        - general: Includes script and install directories, help URL, and browser command.
        - slurm: Includes features, partitions, groups, and default settings for SLURM.
        - menus: Includes menu prefix and desktop entry prefix.
        - vgl: Includes VirtualGL binary and path.
        - jupyter: Includes notebook and JupyterLab modules.

        The method uses helper functions to add variables, string variables, and list variables 
        to the configuration.
        """
        self.clear()
        self.section("general")
        self.new_line()
        self.var("script_dir", self.script_dir)
        self.var("install_dir", self.install_dir)
        self.str_var("help_url", self.help_url)
        self.str_var("browser_cmd", self.browser_cmd)
        self.new_line()

        self.section("slurm")
        self.new_line()

        n_features = 0

        for k, v in self.features.items():
            if v != "":
                self.str_var(f"feature_{k}", v)
                n_features += 1

        if n_features > 0:
            self.new_line()

        n_partitions = 0

        for k, v in self.partitions.items():
            if v != "":
                self.str_var(f"part_{k}", v)
                n_partitions += 1

        if n_partitions > 0:
            self.new_line()

        n_groups = 0

        for k, v in self.groups.items():
            if v != "":
                self.list_var(lambda x: f"{x}", f"group_{k}", v)
                n_groups += 1

        if n_groups > 0:
            self.new_line()

        n_group_props = 0

        for k, v in self.group_defaults.items():
            if "tasks" in v:
                self.var(f"group_{k}_tasks", v["tasks"])
                n_group_props += 1
            if "memory" in v:
                self.var(f"group_{k}_memory", v["memory"])
                n_group_props += 1
            if "exclusive" in v:
                self.bool_var(f"group_{k}_exclusive", v["exclusive"])
                n_group_props += 1

        if n_group_props > 0:
            self.new_line()

        self.var("default_part", self.default_part)
        self.var("default_account", self.default_account)
        self.var("default_tasks", self.default_tasks)
        self.var("default_memory", self.default_memory)
        self.bool_var("default_exclusive", self.default_exclusive)
        self.new_line()
        self.bool_var("use_sacctmgr", self.use_sacctmgr)
        self.new_line()

        self.section("menus")
        self.new_line()
        self.str_var("menu_prefix", self.menu_prefix)
        self.str_var("desktop_entry_prefix", self.desktop_entry_prefix)
        self.new_line()

        self.section("vgl")
        self.new_line()
        self.str_var("vgl_bin", self.vgl_bin)
        self.str_var("vgl_path", self.vgl_path)
        self.new_line()

        self.section("jupyter")
        self.new_line()
        self.str_var("notebook_module", self.notebook_module)
        self.str_var("jupyterlab_module", self.jupyterlab_module)

    def save(self, filename):
        """
        Saves the current configuration to a file.

        This method first creates the configuration by calling `create_config()`
        and then writes the configuration to the specified file.

        Args:
            filename (str): The path to the file where the configuration will be saved.
        """
        self.create_config()
        with open(filename, 'w') as f:
            f.write(self.__config)

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

    def _config_getint(self, config, section, option, default_value=0):
        """Safe config retrieval"""

        if config.has_option(section, option):
            return config.getint(section, option)
        else:
            return default_value
        
    def _config_getquoted(self, config, section, option, default_value=""):
        """Safe config retrieval"""

        if config.has_option(section, option):
            quoted_string = config.get(section, option)
            return quoted_string.strip("\"")
        else:
            return default_value

    def load(self, filename):
        """
        Loads the configuration from a file.

        This method reads the configuration from the specified file and stores it
        in the internal configuration attribute `__config`.

        Args:
            filename (str): The path to the file containing the configuration.
        """
        self.clear()
        self.init_defaults()
        self.query_slurm()

        config = configparser.RawConfigParser()
        config.read(filename)

        self.script_dir = self._config_get(
            config, "general", "script_dir", self.script_dir)
        self.install_dir = self._config_get(
            config, "general", "install_dir", self.install_dir)
        self.help_url = self._config_getquoted(
            config, "general", "help_url", self.help_url)
        self.browser_cmd = self._config_get(
            config, "general", "browser_cmd", self.browser_cmd)

        self.menu_prefix = self._config_get(
            config, "menus", "menu_prefix", self.menu_prefix)
        self.desktop_entry_prefix = self._config_get(
            config, "menus", "desktop_entry_prefix", self.desktop_entry_prefix)

        self.vgl_bin = self._config_get(config, "vgl", "vgl_bin", self.vgl_bin)
        self.vgl_path = self._config_get(
            config, "vgl", "vgl_path", self.vgl_path)

        self.notebook_module = self._config_get(
            config, "jupyter", "notebook_module", self.notebook_module)
        self.jupyterlab_module = self._config_get(
            config, "jupyter", "jupyterlab_module", self.jupyterlab_module)

        self.default_tasks = self._config_getint(
            config, "slurm", "default_tasks", self.default_tasks)
        self.default_memory = self._config_getint(
            config, "slurm", "default_memory", self.default_memory)
        self.default_exclusive = self._config_getboolean(
            config, "slurm", "default_exclusive", self.default_exclusive)
        self.default_part = self._config_get(
            config, "slurm", "default_part", self.default_part)
        self.default_account = self._config_get(
            config, "slurm", "default_account", self.default_account)
        self.use_sacctmgr = self._config_getboolean(
            config, "slurm", "use_sacctmgr", self.use_sacctmgr)

        slurm_items = config.items("slurm")
        for key, value in slurm_items:
            if key.startswith("feature_"):
                self.features[key[8:]] = value.strip("\"")
            elif key.startswith("part_"):
                self.partitions[key[5:]] = value.strip("\"")
            elif key.startswith("group_"):
                if "_tasks" in key:
                    group_name = key.split("_")[1]
                    group_tasks = int(value)
                    if group_name not in self.group_defaults:
                        self.group_defaults[group_name] = {}
                    self.group_defaults[group_name]["tasks"] = group_tasks
                elif "_memory" in key:
                    group_name = key.split("_")[1]
                    group_memory = int(value)
                    if group_name not in self.group_defaults:
                        self.group_defaults[group_name] = {}
                    self.group_defaults[group_name]["memory"] = group_memory
                elif "_exclusive" in key:
                    group_name = key.split("_")[1]
                    group_exclusive = value == "yes"
                    if group_name not in self.group_defaults:
                        self.group_defaults[group_name] = {}
                    self.group_defaults[group_name]["exclusive"] = group_exclusive
                else:
                    self.groups[key[6:]] = [v.strip() for v in value.split(",")]

    def __str__(self):
        """
        Returns a string representation of the configuration.

        This method calls `create_config` to generate the configuration
        and then returns the resulting configuration string.

        Returns:
            str: The configuration string.
        """
        self.create_config()
        return self.__config


if __name__ == "__main__":

    config = BasicConfig()
    print(config)

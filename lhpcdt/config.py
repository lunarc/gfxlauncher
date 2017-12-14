#!/bin/env python

import os, ConfigParser

from singleton import *

def print_error(msg):
    """Print error message"""
    print("Error: %s" % msg)


@Singleton
class GfxConfig(object):
    """Launcher configuration"""
    def __init__(self, config_filename = ""):

        self._default_props()

        self.config_file_alt1 = "/etc/gfxlauncher.conf"
        self.config_file_alt2 = "/sw/pkg/rviz/etc/gfxlauncher.conf"

        if config_filename == "":
            if os.path.isfile(self.config_file_alt1):
                self.config_filename = self.config_file_alt1
            elif os.path.isfile(self.config_file_alt2):
                self.config_filename = self.config_file_alt2
        else:
            self.config_filename = config_filename            

        if not self.parse_config_file():
            print_error("Couldn't parse configuration")
            self.is_ok = False
        else:
            self.is_ok = True


    def _default_props(self):
        """Assign default properties"""
        self.debug_mode = False
        self.script_dir = "/sw/pkg/rviz/sbin/run"
        self.default_part = "lvis"
        self.default_account = "lvis-test"
        self.grantfile = ""
        self.client_script_dir = "/home/bmjl/Development/gfxlauncher/scripts/client"
        self.applications_dir = "/home/bmjl/test-menu/share/applications"
        self.menu_dir = "/home/bmjl/test-menu/etc/xdg/menus/applications-merged"
        self.menu_filename = "Lunarc-On-Demand.menu"
        self.vgl_bin = "/sw/pkg/rviz/vgl/bin/latest"
        self.backend_node = "gfx0"
        self.vgl_connect_template = '%s/vglconnect %s %s/%s'
        self.simple_slurm_template = 'gfxlaunch --vgl --title "%s" --partition %s --account %s --exclusive --cmd %s --simplified'
        self.adv_slurm_template = 'gfxlaunch --vgl --title "%s" --partition %s --account %s --exclusive --cmd %s'
        self.direct_scripts = False

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

        print("")
        print("SLURM settings")
        print("")

        print("default_part = %s" % self.default_part)
        print("default_account = %s" % self.default_account)
        print("grantfile = %s" % self.grantfile)

        print("simple_slurm_template = %s" % self.simple_slurm_template)
        print("adv_slurm_template = %s" % self.adv_slurm_template)

        print("")
        print("Menu settings")
        print("")

        print("application_dir = %s" % self.applications_dir)
        print("menu_dir = %s" % self.menu_dir)
        print("menu_filename = %s" % self.menu_filename)

        print("")
        print("VGL settings")
        print("")

        print("vgl_bin = %s" % self.vgl_bin)
        print("backend_node = %s" % self.backend_node)
        print("vgl_connect_template = %s" % self.vgl_connect_template)
        
    def _config_get(self, config, section, option):
        """Safe config retrieval"""
        
        if config.has_option(section, option):
            return config.get(section, option)
        else:
            return ""

    def _config_getboolean(self, config, section, option):
        """Safe config retrieval"""

        if config.has_option(section, option):
            return config.getboolean(section, option)
        else:
            return ""


    def parse_config_file(self):
        """Parse configuration file"""

        if not os.path.isfile(self.config_filename):
            print_error("Configuration file %s not found" % self.config_filename)
            return False

        print("Using configuration file : %s" % self.config_filename)

        config = ConfigParser.ConfigParser()
        config.read(self.config_filename)

        # Check for correct sections

        try:
            self.script_dir = self._config_get(config, "general", "script_dir")
            self.client_script_dir = self._config_get(config, "general", "client_script_dir")
            self.debug_mode = self._config_getboolean(config, "general", "debug_mode")

            self.default_part = self._config_get(config, "slurm", "default_part")
            self.default_account = self._config_get(config, "slurm", "default_account")
            self.grantfile = self._config_get(config, "slurm", "grantfile")

            self.simple_slurm_template = self._config_get(config, "slurm", "simple_slurm_template")
            self.adv_slurm_template = self._config_get(config, "slurm", "adv_slurm_template")

            self.applications_dir = self._config_get(config, "menus", "applications_dir")
            self.menu_dir = self._config_get(config, "menus", "menu_dir")
            self.menu_filename = self._config_get(config, "menus", "menu_filename")
            self.direct_scripts = self._config_getboolean(config, "menus", "direct_scripts")

            self.vgl_bin = self._config_get(config, "vgl", "vgl_bin")
            self.backend_node = self._config_get(config, "vgl", "backend_node")
            self.vgl_connect_template = self._config_get(config, "vgl", "vglconnect_template")
        except ConfigParser.Error:
            print_error("Failed to read configuration.")
            return False

        return True

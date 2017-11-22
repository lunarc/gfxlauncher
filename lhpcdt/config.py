#!/bin/env python

import os, sys, ConfigParser

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
            self.script_dir = config.get("general", "script_dir")
            self.client_script_dir = config.get("general", "client_script_dir")

            self.default_part = config.get("slurm", "default_part")
            self.default_account = config.get("slurm", "default_account")
            self.grantfile = config.get("slurm", "grantfile")

            self.simple_slurm_template = config.get("slurm", "simple_slurm_template")
            self.adv_slurm_template = config.get("slurm", "adv_slurm_template")

            self.applications_dir = config.get("menus", "applications_dir")
            self.menu_dir = config.get("menus", "menu_dir")
            self.menu_filename = config.get("menus", "menu_filename")

            self.vgl_bin = config.get("vgl", "vgl_bin")
            self.backend_node = config.get("vgl", "backend_node")
            self.vgl_connect_template = config.get("vgl", "vglconnect_template")
        except ConfigParser.Error:
            print_error("Failed to read configuration.")
            return False

        return True

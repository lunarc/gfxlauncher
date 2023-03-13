#!/bin/env python
#
# LUNARC HPC Desktop On-Demand graphical launch tool
# Copyright (C) 2017-2023 LUNARC, Lund University
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

"""
gfxconvert script for creating menus from launch scripts

This tool parses a given directory for launch scripts and from special 
tags in the scripts creates standardised Linux menus. The tools is 
configured from the GfxLauncher configuration file.
"""

import os
import sys
import getpass
import argparse

from lhpcdt import integration as it
from lhpcdt import scripts as scr

if __name__ == "__main__":

    run_scripts = scr.RunScripts("/home/lindemann/Development/gfxlauncher/tests/scripts")
    run_scripts.parse()

    script_db = run_scripts.database

    for category, scripts in script_db.items():
        for script in scripts:
            print(category, ":", script.variables["title"], script.filename)

    user_menu = it.UserMenus()
    user_menu.menu_name_prefix = "LUNARC - "
    user_menu.add_scripts(script_db)
    user_menu.generate()

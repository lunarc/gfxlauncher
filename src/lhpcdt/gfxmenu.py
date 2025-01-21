#!/bin/env python
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
import time
import logging

from lhpcdt import integration as it
from lhpcdt import scripts as scr
from lhpcdt import config

gfxmenu_copyright = """LUNARC HPC Desktop On-Demand - Version %s
Copyright (C) 2017-2025 LUNARC, Lund University
This program comes with ABSOLUTELY NO WARRANTY; for details see LICENSE.
This is free software, and you are welcome to redistribute it
under certain conditions; see LICENSE for details.
"""
gfxmenu_copyright_short = """LUNARC HPC Desktop On-Demand - %s"""
gfxmenu_version = "0.9.18"


def main():
    # ----- Parse command line arguments

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--no-launcher", help="Generate menus and scripts with direct launch.", action="store_true")
    parser.add_argument(
        "--config", help="Show configuration", action="store_true")
    parser.add_argument(
        "--silent", help="Run without output", action="store_true")
    parser.add_argument("--verbose", help="Verbose logging",
                        action="store_true")
    parser.add_argument("--force", help="Force refresh menu entries", action="store_true")
    args = parser.parse_args()

    # ----- Show version information

    if not args.silent:
        print(("LUNARC HPC Desktop - User menu tool - Version %s" % gfxmenu_version))
        print("Written by Jonas Lindemann (jonas.lindemann@lunarc.lu.se)")
        print("Copyright (C) 2018-2025 LUNARC, Lund University")

    # ----- Read configuration

    if args.verbose:
        logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s',
                            datefmt='%d-%b-%y %H:%M:%S', level=logging.DEBUG)

    cfg = config.GfxConfig.create()

    if args.config:
        cfg.print_config()
        sys.exit(0)

    if not cfg.is_ok:
        print("Somehting is wrong with the configuration.")
        sys.exit(0)

    # ----- Parse script directory

    run_scripts = scr.RunScripts(cfg.script_dir)
    run_scripts.launcher = os.path.join(cfg.install_dir, 'gfxlaunch')
    run_scripts.parse()

    script_db = run_scripts.database

    # ----- Create user menu

    user_menu = it.UserMenus()
    user_menu.menu_name_prefix = cfg.menu_prefix
    user_menu.desktop_entry_prefix = cfg.desktop_entry_prefix
    user_menu.add_scripts(script_db)
    user_menu.force_refresh = args.force
    user_menu.generate()


if __name__ == "__main__":

    main()

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

if __name__ == "__main__":

    desktop_entry = it.DesktopEntry()
    desktop_entry.name = "VS Code 2"
    desktop_entry.exec = "code"
    desktop_entry.categories.append("Accessories")

    desktop_menu = it.DesktopMenu()
    desktop_menu.add_entry(desktop_entry)
    desktop_menu.generate()

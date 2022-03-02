#!/bin/env python
#
# LUNARC HPC Desktop On-Demand graphical launch tool
# Copyright (C) 2017-2021 LUNARC, Lund University
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

from lhpcdt import config, desktop

# --- Version information

gfxconvert_version = "0.8.4"

# --- Fix search path for tool

tool_path = os.path.dirname(os.path.abspath(sys.argv[0]))
sys.path.append(tool_path)

# --- Functions

def parse_and_update(filename, tag, new_value):
    """Parse run-script for metadata"""

    # LDT category = "Post Processing"
    # LDT title = "ParaView 5.4.1"
    # LDT part = "snic"
    # LDT job = "notebook"
    # LDT group = "ondemand"

    variables = {}
    variable_lines ={}

    tag_begin = -1
    tag_end = -1

    script_file = open(filename, "r")
    lines = script_file.readlines()
    script_file.close()

    for i, line in enumerate(lines):
        if line.find("##LDT") != -1:
            commands = line.split("##LDT")[1]
            variable_name = commands.split("=")[0].strip()
            variable_value = commands.split("=")[1].strip().strip('"')
            variables[variable_name] = variable_value
            variable_lines[variable_name] = [i, line]
            if tag_begin == -1:
                tag_begin = i
            
            tag_end = i

    if tag in variables:
        lines[variable_lines[tag][0]] = '##LDT %s = "%s"' % (tag, new_value)
    else:
        lines.insert(tag_end+1, '##LDT %s = "%s"' % (tag, new_value))
    
    for line in lines:
        print(line.strip())

    return lines

def parse_script_dir(tag, new_value):
    """Parse script directory for run-scripts"""

    cfg = config.GfxConfig.create()
    script_dir = cfg.script_dir

    for script in os.listdir(script_dir):
        if script.endswith('.sh') and script.startswith('run_') and script.find('rviz-server') != -1:
            filename = os.path.join(script_dir, script)
            new_lines = parse_and_update(filename, tag, new_value)
            with open(filename, "w") as f:
                for line in new_lines:
                    f.write(line)



if __name__ == '__main__':

    # Show version information

    cfg = config.GfxConfig.create()

    #parse_script_dir()

    parse_script_dir("group", "ondemand")

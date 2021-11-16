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


def create_slurm_script(server_fname, slurm_fname, descr, metadata={}, dryrun=False):
    """Create script for running through SLURM"""

    cfg = config.GfxConfig.create()

    client_script_filename = os.path.join(cfg.client_script_dir, slurm_fname)
    server_script_filename = os.path.join(cfg.script_dir, server_fname)

    try:

        client_file = None

        if dryrun:
            client_file = sys.stdout
            client_file.write("slurmscript = "+client_script_filename+"\n")
        else:
            client_file = open(client_script_filename, "w")

        part = cfg.default_part

        vgl = True

        submit_only_slurm_template = cfg.submit_only_slurm_template
        simple_launch_template = cfg.simple_launch_template

        if "vgl" in metadata:
            vgl = metadata["vgl"]

        if vgl == "no":
            submit_only_slurm_template = cfg.submit_only_slurm_template.replace('--vgl', '')
            simple_launch_template = cfg.simple_launch_template.replace('--vgl', '')

        if "part" in metadata:
            part = metadata["part"]

        if "job" in metadata:
            job = metadata["job"]
            client_file.write(submit_only_slurm_template %
                            (descr, part, cfg.default_account, job))
        else:
            client_file.write(simple_launch_template % (
                descr, part, cfg.default_account, server_script_filename))

    except PermissionError:
        print("Couldn't write, %s, check permissions." % client_script_filename)
    finally:
        if not dryrun:
            if client_file != None:
                client_file.close()
                os.chmod(client_script_filename, 0o755)


def create_desktop_entry(script, descr, metadata={}, dryrun=False):
    """Create desktop entry for script"""

    print(("Creating desktop entry '%s'" % script))
    desktop_filename = os.path.join(cfg.applications_dir, "%s.desktop" % descr.replace("/","-"))
    script_filename = os.path.join(cfg.client_script_dir, script)

    entry = desktop.DesktopEntry(dryrun)
    entry.filename = desktop_filename
    entry.terminal = False
    entry.icon = ""
    if "title" in metadata:
        entry.name = metadata["title"]
    else:
        entry.name = descr
    entry.exec_file = "%s" % script_filename
    entry.write()

    return entry


def parse_script_metadata(filename):
    """Parse run-script for metadata"""

    # LDT category = "Post Processing"
    # LDT title = "ParaView 5.4.1"
    # LDT part = "snic"
    # LDT job = "notebook"

    variables = {}

    script_file = open(filename, "r")
    lines = script_file.readlines()
    script_file.close()

    for line in lines:
        if line.find("##LDT") != -1:
            commands = line.split("##LDT")[1]
            variable_name = commands.split("=")[0].strip()
            variable_value = commands.split("=")[1].strip().strip('"')
            variables[variable_name] = variable_value

    return variables


def parse_script_dir(dryrun=False):
    """Parse script directory for run-scripts"""

    cfg = config.GfxConfig.create()
    script_dir = cfg.script_dir

    menu = desktop.Menu(dryrun)
    menu.directory_dir = cfg.directories_dir

    for script in os.listdir(script_dir):
        if script.endswith('.sh') and script.startswith('run_') and script.find('rviz-server') != -1:
            filename = os.path.join(script_dir, script)

            metadata = parse_script_metadata(filename)

            app_name = filename.split("_")[1]

            server_filename = os.path.basename(filename)

            slurm_client_filename = 'run_%s_rviz-slurm.sh' % app_name

            if "title" in metadata:
                slurm_client_descr = metadata["title"].title()
            else:
                slurm_client_descr = app_name.title()

            create_slurm_script(
                server_filename, slurm_client_filename, slurm_client_descr, metadata, dryrun)
            slurm_entry = create_desktop_entry(
                slurm_client_filename, slurm_client_descr, metadata, dryrun)

            if "category" in metadata:

                category = metadata["category"]

                if not category in menu.sub_menus:
                    menu.sub_menus[category] = []

                menu.sub_menus[category].append(
                    os.path.basename(slurm_entry.filename))

            else:
                menu.items.append(os.path.basename(slurm_entry.filename))

    menu.dest_filename = os.path.join(cfg.menu_dir, cfg.menu_filename)
    menu.write()


if __name__ == '__main__':

    # Show version information

    print(("LUNARC HPC Desktop - Wrapper script  - Version %s" % gfxconvert_version))
    print("Written by Jonas Lindemann (jonas.lindemann@lunarc.lu.se)")
    print("Copyright (C) 2018-2021 LUNARC, Lund University")

    cfg = config.GfxConfig.create()
    cfg.print_config()

    if cfg.is_ok:
        if len(sys.argv) > 1:
            parse_script_dir(dryrun=True)
        else:
            parse_script_dir(dryrun=False)

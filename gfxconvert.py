#!/bin/env python

import os, sys, getpass

from lhpcdt import config, desktop

# --- Version information

gfxconvert_version = "0.8"

# --- Fix search path for tool

tool_path = os.path.dirname(os.path.abspath(sys.argv[0]))
sys.path.append(tool_path)

# --- Functions


def create_direct_script(server_fname, direct_fname, descr):
    """Create script for direct vglconnect"""

    cfg = config.GfxConfig.create()

    client_script_filename = os.path.join(cfg.client_script_dir, direct_fname)
    server_script_filename = os.path.join(cfg.script_dir, server_fname)
    
    username = getpass.getuser()

    client_file = open(client_script_filename, "w")

    # vglconnect_template = '%s/vglconnect %s@%s %s/%s'

    client_file.write(cfg.vgl_connect_template % (cfg.vgl_bin, cfg.backend_node, cfg.script_dir, server_fname))
    client_file.close()

    os.chmod(client_script_filename, 0o755)


def create_slurm_script(server_fname, slurm_fname, descr, metadata = {}, dryrun = False):
    """Create script for running through SLURM"""

    cfg = config.GfxConfig.create()

    client_script_filename = os.path.join(cfg.client_script_dir, slurm_fname)
    server_script_filename = os.path.join(cfg.script_dir, server_fname)

    if dryrun:
        client_file = sys.stdout
        client_file.write("slurmscript = "+client_script_filename+"\n")
    else:
        client_file = open(client_script_filename, "w")

    part = cfg.default_part

    if "part" in metadata:
        part = metadata["part"]

    if "job" in metadata:
        job = metadata["job"]
        client_file.write(cfg.submit_only_slurm_template % (descr, part, cfg.default_account, job))
    else:
        client_file.write(cfg.simple_slurm_template % (descr, part, cfg.default_account, server_script_filename))

    if not dryrun:
        client_file.close()
        os.chmod(client_script_filename, 0o755)


def create_desktop_entry(script, descr, metadata = {}, dryrun = False):
    """Create desktop entry for script"""

    print(("Creating desktop entry '%s'" % script))
    desktop_filename = os.path.join(cfg.applications_dir, "%s.desktop" % descr)
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

    ##LDT category = "Post Processing"
    ##LDT title = "ParaView 5.4.1"
    ##LDT part = "snic"
    ##LDT job = "notebook"

    variables = {}

    script_file = open(filename, "r")
    lines = script_file.readlines()
    script_file.close()

    for line in lines:
        if line.find("##LDT")!=-1:
            commands = line.split("##LDT")[1]
            variable_name = commands.split("=")[0].strip()
            variable_value = commands.split("=")[1].strip().strip('"')
            variables[variable_name] = variable_value

    return variables

def parse_script_dir(dryrun = False):
    """Parse script directory for run-scripts"""

    cfg = config.GfxConfig.create()
    script_dir = cfg.script_dir

    menu = desktop.Menu(dryrun)
    menu.directory_dir = cfg.directories_dir

    for script in os.listdir(script_dir):
        if script.endswith('.sh') and script.startswith('run_') and script.find('rviz-server')!=-1:
            filename = os.path.join(script_dir, script)

            metadata = parse_script_metadata(filename)

            app_name = filename.split("_")[1]

            server_filename = os.path.basename(filename)

            direct_client_filename = 'run_%s_rviz-direct.sh' % app_name
            direct_client_descr = app_name.title() + ' (Direct)'
            slurm_client_filename = 'run_%s_rviz-slurm.sh' % app_name
            slurm_client_descr = app_name.title()

            create_slurm_script(server_filename, slurm_client_filename, slurm_client_descr, metadata, dryrun)
            slurm_entry = create_desktop_entry(slurm_client_filename, slurm_client_descr, metadata, dryrun)

            if cfg.direct_scripts:
                create_direct_script(server_filename, direct_client_filename, direct_client_descr)
                direct_entry = create_desktop_entry(direct_client_filename, direct_client_descr)

            if cfg.direct_scripts:
                menu.items.append(os.path.basename(direct_entry.filename))

            if "category" in metadata:

                category = metadata["category"]

                if not category in menu.sub_menus:
                    menu.sub_menus[category] = []

                menu.sub_menus[category].append(os.path.basename(slurm_entry.filename))

            else:
                menu.items.append(os.path.basename(slurm_entry.filename))

    menu.dest_filename = os.path.join(cfg.menu_dir, cfg.menu_filename)
    menu.write()


if __name__ == '__main__':

    # Show version information

    print(("LUNARC HPC Desktop - Wrapper script  - Version %s" % gfxconvert_version))
    print("Written by Jonas Lindemann (jonas.lindemann@lunarc.lu.se)")
    print("Copyright (C) 2018-2020 LUNARC, Lund University")

    cfg = config.GfxConfig.create()
    cfg.print_config()

    if cfg.is_ok:
        if len(sys.argv)>1:
            parse_script_dir(dryrun = True)
        else:
            parse_script_dir(dryrun = False)

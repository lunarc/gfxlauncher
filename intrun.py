#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
import sys

def main():
    # Create the argument parser
    parser = argparse.ArgumentParser(description='Description of your script')

    # Add arguments
    parser.add_argument('-s', '--silent', help='Run without asking for job parameters.', action='store_true')
    parser.add_argument('-d', '--dbus', help='Run command with dbus support.', action='store_true')
    parser.add_argument('-n', '--tasks-per-node', help='Number of tasks per node.', type=int, default=1)
    parser.add_argument('-c', '--cmd', help='Command to run.', type=str)

    # Parse the arguments
    args = parser.parse_args()

    # Access the values of the arguments
    silent = args.silent
    dbus = args.dbus
    tasks_per_node = int(args.tasks_per_node)

    old_path=os.environ['PATH']

    if 'PYTHONPATH' in os.environ:
        old_python_path=os.environ['PYTHONPATH']
    else:
        old_python_path=''

    old_ld_library_path=os.environ['LD_LIBRARY_PATH']

    # Set the new values
    os.environ['PATH'] = '/bin:' + old_path
    os.environ['PYTHONPATH'] = '/usr/lib64/python3.9/site-packages'
    os.environ['LD_LIBRARY_PATH'] = '/usr/lib64/python3.9/site-packages/PyQt5'

    # Get the current directory

    curr_dir = os.getcwd()

    if dbus:
        dbus_launch_cmd = 'dbus-launch --exit-with-session '
        dbus_cleanup_cmd = 'killall dbus-launch'
    else:
        dbus_launch_cmd = ''
        dbus_cleanup_cmd = ''

    full_path_bin = os.path.realpath(args.cmd)
    full_path = os.path.dirname(full_path_bin)
    exe_name = os.path.basename(full_path_bin)

    full_path_template = f"""export PATH={old_path}
export LD_LIBRARY_PATH={old_ld_library_path}
export PYTHONPATH={old_python_path}
cd {full_path}
{dbus_launch_cmd}./{exe_name}
{dbus_cleanup_cmd}"""

    rel_path_template = f"""export PATH={old_path}
export LD_LIBRARY_PATH={old_ld_library_path}
export PYTHONPATH={old_python_path}
cd {full_path}
{dbus_launch_cmd}{exe_name}
{dbus_cleanup_cmd}"""

    if os.path.exists(full_path_bin):
        print("full path:")
        print(full_path_template)
    else:
        print("relative path:")
        print(rel_path_template)


if __name__ == '__main__':
    main()
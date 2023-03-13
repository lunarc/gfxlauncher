#!/usr/bin/env python

import os, sys

from . import integration

class RunScript:
    def __init__(self, filename=""):
        self.__filename = filename
        self.__parse_metadata()

    def __parse_metadata(self):
        """Parse run-script for metadata"""

        # LDT category = "Post Processing"
        # LDT title = "ParaView 5.4.1"
        # LDT part = "snic"
        # LDT job = "notebook"
        # LDT group = "ondemand"

        self.__variables = {}

        with open(self.__filename, "r") as script_file:
            lines = script_file.readlines()

        for line in lines:
            if line.find("##LDT") != -1:
                commands = line.split("##LDT")[1]
                variable_name = commands.split("=")[0].strip()
                variable_value = commands.split("=")[1].strip().strip('"')
                self.__variables[variable_name] = variable_value

    @property
    def variables(self):
        return self.__variables

    @property
    def filename(self):
        return self.__filename

class RunScripts:
    def __init__(self, script_dir=""):
        self.__script_dir = script_dir
        self.__script_dict = {}


    def parse(self, dryrun=False, no_launcher=False):

        """Parse script directory for run-scripts"""

        #cfg = config.GfxConfig.create()
        #script_dir = cfg.script_dir
        script_dir = self.__script_dir

        self.__script_dict = {}

        for script in os.listdir(script_dir):
            if script.endswith('.sh') and script.startswith('run_') and script.find('rviz-server') != -1:
                print("Found:", script)
                filename = os.path.join(script_dir, script)

                run_script = RunScript(filename)

                metadata = run_script.variables

                app_name = filename.split("_")[-2]

                server_filename = os.path.basename(filename)

                if no_launcher:
                    slurm_client_filename = 'run_%s_rviz-direct.sh' % app_name
                else:
                    slurm_client_filename = 'run_%s_rviz-slurm.sh' % app_name

                if "title" in metadata:
                    slurm_client_descr = metadata["title"].title()
                else:
                    slurm_client_descr = app_name.title()

                category = "general"

                if "category" in metadata:
                    category = metadata["category"]

                if not category in self.__script_dict:
                    self.__script_dict[category] = []

                self.__script_dict[category].append(run_script)


    @property
    def database(self):
        return self.__script_dict




if __name__ == "__main__":

    run_scripts = RunScripts("/home/lindemann/Development/gfxlauncher/tests/scripts")
    run_scripts.parse()

    script_db = run_scripts.database


    

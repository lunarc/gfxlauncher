#!/usr/bin/env python

import os, sys, datetime, logging

from . import integration


class RunScript:
    def __init__(self, filename=""):
        self.__filename = filename
        self.__launch_cmd = ""
        self.__no_launcher = False
        self.__launcher = "gfxlaunch"
        self.__changed = None
        self.__parse_metadata()
        self.__parse_failed = False
        self.__icon = "system-icon"

    def __parse_metadata(self):
        """Parse run-script for metadata"""

        ##LDT category = "Post Processing"
        ##LDT title = "ParaView 5.4.1"
        ##LDT part = "snic"
        ##LDT job = "notebook"
        ##LDT group = "ondemand"
        ##LDT vgl = "yes"
        ##LDT part_disable = "yes"
        ##LDT feature_disable = "yes"
        ##LDT direct_launch = "yes"
        ##LDT icon = "system-icon"

        self.__variables = {}

        try:
            with open(self.__filename, "r") as script_file:
                lines = script_file.readlines()
        except PermissionError:
            self.__parse_failed = True
            return

        self.__changed = os.stat(self.__filename).st_mtime

        for line in lines:
            if line.find("##LDT") != -1:
                commands = line.split("##LDT")[1]
                variable_name = commands.split("=")[0].strip()
                variable_value = commands.split("=")[1].strip().strip('"')
                self.__variables[variable_name] = variable_value

        vgl = "no"

        cmd_options = ""

        if "vgl" in self.__variables:
            vgl = self.__variables["vgl"]

        if vgl == "yes":
            cmd_options += " --vgl"

        if "part" in self.__variables:
            cmd_options += "--partition %s" % self.__variables["part"]

        if "group" in self.__variables:
            cmd_options += " --group %s" % self.__variables["group"]

        if "title" in self.__variables:
            cmd_options += ' --title "%s"' % self.__variables["title"]

        if "restrict" in self.__variables:
            cmd_options += ' --restrict "%s"' % self.__variables["restrict"]

        if "job" in self.__variables:
            cmd_options += ' --job %s' % self.__variables["job"]

        if "part_disable" in self.__variables:
            if self.__variables["part_disable"] == "yes":
                cmd_options += ' --part-disable'

        if "feature_disable" in self.__variables:
            if self.__variables["feature_disable"] == "yes":
                cmd_options += ' --feature-disable'

        if "no_launcher" in self.__variables:
            if self.__variables["no_launcher"] == "yes":
                self.__no_launcher = True
            else:
                self.__no_launcher = False

        if "icon" in self.__variables:
            self.__icon = self.__variables["icon"]

        cmd_options += " --cmd %s" % self.filename

        if self.__no_launcher:
            self.__launch_cmd = self.filename
        else:
            self.__launch_cmd = self.__launcher + " " + cmd_options.strip()


    @property
    def variables(self):
        return self.__variables

    @property
    def filename(self):
        return self.__filename

    @property
    def launch_cmd(self):
        self.__parse_metadata()
        return self.__launch_cmd

    @property
    def launcher(self):
        return self.__launcher

    @launcher.setter
    def launcher(self, value):
        self.__launcher = value
        self.__parse_metadata()

    @property
    def changed(self):
        return self.__changed

    @property
    def parse_failed(self):
        return self.__parse_failed
    
    @property
    def no_launcher(self):
        return self.__no_launcher
    
    @property
    def icon(self):
        return self.__icon

class RunScripts:
    def __init__(self, script_dir=""):
        self.__script_dir = script_dir
        self.__launcher = "gfxlaunch"
        self.__script_dict = {}


    def parse(self, dryrun=False):

        """Parse script directory for run-scripts"""

        #cfg = config.GfxConfig.create()
        #script_dir = cfg.script_dir
        script_dir = self.__script_dir

        logging.debug("Parsing script directory: %s" % script_dir)

        self.__script_dict = {}

        for script in os.listdir(script_dir):
            if script.endswith('.sh') != -1:
                #print("Found:", script)
                filename = os.path.join(script_dir, script)

                if os.path.isdir(filename):
                    continue

                run_script = RunScript(filename)
                run_script.launcher = self.__launcher

                if run_script.parse_failed:
                    continue

                metadata = run_script.variables

                app_name = filename.split(".sh")[0]

                server_filename = os.path.basename(filename)

                use_launcher = not run_script.no_launcher

                if run_script.no_launcher:
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

    def __update(self):

        for category, scripts in self.__script_dict.items():
            for script in scripts:
                script.launcher = self.__launcher

    @property
    def database(self):
        return self.__script_dict

    @property
    def launcher(self):
        return self.__launcher

    @launcher.setter
    def launcher(self, value):
        self.__launcher = value
        self.__update()




if __name__ == "__main__":

    run_scripts = RunScripts("/home/lindemann/Development/gfxlauncher/scripts")
    run_scripts.parse()

    script_db = run_scripts.database




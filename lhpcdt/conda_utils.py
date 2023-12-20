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
# This program is distributed in the  hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import subprocess, getpass, os, json

class CondaInstall:
    def __init__(self):
        self.user_name = getpass.getuser()
        self.home_dir = os.path.expanduser("~")
        self.conda_dir = os.path.join(self.home_dir, ".conda")
        self.conda_envs_dir = os.path.join(self.conda_dir, "envs")
        self.conda_envs = {}
        self.on_query_env = None
        self.on_query_package = None
        self.on_query_completed = None
        self.query_packages = False

    def query(self):
        self.__query_conda_envs()

    def have_conda_dir(self):
        return os.path.exists(self.conda_dir)
    
    def have_conda_envs_dir(self):
        return os.path.exists(self.conda_envs_dir)

    def __query_conda_envs(self):
        if self.have_conda_envs_dir():

            print("Parsing environments...")

            file_entries = os.listdir(self.conda_envs_dir)

            self.conda_envs.clear()

            for entry in file_entries:
                env_dir = os.path.join(self.conda_envs_dir, entry)
                if os.path.isdir(env_dir):

                    if self.on_query_env is not None:
                        self.on_query_env(entry)

                    self.conda_envs[entry] = {"env_dir":env_dir, "packages":{}}

                    if self.query_packages:

                        meta_dir = os.path.join(env_dir, "conda-meta")

                        package_entries = os.listdir(meta_dir)

                        for package_filename in package_entries:

                            if self.on_query_package is not None:
                                self.on_query_package(package_filename)

                            try: 
                                package_dict = json.load(open(os.path.join(meta_dir, package_filename), "r"))
                                self.conda_envs[entry]["packages"][package_dict["name"]] = package_dict
                            except json.decoder.JSONDecodeError:
                                print("error")

            if self.on_query_completed is not None:
                self.on_query_completed()


if __name__ == "__main__":

    conda = CondaInstall()
    print(conda.conda_envs["compute-env"]["packages"]["numpy"]["version"])
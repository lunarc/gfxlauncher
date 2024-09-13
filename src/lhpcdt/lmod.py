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
LMOD JSON module parser

This module provides classes for parsing and searching the LMOD module tree.
"""

import os
import sys
import subprocess
import json

# Generate modules.json with:
# $LMOD_DIR/spider -o jsonSoftwarePage $MODULEPATH > modules.json

class LmodDB(object):
    def __init__(self, filename="modules.json"):
        self._filename = filename
        with open(self._filename, "r") as f:
            self.modules = json.load(f)

        self.module_dict = {}
        self.module_version_dict = {}

        for module in self.modules:
            module_name = module["package"]
            self.module_dict[module_name] = module
            for version in module["versions"]:
                if "versionName" in version:
                    module_version = version["versionName"]

                    if not module_name in self.module_version_dict:
                        self.module_version_dict[module_name] = {}
                    if not module_version in self.module_version_dict[module_name]:
                        self.module_version_dict[module_name][module_version] = []

                    self.module_version_dict[module["package"]][module_version].append(version)


    def find_versions(self, module):
        versions = []
        for version in self.module_version_dict[module].keys():
            versions.append(version)
        return versions

    def find_parents(self, module, version):
        module_parents = []
        if module in self.module_version_dict:
            if version in self.module_version_dict[module]:
                for parents in self.module_version_dict[module][version]:
                    if "parent" in parents:
                        for parent in parents["parent"]:
                            module_parents.append(parent)
                return module_parents
        
        return []

    def find_version_info(self, module):
        versions = []
        for version in self.module_dict[module]["versions"]:
            versions.append(version)
        return versions

    def find_modules(self, name=""):
        module_names = []

        for module in self.modules:
            if name=="":
                module_names.append(module["package"])
            else: 
                if name in module["package"]:
                    module_names.append(module["package"])
                elif name.upper() in module["package"]:
                    module_names.append(module["package"])
                elif name.lower() in module["package"]:
                    module_names.append(module["package"])

        return module_names

    def find_description(self, module):
        try:
            return self.module_dict[module]["description"]
        except:
            return ""

    def find_default_version(self, module):
        try:
            return self.module_dict[module]["defaultVersionName"]
        except:
            return ""


if __name__ == "__main__":

    lmod = LmodDB()
    versions = lmod.find_versions("GROMACS")
    print(versions)

    module_names = lmod.find_modules()
    print(module_names)

    #lmod = LmodDB()
    #versions = lmod.find_versions("Anaconda3")
    #print(versions)

    #dep_mods = lmod.find_deps("Anaconda3", versions[1])
    #print(dep_mods)

    #default_version = lmod.find_default_version("Anaconda3")
    #print(default_version)
    
    #lmod.parse_deps()

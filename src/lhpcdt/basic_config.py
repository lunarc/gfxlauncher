#!/usr/bin/env python
#
# LUNARC HPC Desktop On-Demand graphical launch tool
# Copyright (C) 2017-2024 LUNARC, Lund University
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

class BasicConfig:
    def __init__(self):

        self.script_dir = "/sw/pkg/ondemand-dt/run"
        self.install_dir = "/sw/pkg/gfxlauncher"
        self.help_url = "https://lunarc-documentation.readthedocs.io/en/latest/getting_started/gfxlauncher/"
        self.browser_cmd = "firefox"


        self.features = {"mem256gb":"256 GB Memory node"}

        self.partitions = {
            "gpua40":"AMD/NVIDIA A40 48c 24h",
            "gpua40i":"Intel/NVIDIA A40 32c 48h",
            "test":"Test partition"
        }            
        self.groups = {
            "ondemand":["gpua40", "gpua40i"], 
            "all":["test"]
        }

        self.default_tasks = 1
        self.default_memory = 5300
        self.default_exclusive = False
        self.default_part = "gpua40"
        self.default_account = ""

        self.use_sacctmgr = True

        self.menu_prefix = "Applications - "
        self.desktop_entry_prefix = "gfx-"

        self.vgl_bin = "/usr/bin/vglconnect"
        self.vgl_path = "/usr/bin"

        self.notebook_module = "Anaconda3"
        self.jupyterlab_module = "Anaconda3"

        self.__config = ""

    def clear(self):
        self.__config = ""

    def section(self, name):
        self.__config += f"[{name}]\n"

    def new_line(self):
        self.__config += "\n"

    def var(self, name, value):
        self.__config += f"{name} = {value}\n"

    def str_var(self, name, value):
        self.__config += f"{name} = \"{value}\"\n"

    def list_var(self, f, name, value):

        group_str = ", ".join([f(x) for x in value])
        self.__config += f"{name} = {group_str}\n"

    def create_config(self):
        self.section("general")
        self.new_line()
        self.var("script_dir", self.script_dir)
        self.var("install_dir", self.install_dir)
        self.str_var("help_url", self.help_url)
        self.str_var("browser_cmd", self.browser_cmd)
        self.new_line()

        self.section("slurm")
        self.new_line()

        for k, v in self.features.items():
            self.str_var(k, v)
        self.new_line()

        for k, v in self.partitions.items():
            self.str_var(k, v)
        self.new_line()

        for k, v in self.groups.items():
            self.list_var(lambda x: f"{x}", k, v)
        self.new_line()

        self.var("default_part", self.default_part)
        self.str_var("default_account", self.default_account)
        self.var("default_tasks", self.default_tasks)
        self.var("default_memory", self.default_memory)
        self.var("default_exclusive", self.default_exclusive)
        self.new_line()
        self.var("use_sacctmgr", self.use_sacctmgr)   
        self.new_line()     

        self.section("menus")
        self.new_line()
        self.str_var("menu_prefix", self.menu_prefix)
        self.str_var("desktop_entry_prefix", self.desktop_entry_prefix)
        self.new_line()

        self.section("vgl")
        self.new_line()
        self.str_var("vgl_bin", self.vgl_bin)
        self.str_var("vgl_path", self.vgl_path)
        self.new_line()

        self.section("jupyter")
        self.new_line()
        self.str_var("notebook_module", self.notebook_module)
        self.str_var("jupyterlab_module", self.jupyterlab_module)



    def __str__(self):
        self.create_config()
        return self.__config
    

if __name__ == "__main__":

    config = BasicConfig()


    print(config)


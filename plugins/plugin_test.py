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

import os, sys

import importlib

sys.path.append("..")

from lhpcdt import *

def load_job_plugin(filename):
    spec = importlib.util.spec_from_file_location("module.name", filename)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.JobPlugin()

if __name__ == "__main__":

    j1 = load_job_plugin("./JupyterLabJobPlugin.py")
    j2 = load_job_plugin("./JupyterNotebookJobPlugin.py")

    print(j1.plugin_name+" - "+j1.plugin_descr)
    print(j2.plugin_name+" - "+j2.plugin_descr)


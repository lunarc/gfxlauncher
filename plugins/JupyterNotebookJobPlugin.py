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
Jobs module

This module provides classes for supported job types.
"""


import os
import sys
import subprocess
import time
from subprocess import Popen, PIPE, STDOUT

from lhpcdt.jobs import JobPluginBase

class JobPlugin(JobPluginBase):
    """Jupyter notebook job"""

    def __init__(self, account="", partition="", time="00:30:00", notebook_module="Anaconda3"):
        super().__init__(account, partition, time)
        self.plugin_name = "JupyterNotebook"
        self.plugin_descr = "JupyterNotebook job plugin."

        self.notebook_url = ""
        self.process_output = True
        self.processing_description = "Waiting for notebook instance to start."
        self.notebook_module = notebook_module

        self.add_module(self.notebook_module)

        self.add_custom_script("unset XDG_RUNTIME_DIR")
        self.add_custom_script('jupyter-notebook --no-browser --ip=$HOSTNAME')
        self.add_custom_script("module list")
        self.add_custom_script("which python")

    def on_notebook_url_found(self, url):
        """Event method called when notebook has been found"""
        print("Notebook found: "+url)

    def do_process_output(self, output_lines):
        """Process job output"""

        Job.do_process_output(self, output_lines)

        if self.process_output:
            for line in output_lines:
                if line.find("?token=") != -1:
                    if line.find("127.0.0.1") == -1:
                        url = line[line.find("http:"):].strip()
                        self.notebook_url = url
                        self.process_output = False
                        self.on_notebook_url_found(self.notebook_url)



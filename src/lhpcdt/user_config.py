#!/bin/env python
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

import os

class UserConfig:
    def __init__(self):
        self.__job_output_dir = ".lhpc"
        self.__job_output_template = "lhpcdt-%j.out"

    def setup(self):
        job_dir_path = os.path.join(os.path.expanduser("~"), self.__job_output_dir)
        if not os.path.exists(job_dir_path):
            print("Creating job output directory: " + job_dir_path)
            os.makedirs(job_dir_path)
        else:
            print("Job output directory already exists: " + job_dir_path)

        print("Job output template: " + self.__job_output_template)
        print("Job output file path: " + self.job_output_file_path)

    @property
    def job_output_dir(self):
        return self.__job_output_dir

    @job_output_dir.setter
    def job_output_dir(self, value):
        self.__job_output_dir = value

    @property
    def job_output_template(self):
        return self.__job_output_template
    
    @job_output_template.setter
    def job_output_template(self, value):
        self.__job_output_template = value

    @property
    def job_output_file_path(self):
        return os.path.join(os.path.expanduser("~"), self.__job_output_dir, self.__job_output_template)
    
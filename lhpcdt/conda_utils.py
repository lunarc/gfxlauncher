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

import subprocess

def find_conda_envs():
    result = subprocess.run(["conda", "env", "list"], capture_output=True)

    env_list = []

    lines = str(result.stdout).split("\\n")
    for e in lines:
        if not '#' in e:
            items = e.split()
            if len(items)>1:
                env_list.append(items[0])

    return env_list


if __name__ == "__main__":

    env_list = find_conda_envs()
    print(env_list)




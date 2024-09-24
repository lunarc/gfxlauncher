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


gfxlauncher_template = """[general]
script_dir = /sw/pkg/ondemand-dt/run
install_dir = /sw/pkg/gfxlauncher
help_url = "https://lunarc-documentation.readthedocs.io/en/latest/getting_started/gfxlauncher/"
browser_command = firefox

[slurm]
default_part = gpua40
default_account = lu-test

feature_mem96gb = "96 GB Memory node"
feature_mem64gb = "64 GB Memory node"
feature_mem128gb = "128 GB Memory node"
feature_mem192gb = "192 GB Memory node"
feature_mem384gb = "384 GB Memory node"
feature_mem768gb = "768 GB Memory node"
feature_mem256gb = "256 GB Memory node"
feature_mem512GB = "512 GB Memory node"
feature_gpua40 = "NVIDIA A40 GPU"
feature_milan = "AMD Milan CPU"
feature_gpu3k20 = "3 x NVIDIA K20 GPU (128GB RAM)"
#feature_gpu2k20 = "2 x NVIDIA K20 GPU"
feature_gpu8k20 = "8 x NVIDIA K20 GPU (128GB RAM)"
#feature_gpu4k20 = "4 x NVIDIA K20 GPU"
feature_kepler = "2 x NVIDIA K80 GPU"
feature_ampere = "2 x NVIDIA A100 GPU"
feature_ignore = "milan,rack-,rack_,bc,haswell,cascade,enc,jobtmp,skylake,ampere,kepler,sandy"

part_lu48 = "AMD 48 cores"
part_lu32 = "Intel 32 cores"
part_gpua40 = "AMD/NVIDIA A40 48c 24h"
part_gpua100 = "AMD/NVIDIA A100 48 cores"
part_gpua40i = "Intel/NVIDIA A40 32c 48h"
part_ignore = "lunarc,hep"

group_ondemand = gpua40, gpua40i
group_ondemandamd = gpua40
group_ondemandintel = gpua40i
group_develop = gpua40i
group_metashape184 = lvis2
group_cpu = lu48
group_gpu = gpua100,gpua40
group_win = win
group_mathem = lu48, lu32
group_all = lu48,lu32,gpua100,gpua40
group_cpuintel = lu32
group_cpuamd = lu48
group_cpuall = lu48, lu32

group_ondemand_tasks = 4
group_ondemand_memory = -1
group_ondemand_exclusive = no

group_mathem_tasks = 4
group_cpuall_tasks = 1

default_tasks = 1
default_memory = 5300
default_exclusive = no

use_sacctmgr = yes

[menus]
menu_prefix = "Applications - "
desktop_entry_prefix = "gfx-"

[vgl]
vgl_bin = /usr/bin/vglconnect 
vgl_path = /usr/bin
backend_node = gfx0
vglconnect_template = %s/vglconnect %s %s/%s

[jupyter]
notebook_module = Anaconda3
jupyterlab_module = Anaconda3

[xfreerdp]
xfreerdp_path = /sw/pkg/freerdp/2.0.0-rc4/bin
xfreerdp_cmdline = %s /v:%s /u:$USER /d:ad.lunarc /sec:tls /cert-ignore /audio-mode:1 /gfx +gfx-progressive -bitmap-cache -offscreen-cache -glyph-cache +clipboard /size:1280x1024 /dynamic-resolution /t:"LUNARC HPC Desktop Windows 10 (NVIDA V100)"
"""

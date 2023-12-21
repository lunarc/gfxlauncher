Configuring the launcher
========================

GfxLauncher and the gfxconvert script is configured in the **/etc/gfxlauncher.conf** configuration file. This file controls all the default settings and slurm templates used.

An example configuration file is shown below:

.. code-block:: ini

    [general]
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
    group_develop = gpua40i
    group_metashape184 = lvis2
    group_cpu = lu48
    group_gpu = gpua100,gpua40
    group_win = win
    group_all = lu48,lu32,gpua100,gpua40

    group_ondemand_tasks = 4
    group_ondemand_memory = -1
    group_ondemand_exclusive = no

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


General section - [general]
---------------------------

The general section mainly contains information on where the **gfxconvert** tool can find the server scripts used for starting the applications on the backend infrastructure, **install_dir**. The server scripts also contains meta data for menu generation. The **script_dir** tells **gfxconvert** where the run-scripts should be generated.

SLURM section - [slurm]
-----------------------

This section contain settings related to SLURM.

+-----------------+--------------------------------------------------------------------------------------------+
| Variable        | Description                                                                                |
+-----------------+--------------------------------------------------------------------------------------------+
| default_part    | If no partition is given on the gfxlaunch command line this is the default partition used. |
+-----------------+--------------------------------------------------------------------------------------------+
| default_account | If no account information is given this is the default account used.                       |
+-----------------+--------------------------------------------------------------------------------------------+
| use_sacctmgr    | If set to yes (default) gfxlaunch will use project information from the sacctmgr command   |
|                 | instead of grantfiles. This is the default.                                                |
+-----------------+--------------------------------------------------------------------------------------------+

.. note:: grantfile and grantfile_base are specific to SNIC/LUNARC HPC resources and can be disabled.

Feature descriptions
~~~~~~~~~~~~~~~~~~~~

It is also possible to give descriptive names of SLURM features, which will be displayed in the user interface combobox. Feature descriptions are given by variables prefixed with **feature_** and the name of the feature in SLURM. An feature variable name for the SLURM feature **gpu4k20** will then be **feature_gpu4k20**. The description is a string assigned to the configuration variable, enclosed with "". An example feature variable assignment is shown below:

.. code-block:: ini

    feature_gpu4k20 = "4 x NVIDIA K20 GPU"
    
Ignoring features
~~~~~~~~~~~~~~~~~

Not all features should be automatically be exposed to the users. To hide these the **feature_ignore** configuration variable can be used to list features that shoudln't be considered in the user interface. The following example shows this variable used:

.. code-block:: ini

    feature_ignore = "rack-,rack_,bc,haswell,cascade,enc,jobtmp,skylake,ampere,kepler,sandy"
    
Partition descriptions
~~~~~~~~~~~~~~~~~~~~~~

To make the resource selection more intuitive it is also possible to give the SLURM partitions more easy to understand descriptions. This is done by providing special partition variables prefixed with **part_** and the name of the partition in SLURM. A partition variable name for the SLURM partition **gpua100** would then be **part_gpua100**. The description is a string assigned to the configuration variable, enclosed with "". An example partition variable assignment is shonw below:

.. code-block:: ini

    part_gpua100 = "AMD/NVIDIA A100 48 cores"

Ignoring partitions
~~~~~~~~~~~~~~~~~~~

Just as with features, not all partitions should be automatically be exposed to the users. To hide these the **part_ignore** configuration variable can be used to list features that shoudln't be considered in the user interface. The following example shows this variable used:

.. code-block:: ini

    part_ignore = "lunarc,hep"
    
Grouping partitions
~~~~~~~~~~~~~~~~~~~

Certain applications will require certain partitions when running. To limit the choices in the user interface it is possible to define groups of partitions, this can be done by defining variables with the **group_**-prefix followed by the groupname. For each group a number of partitions can be specified. Examples of group definitions are shown below:

.. code-block:: ini

    group_ondemand = lvis,lvis2
    group_cpu = lu,lu2
    group_gpu = gpuk20,gpua100
    group_win = win
    
The partition groups can be used the **gfxlaunch** switch --group to only display the partitions in the specified group.


Menu section - [menu]
---------------------

Directories and files for the **gfxconvert** menu generation is given in this section. The following variables are used by **gfxconvert**.

+----------------------------+-------------------------------------------------------------------------------+
| Variable                   | Description                                                                   |
+----------------------------+-------------------------------------------------------------------------------+
| menu_prefix                | Prefix added to the menu descriptions to identify menus generated by gfxmenu. |
+----------------------------+-------------------------------------------------------------------------------+
| directdesktop_entry_prefix | Prefix added to desktop-shortcut files generated by gfxmenu.                  |
+----------------------------+-------------------------------------------------------------------------------+

VirtualGL section - [vgl]
-------------------------

This section is used by **gfxlaunch** to configure where the binaries for VirtualGL can be found. The following variables can be configured:

+----------------------+-----------------------------------------------------------------------------+
| Variable             | Description                                                                 |
+----------------------+-----------------------------------------------------------------------------+
| vgl_path             | Path for VirtualGL executables (for example: /usr/bin)                      |
+----------------------+-----------------------------------------------------------------------------+
| vgl_connect_template | Command to execute vglconnect. Should be %s/vglconnect %s %s/%s by default. |
+----------------------+-----------------------------------------------------------------------------+

XFreeRDP section - [xfreerdp]
-----------------------------

This section is used by **gfxlaunch** to configure where the binaries for XFreeRDP can be found. The following variables can be configured:

+----------------------+-----------------------------------------------------------------------------+
| Variable             | Description                                                                 |
+----------------------+-----------------------------------------------------------------------------+
| xfreerdp_path        | Path for XFreeRDP executables                                               |
+----------------------+-----------------------------------------------------------------------------+

Jupyter related section - [jupyter]
-----------------------------------

+-----------------------+-----------------------------------------------------------------------------+
| Variable              | Description                                                                 |
+-----------------------+-----------------------------------------------------------------------------+
| notebook_module       | Module loaded for Jupyter Notebook jobs                                     |
+-----------------------+-----------------------------------------------------------------------------+
| jupyterlab_module     | Module loaded for Jupyter Lab jobs                                          |
+-----------------------+-----------------------------------------------------------------------------+
| jupyter_use_localhost | If set to yes. gfxlaunch will start the notebook on localhost of the node   |
|                       | and connect using a ssh tunnel to the notbook. If set to no gfxlaunch will  |
|                       | connect directly to to the notebook running on the node.                    |
+-----------------------+-----------------------------------------------------------------------------+


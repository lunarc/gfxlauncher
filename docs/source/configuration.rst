Configuration
=============

GfxLauncher and the gfxconvert script is configured in the **/etc/gfxlauncher.conf** configuration file. This file controls all the default settings and slurm templates used.

An example configuration file is shown below:

.. code-block:: ini

    [general]
    script_dir = /sw/pkg/rviz/sbin/run
    client_script_dir = /sw/pkg/rviz/sbin/run/launcher

    [slurm]
    default_part = lvis
    default_account = lvis-test
    grantfile = /sw/pkg/slurm/local/grantfile.lvis
    grantfile_base = /sw/pkg/slurm/local/grantfile.%s

    simple_launch_template = gfxlaunch --vgl --title "%s" --partition %s --account %s --exclusive --tasks-per-node=-1 --cmd %s --simplified
    
    feature_gpu4k20 = "4 x NVIDIA K20 GPU"
    feature_gpu8k20 = "8 x NVIDIA K20 GPU"
    feature_mem96gb = "96 GB Memory node"
    feature_mem64gb = "64 GB Memory node"
    feature_gpu2k20 = "2 x NVIDIA K20 GPU"

    [menus]
    applications_dir = /sw/pkg/rviz/share/applications
    directories_dir = /sw/pkg/rviz/share/desktop-directories
    menu_dir = /sw/pkg/rviz/etc/xdg/menus/applications-merged
    menu_filename = Lunarc-On-Demand.menu

    [vgl]
    vgl_path = /sw/pkg/rviz/vgl/bin/latest
    vglconnect_template = %s/vglconnect %s %s/%s

    [xfreerdp]
    xfreerdp_path = /sw/pkg/...

    [jupyter]
    notebook_module = Anaconda3
    jupyterlab_module = Anaconda3

General configuration section - [general]
-----------------------------------------

The general section mainly contains information on where the **gfxconvert** tool can find the server scripts used for starting the applications on the backend infrastructure, **script_dir**. The server scripts also contains meta data for menu generation. The **client_script_dir** tells **gfxconvert** where the launch-scripts should be generated. Created menu items will point to this location.

SLURM configuration section - [slurm]
-------------------------------------

This section contain settings related to SLURM.

+-----------------+--------------------------------------------------------------------------------------------+
| Variable        | Description                                                                                |
+-----------------+--------------------------------------------------------------------------------------------+
| default_part    | If no partition is given on the gfxlaunch command line this is the default partition used. |
+-----------------+--------------------------------------------------------------------------------------------+
| default_account | If no account information is given this is the default account used.                       |
+-----------------+--------------------------------------------------------------------------------------------+
| grantfile       | This is the grantfile used to find user accounts.                                          |
+-----------------+--------------------------------------------------------------------------------------------+
| grantfile_base  | This is the grantfile template used for a specific partition.                              |
+-----------------+--------------------------------------------------------------------------------------------+

The template command line for calling the **gfxlaunch**-command is given by the **simple_slurm_template** variable. An example of this variable is shown below:

.. code-block:: bash

    simple_slurm_template = gfxlaunch --vgl --title "%s" --partition %s --account %s --exclusive --tasks-per-node=-1 --cmd %s --simplified

The usage of **gfxlaunch** is described in a separate section.

It is also possible to give descriptive names of SLURM features, which will be displayed in the user interface combobox. Feature descriptions are given by variables prefixed with **feature_** and the name of the feature in SLURM. An feature variable name for the SLURM feature **gpu4k20** will then be **feature_gpu4k20**. The description is a string assigned to the configuration variable, enclosed with "". An example feature variable assignment is shown below:

.. code-block:: ini

    feature_gpu4k20 = "4 x NVIDIA K20 GPU"

Menu configuration section - [menu]
-----------------------------------

Directories and files for the **gfxconvert** menu generation is given in this section. The following variables are used by **gfxconvert**.

+------------------+-----------------------------------------------------------------------------+
| Variable         | Description                                                                 |
+------------------+-----------------------------------------------------------------------------+
| applications_dir | gfxconvert will create the .desktop entries for the client scripts here.    |
+------------------+-----------------------------------------------------------------------------+
| directories_dir  | gfxconvert will create .directory entries here for the sub categories here. |
+------------------+-----------------------------------------------------------------------------+
| menu_dir         | gfxconvert will create the final .menu file here.                           |
+------------------+-----------------------------------------------------------------------------+
| menu_filename    | This is the name that will be used for the final .menu file.                |
+------------------+-----------------------------------------------------------------------------+

VirtualGL configuration - [vgl]
-------------------------------

This section is used by **gfxlaunch** to configure where the binaries for VirtualGL can be found. The following variables can be configured:

+----------------------+-----------------------------------------------------------------------------+
| Variable             | Description                                                                 |
+----------------------+-----------------------------------------------------------------------------+
| vgl_path             | Path for VirtualGL executables                                              |
+----------------------+-----------------------------------------------------------------------------+
| vgl_connect_template | Command to execute vglconnect. Should be %s/vglconnect %s %s/%s by default. |
+----------------------+-----------------------------------------------------------------------------+

XFreeRDP configuration - [xfreerdp]
-----------------------------------

This section is used by **gfxlaunch** to configure where the binaries for XFreeRDP can be found. The following variables can be configured:

+----------------------+-----------------------------------------------------------------------------+
| Variable             | Description                                                                 |
+----------------------+-----------------------------------------------------------------------------+
| xfreerdp_path        | Path for XFreeRDP executables                                               |
+----------------------+-----------------------------------------------------------------------------+

Jupyter related settings - [jupyter]
------------------------------------

+----------------------+-----------------------------------------------------------------------------+
| Variable             | Description                                                                 |
+----------------------+-----------------------------------------------------------------------------+
| notebook_module      | Module loaded for Jupyter Notebook jobs                                     |
+----------------------+-----------------------------------------------------------------------------+
| jupyterlab_module    | Module loaded for Jupyter Lab jobs                                          |
+----------------------+-----------------------------------------------------------------------------+


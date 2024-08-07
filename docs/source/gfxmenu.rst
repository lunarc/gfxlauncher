Generating menus
================

To maintain a large number of graphical applications that is using a SLURM backend in different way we need an easy way of creating shortcuts and menus without a lot of manual work. To support this the other part of the GFX Launcher framework is the **gfxmenu** command which is a special tool for automatically generating a user menu structure and related shortcuts with **gfxlaunch** commands. 

The main concept is to provide a script for each application that is going run on the backend nodes. The scripts contains the commands for how to start the application and a number of special tags for configuring the behavior of the user interface presented by the **gfxlaunch** command. **gfxmenu** reads these scripts and automatically creates a user menu structure according to the tags in the scripts. 

The **gfxmenu** command should be run at user login and creates entries in the **.local/** and **.config/** folders of the users home directory. A suitable place for this script is a runscript in the **/etc/profile.d** folder, calling the **gfxmenu** command (described below). 

Creating start-scripts for use with gfxmenu
-------------------------------------------

To use the **gfxmenu** tool to generate menus, every application that should be integrated into the menu needs to have a special start script. The filenames of these scripts should be in the form of:

``[Application name and version].sh``

An example of a script filename is shown below:

``blender-3.5.1.sh``

The main purpose of the script is to launch the application and provide launcher tags customising the **gfxlaunch** user interface. If the application requires hardware accelerated graphics it is usually started with the **vglrun** command in this script. An example of such a script is shown below:

.. code-block:: bash

    #!/bin/sh

    ##LDT category = "Post Processing"
    ##LDT title = "ParaView 5.9.1"
    ##LDT group = "ondemand"

    vglrun /sw/pkg/paraview/5.9.1/bin/paraview

The ``##LDT`` tags are special tags used by the **gfxmenu** scripts to greate **gfxlaunch** commands in the desktop shortcuts with the proper settings and window title.

The following attributes are supported by **gfxmenu**:

+------------------------+-------------------------------------------------------------------+
| Attribute              | Description                                                       |
+------------------------+-------------------------------------------------------------------+
| ##LDT category         | Menu category to add the menu item.                               |
+------------------------+-------------------------------------------------------------------+
| ##LDT title            | Menu item name. This will also be assigned to the GfxLauncher UI. |
+------------------------+-------------------------------------------------------------------+
| ##LDT part             | Default partition used when submitting the job                    |
+------------------------+-------------------------------------------------------------------+
| ##LDT job              | Job type. Currently one of vm, notebook and jupyterlab            |
+------------------------+-------------------------------------------------------------------+
| ##LDT group            | Partition group to display in user interface (--group)            |
+------------------------+-------------------------------------------------------------------+
| ##LDT feature_disable  | Hide the feature selection combo.                                 |
+------------------------+-------------------------------------------------------------------+
| ##LDT part_disable     | Hide the partition selection combi                                |
+------------------------+-------------------------------------------------------------------+
| ##LDT no_launcher      | Creates a direct launch of the script, bypassing the backend (yes)|
+------------------------+-------------------------------------------------------------------+

When the job attribute is specified the script can be empty except for the attribute declarations.

A script for a Jupyter Lab session is shown below:

.. code-block:: bash

    #!/bin/sh

    ##LDT category = "Development"
    ##LDT title = "Jupyter Lab"
    ##LDT part = "lu"
    ##LDT job = "jupyterlab"

.. note::

    The **gfxmenu** the no_launcher attribute is used to create a direct launch of the script, bypassing the backend. This is useful for applications that do not require a backend job to be started. However, as the gnome shell is launched early it is not certain that module commands are available. The start scripts needs to set the paths to the applications manually.

Generating menus and desktop entries
------------------------------------

The **gfxmenu** uses the directories in the /etc/gfxlauncher.conf configuration files to read the start-scripts and generate the menus items and directories. An example of running this command is shown below:

.. code-block:: bash

    $ gfxmenu
    LUNARC HPC Desktop - User menu tool - Version 0.9.4
    Written by Jonas Lindemann (jonas.lindemann@lunarc.lu.se)
    Copyright (C) 2018-2023 LUNARC, Lund University
    Using configuration file : /sw/pkg/ondemand-dt/etc/gfxlauncher.conf

Adding menus to shared desktop setup
------------------------------------

The generated menus can be added by using the following profile.d script. This script activates the menu if the user is found in the specified grantfile.

/etc/profile.d/ondemand-dt-00.sh:

.. code-block:: bash

    #/bin/bash

    export ONDEMAND_DT_DIR=/sw/pkg/gfxlauncher
    export PATH=${ONDEMAND_DT_DIR}:$PATH

    # Generate user menu

    gfxmenu --silent &>/dev/null

This script will generate a user menu structure in the users home directory. With the following layout:

In the **[User home directory]/.local/share/applications** folder will contain the generated desktop shortcuts (.desktop) with the prefix set by the configuration variable, **desktop_entry_prefix**. A sample directory is shown below:

.. code-block:: bash
    
    $ ls
    gfx-abaqus_cae_6.13-5.desktop           gfx-comsol_multiphysics_5.3.desktop   
    gfx-abaqus_cae_v6r2017.desktop          gfx-fiji_1.53c.desktop
    gfx-abaqus_cae_v6r2019.desktop          gfx-fiji_2.5.0.desktop
    gfx-amira_6.5.0.desktop                 gfx-freesurfer_5.3.0.desktop
    ...

The **[User home directory]/.local/share/desktop-directories** folder will contain the menu directory files (.directory) for each of the categories defined in the run scripts.

.. code-block:: bash

    $ ls -1
    3d_modeling.directory
    3d_visualisation.directory
    cae.directory
    chemistry.directory

The generated menu itself is located in **[User home directory]/.config/menus/applications-merged/applications.menu**. This file is overwritten each time the **gfxmenu** command is executed. In the menus folder, **gfxmenu** will also create symlinks to **gnome-applications-merged**, **kde-applications-merged** and **mate-applications-merged**. 

The menu should update automatically by the desktop environment when the files in these directories are modified or updated.
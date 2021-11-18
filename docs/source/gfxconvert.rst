Generating menus with gfxconvert
================================

**gfxconvert** is a special tool for automatically generating shell-scripts using the **gfxlaunch** tool. The basic idea is to create a script for running the specified application on a backend node. In this script it is possible to add special attributes for specifying job types, default partition and window titles. **gfxconvert** can be run as cron-job in the background to keep the menu system updated when scripts are added.

Creating shell scripts for use with gfxconvert
----------------------------------------------

To use the **gfxconvert** tool to generate menus, every application that should be integrated in the menu needs to have a special start script. **gfxconvert** requires the filename of the script to have the form:

``run_[Application name and version]_rviz-server.sh``

An example of a script filename is shown below:

``run_tomviz-1.5_rviz-server.sh``

The purpose of the script is to launch the application. If the application requires hardware accelerated graphics it is usually started with the **vglrun** command in this script. An example of such a script is shown below:

.. code-block:: bash

    #!/bin/sh

    ##LDT category = "Volume Rendering"
    ##LDT title = "Tomviz 1.5"
    ##LDT group = "ondemand"

    vgl_P=/opt/VirtualGL/bin
    app_P=

    #ml foss/2018b
    module load GCC/7.3.0-2.30
    module load OpenMPI/3.1.1
    ml Tomviz

    $vgl_P/vglrun tomviz

The ``##LDT`` tags are special attributes used by the **gfxconvert** scripts to greate **gfxlaunch** scripts in the correct menu category and with the proper window title.

The following attributes are supported by **gfxconvert**:

+----------------+-------------------------------------------------------------------+
| Attribute      | Description                                                       |
+----------------+-------------------------------------------------------------------+
| ##LDT category | Menu category to add the menu item.                               |
+----------------+-------------------------------------------------------------------+
| ##LDT title    | Menu item name. This will also be assigned to the GfxLauncher UI. |
+----------------+-------------------------------------------------------------------+
| ##LDT part     | Default partition used when submitting the job                    |
+----------------+-------------------------------------------------------------------+
| ##LDT job      | Job type. Currently one of vm, notebook and jupyterlab            |
+----------------+-------------------------------------------------------------------+
| ##LDT group    | Partition group to display in user interface (--group)            |
+----------------+-------------------------------------------------------------------+

When the job attribute is specified the script can be empty except for the attribute declarations.

A script for a Jupyter Lab session is shown below:

.. code-block:: bash

    #!/bin/sh

    ##LDT category = "Development"
    ##LDT title = "Jupyter Lab"
    ##LDT part = "snic"
    ##LDT job = "jupyterlab"

Generating the client scripts with gfxconvert
---------------------------------------------

The **gfxconvert** uses the directories in the /etc/gfxlauncher.conf configuration files to read the launchscripts and generate the menus items and directories. An example of running this command is shown below:

.. code-block:: bash

    $ gfxconvert
    LUNARC HPC Desktop - Wrapper script  - Version 0.8.1
    Written by Jonas Lindemann (jonas.lindemann@lunarc.lu.se)
    Copyright (C) 2018-2020 LUNARC, Lund University
    Using configuration file : /sw/pkg/rviz/etc/gfxlauncher.conf
    ...
    Creating desktop entry 'run_hypermesh_rviz-slurm.sh'
    Creating desktop entry 'run_cellprofiler-3.0.0-rviz-server.sh_rviz-slurm.sh'
    Creating desktop entry 'run_vmd-1.9.2_rviz-slurm.sh'
    Creating desktop entry 'run_matlab-2018b_rviz-slurm.sh'
    Creating desktop entry 'run_freesurfer-6.0.0_rviz-slurm.sh'
    Creating desktop entry 'run_hypergraph_rviz-slurm.sh'

It is also possible to do a dryrun of the process by using the command:

.. code-block:: bash

    $ gfxconvert dryrun

Adding menus to shared desktop setup
------------------------------------

The generated menus can be added by using the following profile.d script. This script activates the menu if the user is found in the specified grantfile.

/etc/profile.d/lunarc_99-activate-LUNARC-dt.sh:

.. code-block:: bash

    #!/bin/sh

    LVIS_GRANTFILE=/sw/pkg/slurm/local/grantfile.lvis

    if grep -qw $USER $LVIS_GRANTFILE
    then
        # Append the LUNARC LVIS menu path.
        export XDG_CONFIG_DIRS=/sw/pkg/rviz/etc/xdg:${XDG_CONFIG_DIRS:-/etc/xdg}
        export XDG_DATA_DIRS=/sw/pkg/rviz/share:${XDG_DATA_DIRS:-/usr/local/share:/usr/share}

        # Add the default menu merging directive to the menu file.
        if ! grep -qs '<DefaultMergeDirs/>' ~/.config/menus/applications.menu
        then
            sed -i '/<DefaultDirectoryDirs\/>/a <DefaultMergeDirs/>' \
                ~/.config/menus/applications.menu
            # Make Mate reload the menu file.
            ln -sf applications.menu ~/.config/menus/mate-applications.menu
        fi
        export LVIS_USER=$USER
    fi

If the menus should be availble for all users the outer if-statement cab be removed.

.. code-block:: bash

    #!/bin/sh

    # Append the LUNARC LVIS menu path.
    export XDG_CONFIG_DIRS=/sw/pkg/rviz/etc/xdg:${XDG_CONFIG_DIRS:-/etc/xdg}
    export XDG_DATA_DIRS=/sw/pkg/rviz/share:${XDG_DATA_DIRS:-/usr/local/share:/usr/share}

    # Add the default menu merging directive to the menu file.
    if ! grep -qs '<DefaultMergeDirs/>' ~/.config/menus/applications.menu
    then
        sed -i '/<DefaultDirectoryDirs\/>/a <DefaultMergeDirs/>' \
            ~/.config/menus/applications.menu
        # Make Mate reload the menu file.
        ln -sf applications.menu ~/.config/menus/mate-applications.menu
    fi
    export LVIS_USER=$USER

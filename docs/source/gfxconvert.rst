Generating menus with gfxconvert
================================

**gfxconvert** is a special tool for automatically generating shell-scripts using the **gfxlaunch** tool. The basic idea is to create a script for running the specified application on a backend node. In this script it is possible to add special attributes for specifying job types, default partition and window titles. **gfxconvert** can be run as cron-job in the background to keep the menu system updated when scripts are added.

Creating shell scripts for use with gfxconvert
----------------------------------------------

Generating gfxlaunch based shell scripts for menus
--------------------------------------------------


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

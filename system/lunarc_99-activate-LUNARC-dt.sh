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


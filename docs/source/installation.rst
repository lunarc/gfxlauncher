Installation
============

GfxLauncher doesn't come as a package (yet). Installation is done by unpacking the distribution and configuring the application using configuration files and environment variables.

Downloading
-----------

Latest version of the software can be found at:

https://github.com/lunarc/gfxlauncher/releases


Installing from PyPi
--------------------

Since version 0.9.13 GfxLauncher is available on PyPi. To install it, run:

.. code-block:: bash

    $ pip install gfxlauncher

To validate the installation, run:

.. code-block:: bash

    $ gfxlaunch --help

This will show the help text and version number for the gfxlaunch command as shown below:

.. code-block:: 
    LUNARC HPC Desktop On-Demand - Version 0.9.13
    Copyright (C) 2017-2024 LUNARC, Lund University
    This program comes with ABSOLUTELY NO WARRANTY; for details see LICENSE.
    This is free software, and you are welcome to redistribute it
    under certain conditions; see LICENSE for details.


    usage: gfxlaunch [-h] [--simplified] [--cmd CMDLINE] [--vgl] [--vglrun] [--title TITLE] [--partition PART] [--account ACCOUNT]
                    [--grantfile GRANT_FILENAME] [--exclusive] [--count COUNT] [--memory MEMORY] [--time TIME] [--only-submit] [--job JOB_TYPE]
                    [--name JOB_NAME] [--tasks-per-node TASKS_PER_NODE] [--cpus-per-task CPUS_PER_TASK] [--no-requeue] [--user USER]
                    [--ignore-grantfile] [--jupyterlab-module JUPYTERLAB_MODULE] [--notebook-module NOTEBOOK_MODULE] [--autostart] [--locked]
                    [--group GROUP] [--silent] [--splash] [--restrict RESTRICT] [--part-disable] [--feature-disable]

Exracting source package
------------------------

Unpack the distribution in a suitable location.

.. code-block:: bash

    $ tar xvzf v0.9.3.tar.gz

Make sure the search path is added to this location.

Installing requirements
-----------------------

The requirements for GfxLauncher is a Python 3.x interpreter with the following additional packages:

 * PyQt 5.x
 * configparser

Disk layout
-----------

The installation of GfxLauncher requires directory locations to fully function:

 * Main installation directory, where the Python-software is installed. (User readable - Admin writable)
 * Script directory - (User readable - Admin writable)
 

Required directories for the Installation
-----------------------------------------

The recommended way of installing GfxLauncher is to create a main directory, **ondemand-dt**, in which we place the launcher scripts as well as the configuration and run-scripts.

+----------------------------------------------------------------------------------------------------------------------------+
| Directory                     | Description                                                                                |
+-------------------------------+--------------------------------------------------------------------------------------------+
| .../ondemand-dt/gfxlauncher   | Main installation directory of GfxLauncher                                                 |
+-------------------------------+--------------------------------------------------------------------------------------------+
| .../ondemand-dt/etc           | Launcher configuration files.                                                              |
+-------------------------------+--------------------------------------------------------------------------------------------+
| .../ondemand-dt/run           | Launcher run-scripts with launcher tags.                                                   |
+-------------------------------+--------------------------------------------------------------------------------------------+
    
Setting up a runtime environment
--------------------------------

For the command line tools in the distribution to work the **.../ondemand-dt/gfxlauncher** directory must be added to the search path for all users. This can best be achieved by adding a profile.d script:

/etc/profile.d/ondemand-dt-00.sh:

.. code-block:: bash

    #/bin/bash

    export ONDEMAND_DT_DIR=/sw/pkg/gfxlauncher
    export PATH=${ONDEMAND_DT_DIR}:$PATH


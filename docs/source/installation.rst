Installation
============

GfxLauncher doesn't come as a package (yet). Installation is done by unpacking the distribution and configuring the application using configuration files and environment variables.

Downloading
-----------

Latest version of the software can be found at:

https://github.com/lunarc/gfxlauncher/releases


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

+-------------------------------+--------------------------------------------------------------------------------------------+
| Directory                     | Description                                                                                |
+-------------------------------+--------------------------------------------------------------------------------------------+
| .../ondemand-dt/gfxlauncher | Main installation directory of GfxLauncher                                                 |
+-------------------------------+--------------------------------------------------------------------------------------------+
| .../ondemand-dt/etc         | Launcher configuration files.                                                              |
+-------------------------------+--------------------------------------------------------------------------------------------+
| .../ondemand-dt/run         | Launcher run-scripts with launcher tags.                                                   |
+-------------------------------+--------------------------------------------------------------------------------------------+
    
Setting up a runtime environment
--------------------------------

For the command line tools in the distribution to work the **.../ondemand-dt/gfxlauncher** directory must be added to the search path for all users. This can best be achieved by adding a profile.d script:

/etc/profile.d/ondemand-dt-00.sh:

.. code-block:: bash

    #/bin/bash

    export ONDEMAND_DT_DIR=/sw/pkg/gfxlauncher
    export PATH=${ONDEMAND_DT_DIR}:$PATH


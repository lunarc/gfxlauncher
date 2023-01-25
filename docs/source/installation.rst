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

    $ tar xvzf v0.8.5.tar.gz

Make sure the search path is added to this location.

Installing requirements
-----------------------

The requirements for GfxLauncher is a Python 3.x interpreter with the following additional packages:

 * PyQt 5.x
 * configparser

.. note::
    In the **conda** directory there is an enviornment yml file for creating a conda environment for GfxLauncher.

Disk layout
-----------

The installation of GfxLauncher requires directory locations to fully function:

 * Main installation directory, where the Python-software is installed. (User readable - Admin writable)
 * Configuration directory. (User readable - Admin writable)
 * Directory where menus are to generated. (User readable - Admin writable)
 * pr


Creating a conda environment
----------------------------

The easiest way of providing suitable environment for GfxLauncher is to create an Anaconda environment. This can be done by using the following commands:

.. code-block:: bash

    (base) $ conda create -n gfxlauncher
    (base) $ conda activate gfxlauncher
    (gfxlauncher) $ conda install pyqt
    (gfxlauncher) $ conda install configparser
    
The **gfxconvert** command that generates menus and run-scripts should be able to be used by a system provided Python interpreter. The **configparser** package must then be installed as a system package.

Required directories for the Installation
-----------------------------------------

+-----------------+--------------------------------------------------------------------------------------------+
| Directory       | Description                                                                                |
+-----------------+--------------------------------------------------------------------------------------------+
| default_part    | If no partition is given on the gfxlaunch command line this is the default partition used. |
+-----------------+--------------------------------------------------------------------------------------------+
    
Setting up a runtime environment
--------------------------------

For the command line tools in the distribution to work, the **LHPCDT_PYTHON_RUNTIME** variable must be set to the **bin** directory of the Python runtime used. As an example: **/.../envs/gfxlauncher/bin** (location of the python binary in the gfxlauncher conda environment).

Adding this variable for all users is best accomplished by adding a **/etc/profile.d** script. Below is an example of a profile.d script for setting this variable:

/etc/profile.d/lunarc_99-activate-LUNARC-dt.sh:

.. code-block:: bash

    export LHPCDT_PYTHON_RUNTIME=/sw/pkg/lunarc/envs/gfxlauncher/bin

The search path should point to the Python distribution used.

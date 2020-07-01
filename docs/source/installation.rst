Installation
============

GfxLauncher doesn't come as a package (yet). Installation is done by unpacking the distribution and setting up some environment variables.

Downloading
-----------

Latest version of the software can be found at:

https://github.com/lunarc/gfxlauncher/releases


Installing
----------

Unpack the distribution in a suitable location.

.. code-block:: bash

    $ tar xvzf v0.5.3.tar.gz

Make sure the search path is added to this location.

Requirements
------------

The requirements for GfxLauncher is a Python 3.x interpreter with the following additional packages:

 * PyQt 5.x
 * configparser

In the **conda** directory there is an enviornment yml file for creating a conda environment for GfxLauncher.

Setting runtime environment for all users
-----------------------------------------

For the command line tools in the distribution to work, the **LHPCDT_PYTHON_RUNTIME** variable must be set to the **bin** directory of the Python runtime used. As an example: **/.../envs/gfxlauncher/bin**.

Adding this variable for all users is best accomplished by adding a **/etc/profile.d** script. Below is an example of a profile.d script for setting this variable:

/etc/profile.d/lunarc_99-activate-LUNARC-dt.sh:

.. code-block:: bash

    export LHPCDT_PYTHON_RUNTIME=/sw/pkg/lunarc/envs/gfxlauncher/bin

The search path should point to the Python distribution used.

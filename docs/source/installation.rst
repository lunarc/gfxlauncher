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

For the command line tools in the distribution to work, the **LHPCDT_PYTHON_RUNTIME** variable must be set to the **bin** directory of the Python runtime used. As an example: **/.../envs/gfxlauncher/bin**.


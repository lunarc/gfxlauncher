Quickstart
==========

This page gets a single application from a fresh GfxLauncher install to a working
desktop menu entry. It's aimed at the person setting up GfxLauncher on a cluster
(usually an admin) - end users just click the menu item that comes out of the last
step.

1. Install
----------

.. code-block:: bash

    $ pip install gfxlauncher
    $ gfxlaunch --help

If the help text and version number are printed, the command line tools are on
your ``PATH`` and ready to use. See :doc:`installation` for PyPI vs. source
package installs and the recommended directory layout.

2. Write a minimal configuration
---------------------------------

GfxLauncher and ``gfxmenu`` read their settings from ``/etc/gfxlauncher.conf``.
A minimal file only needs a script directory and a default Slurm partition:

.. code-block:: ini

    [general]
    script_dir = /sw/pkg/ondemand-dt/run

    [slurm]
    default_part = mypartition
    default_account = myaccount

See :doc:`configuration` for the full set of options (feature/partition
descriptions, partition groups, Jupyter/RStudio/Ollama backends, ...).

3. Create a start-script for one application
----------------------------------------------

``gfxmenu`` builds menus from small shell scripts placed in ``script_dir``, one
per application. Create ``/sw/pkg/ondemand-dt/run/xterm.sh``:

.. code-block:: bash

    #!/bin/sh

    ##LDT category = "Utilities"
    ##LDT title = "Terminal"

    xterm

Then generate the menu:

.. code-block:: bash

    $ gfxmenu

This writes a desktop entry into ``~/.local/share/applications`` and updates the
application menu. See :doc:`gfxmenu` for the full ``##LDT`` tag reference and how
to roll this out for all users via ``/etc/profile.d``.

4. Test the launch directly
-----------------------------

Before relying on the generated menu entry, it's worth calling ``gfxlaunch``
directly to confirm the Slurm submission and connection work:

.. code-block:: bash

    $ gfxlaunch --title "Terminal" --partition mypartition --account myaccount --cmd xterm

This submits a placeholder job to ``mypartition`` and opens ``xterm`` on the
allocated node over SSH once it starts running. See :doc:`gfxlaunch` for every
switch, and :doc:`technical_description` for how the different launch methods
(SSH, VirtualGL, notebooks, RDP) work under the hood.

Next steps
----------

* :doc:`node_config` - required setup on the compute nodes (pam_exec) so the
  SSH-launched application gets the job's resource limits.
* :doc:`configuration` - Jupyter, RStudio and Ollama backends, partition
  groups, and hiding features/partitions from users.
* :doc:`gfxmenu` - rolling out generated menus to every user at login.

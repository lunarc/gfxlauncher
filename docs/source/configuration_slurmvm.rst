Configuration of Windows VM allocation
======================================

Allocation of Windows virtual machines is handled by a special prolog/epilog script for SLURM. This script will maintain a small database of allocated VMs. The prolog-script will also create a special file in the users home folder for any allocated vm:s during the life time of the job. After job termination the script will also remove this file.

To make sure the configured virtual machines are not used by other users the prolog/epilog can also be configured to logoff all users after a completed job and also enable/disable user accounts on the configured VMs.

Installing prolog/epilog script in SLURM
----------------------------------------

The prolog/epilog script, prolog, is provided in the source distribution in the **slurmvm**. To integrate this script in slurm it must be copied/linked to the slurm configuration directory to /etc/slurm/prolog and /etc/slurm/epilog scripts. The easiest way is to just create symbolic links from the source installation directory for the required files.

.. code-block:: bash

    cd /etc/slurm
    ln -s /[install-dir]/gfxlauncher/slurmvm/prolog prolog
    ln -s /[install-dir]/gfxlauncher/slurmvm/prolog epilog
    ln -s /[install-dir]/gfxlauncher/slurmvm/lhpcvm.py lhpcvm.py

Configuration of SLURM virtual node
-----------------------------------

A special node must be configured that will handle the allocation of the virtual machines. A typical configuration in the slurm.conf looks like this:

.. code-block:: bash

    #virtual node for windows integration
    NodeName=wg01    Procs=1 RealMemory=800 Sockets=1 CoresPerSocket=1 ThreadsPerCore=1 Gres=win10m:4 Feature=win,virt State=UNKNOWN
    PartitionName=win Nodes=wg01 OverSubscribe=YES Default=NO  MaxTime=168:00:00 DefaultTime=00:01 ExclusiveUser=no State=UP

As the virtual node does not represent real hardware it has to be configured with the **OverSubscribe=YES** directive. This also enable the virtual node to be a small virtual machine with just enough resources to run the slurmd-daemon.

In the configuration above the virtual node wg01 maintains 4 virtual machnies as a consumable SLURM resource, **Gres=win10m:4**. This must match the actual configuration of the prolog/epilog script described in the next section.

Configuring the VM backend
--------------------------

The configuration of the prolog/epilog script is done through the configuration file **/etc/slurm/lhpcvm.conf**. On a high level the file defines the virtual machines configured by the node. The number of configured machines should correspond to the configured consumable resources in SLURM. 

A typical configuration file for 4 virtual machines are shown below. The different sections are described in separate sections.

.. code-block:: ini

    [DEFAULT]
    loglevel = ERROR
    manage_server = yes

    [win10-default]
    logoff_users_script = /root/rviz/bin/lunarc-logoff-all-users.sh
    disable_user_script = /root/rviz/bin/lunarc-disable-aduser.sh
    enable_user_script = /root/rviz/bin/lunarc-enable-aduser.sh
    update_script = /root/rviz/bin/install-win-updates.sh

    [win10m-ip22]
    name=win10m-ip22
    hostname=10.18.50.22
    kind=win10

    [win10m-ip23]
    name=win10m-ip23
    hostname=10.18.50.23
    kind=win10

    [win10m-ip24]
    name=win10m-ip24
    hostname=10.18.50.24
    kind=win10

    [win10m-ip25]
    name=win10m-ip25
    hostname=10.18.50.25
    kind=win10

The [DEFAULT] section
---------------------

The default section controls logging and settings that apply to all sections. The availble key words are described in the table below:

+---------------+-----------------------------------------------------------------------------+
| Variable      | Description                                                                 |
+---------------+-----------------------------------------------------------------------------+
| loglevel      | Level of logging can be VERBOSE, INFO, WARNING, ERROR, CRITICAL             |
+---------------+-----------------------------------------------------------------------------+
| manage_server | This variable controls if the virtual machines should be managed by the     |
|               | prolog/epilog script. yes enables logoff/enable/disable                     |
+---------------+-----------------------------------------------------------------------------+

The [win10-default] section
---------------------------

This section controls the behavior of nodes configured with the platform property kind=win10. Currently supported platforms are currently only **win10**

The variables that can be set in this section defines the scripts that will be called by the prolog/epilog script at start and end of the job. The different options are described in the table below:

+---------------------+---------------------------------------------------------------------------------------+
| Variable            | Description                                                                           |
+---------------------+---------------------------------------------------------------------------------------+
| logoff_users_script | Script that is called with the virutal machine hostname. Should logoff all users.     |
+---------------------+---------------------------------------------------------------------------------------+
| disable_user_script | Script that is called with the username of the user account that should be disabled.  |
+---------------------+---------------------------------------------------------------------------------------+
| enable_user_script  | Script that is called with the username of the user account that should be enabled.   |
+---------------------+---------------------------------------------------------------------------------------+
| update_script       | Script that is called with the virtual machine hostname. Should update the node.      |
+---------------------+---------------------------------------------------------------------------------------+

The virtual server configuration sections
-----------------------------------------

Other sections in the configuration are configurations for each virtual server. A virtual server is configured with a section named with the available hostname of the server. The configuration variables for each section is described in the following table:

+----------+---------------------------------------------------------------------------------------+
| Variable | Description                                                                           |
+----------+---------------------------------------------------------------------------------------+
| name     | Descriptive name of the virtual server.                                               |
+----------+---------------------------------------------------------------------------------------+
| hostname | Specific explicit hostname of the server.                                             |
+----------+---------------------------------------------------------------------------------------+
| kind     | Platform of the virtual server. Currently only win10 is available.                    |
+----------+---------------------------------------------------------------------------------------+



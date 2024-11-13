Using the launcher
==================

Applications are started by using the command line tool **gfxlaunch**. The purpose of this command is to provide a customisable user interface for launching different kinds of interactive applications. It can be used standalone in your own workflows or in combination with the **gfxconvert** tool for generating menus and special client scripts that will be called from the menu items. This chapter describes the options and how this command can be used for different kind of applications.

Command line switches
---------------------

The command line switches of **gfxlaunch** is described in the table below:

+---------------------------------+---------------------------------------------------+
| Switch                          | Description                                       |
+---------------------------------+---------------------------------------------------+
| --vgl                           | Use VirtuaGL infrastructure                       |
+---------------------------------+---------------------------------------------------+
| --vglrun                        | Prefix command with vglrun                        |
+---------------------------------+---------------------------------------------------+
| --title TITLE                   | Window title                                      |
+---------------------------------+---------------------------------------------------+
| --partition PART                | Default partition to use                          |
+---------------------------------+---------------------------------------------------+
| --grantfile GRANT_FILENAME      | Default account to use                            |
+---------------------------------+---------------------------------------------------+
| --exclusive                     | Use node exclusively                              |
+---------------------------------+---------------------------------------------------+
| --count COUNT                   | Number of cpu:s to us                             |
+---------------------------------+---------------------------------------------------+
| --memory MEMORY                 | Memory in MB to use                               |
+---------------------------------+---------------------------------------------------+
| --time TIME                     | Job walltime                                      |
+---------------------------------+---------------------------------------------------+
| --only-submit                   | Only job submission. No remote execution to node. |
+---------------------------------+---------------------------------------------------+
| --job JOB_TYPE                  | Submit a specific type of job.                    |
+---------------------------------+---------------------------------------------------+
| --name JOB_NAME                 | Job name in LRMS.                                 |
+---------------------------------+---------------------------------------------------+
| --tasks-per-node TASKS_PER_NODE | Number of tasks per node.                         |
+---------------------------------+---------------------------------------------------+
| --ignore-grantfile              | Ignore grantfile checking.                        |
+---------------------------------+---------------------------------------------------+
| --autostart                     | Start application directly with given parameters  |
+---------------------------------+---------------------------------------------------+
| --locked                        | Prevent changes to settings in user interface     |
+---------------------------------+---------------------------------------------------+
| --group GROUP                   | Display only partitions in the GROUP group.       |
+---------------------------------+---------------------------------------------------+

Running standard X11 application (No graphics)
----------------------------------------------

Standard X11 applications are launched by submitting a place holder job to Slurm. When the job is running gfxlaunch will execute the X11 application by using SSH with the -X switch. An example of the command line options used is shown below:

.. code-block:: bash

    gfxlaunch --title "Graphical Terminal" --partition lvis --account lvis-test --exclusive --time 00:45:00 --tasks-per-node=1 --cmd xterm

The **--title** switch sets the window title. **--partition** and **--account** sets the Slurm partition and account to be used when submitting the job. **--exclusive** and **--tasks-per-node** corresponds to Slurm job attributes. **--time** sets the wall time for the job.  Most of these options can be overidden by the user in the user interface.

If all of the node should be used including all cpu-cores, use **--tasks-per-node=-1** and **--exclusive** the command line becomes:

.. code-block:: bash

    gfxlaunch --title "Graphical Terminal" --partition lvis --account lvis-test --exclusive --time 00:45:00 --tasks-per-node=-1 --cmd xterm

Running applications using hardware accelerated graphics
--------------------------------------------------------

Applications requiring hardware accelerated graphics (OpenGL) require special launch methods to run. GfxLauncher supports the VirtualGL model of running hardware accelerated applications remotely. In this model the OpenGL graphics stream is tunneled from a server with a GPU or a graphics card to a client server with a standard VNC based remote desktop session. Launching the actual application is done by using the VirtualGL command, **vglconnect**, to setup the tunneling of the  graphics stream and the **vglrun** command to wrap the actual application and stream it back to the client. 

A VirtualGL based session is configured by specifying the **--vgl** switch in the **gfxlaunch** tool. This will use the **vglconnect** command instead of **ssh** to start the remote application. In addition the **--vglrun** switch can be used to indicate that **gfxlaunch** should prefix the client launch script with the **vglrun** command. If you omit this switch you will have to call vglrun in your own script.

In the following example we use the **--vgl** switch with our own command line calling **vglrun** and then xterm.

.. code-block:: bash

    gfxlaunch --vgl --title "X terminal" --partition lvis --account lvis-test --exclusive --cmd "vglrun xterm"

This launches a xterm window with support for running accelerated applications. 

In the next example we add the **--vglrun** switch to let **gfxlaunch** call our command using **vglrun**.

.. code-block:: bash

    gfxlaunch --vgl --vglrun --title "X terminal" --partition lvis --account lvis-test --exclusive --cmd xterm

As many applications could have more complicated setups it is often a good idea to implement the client launch procedure in a standalone script. Below shows a script for starting ParaView on a backend server:

.. code-block:: bash

    ./gfxlaunch --vgl --title "Paraview-5.4.1" --partition lvis --account lvis-test --exclusive --tasks-per-node=-1 --cmd /sw/pkg/rviz/sbin/run/run_paraview-5.4.1_rviz-server.sh

The script contains the followin code:

.. code-block:: bash    
    
    #!/bin/sh

    ##LDT category = "Post Processing"
    ##LDT title = "ParaView 5.4.1"

    vgl_P=/opt/VirtualGL/bin
    app_P=/sw/pkg/paraview/5.4.1/bin

    $vgl_P/vglrun $app_P/paraview

In this case the script will call the application with the **vglrun** command.

Running Jupyter Notebooks and Jupyter Labs
------------------------------------------

Jupyter Notebook and Jupyter Lab session are local web servers that acts as the applications main user interface. GfxLauncher starts these kind of applications by sending a normal job to the Slurm queue. It then waits for the URL of the started web server to appear in the job output and launches a browser session to this URL. The user interface displays a special button to reconnect to the job if the users closes the browser session by mistake.

To launch a Jupyter Notebook session the following switches for the **gfxlaunch** command.

.. code-block:: bash

    gfxlaunch --title "Jupyter Notebook" --partition lvis --account lvis-test --only-submit --job=notebook

The **--only-submit** tells **gfxlaunch** to submit a standard job instead of a placeholder job. The **--job=notebook** tells the **gfxlaunch** command to submit a Jupyter Notebook job to Slurm.

A Jupyter Lab session is launched in a similar way except for using the switch **--job=jupyterlab**.

.. code-block:: bash

    gfxlaunch --title "Jupyter Lab" --partition lvis --account lvis-test --only-submit --job=jupyterlab

Running Windows based desktop applications
------------------------------------------

This launch method requires a dedicated node that will control access to pre configured Windows virtual machines. The backend will allocate an availble VM. The launch method monitors a special file .lhpc/vm_host_[jobid].ip which contains the ip-number to the allocated VM. When the file for the corresponding job is available, gfxlaunch will start a xfreerdp connection to the VM automatically.

.. code-block:: bash

    gfxlaunch --title "Windows Application" --partition win --account lvis-test --simplified --only-submit --ignore-grantfile --job=vm




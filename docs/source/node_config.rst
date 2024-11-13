Configuring compute nodes
=========================

The compute nodes are where the applications will launched by the GfxLauncher framework. Usually the compute nodes are part of a cluster and managed by a job scheduler like Slurm. For the GfxLauncher to work properly the compute nodes need to be configured so that applications can be launched by issuing a command on the node using SSH or vglconnect. The following sections describe one way of how to configuring the compute nodes for GfxLauncher.

There are two requirements for the compute nodes:

 1. A user must be able to use SSH execute applications. See Slurm documentation (https://slurm.schedmd.com/pam_slurm_adopt.html)
 2.  When executing the application on the node it has to be associated with the same context as the placeholder job. 

To solve the second point a special pam module is required to associate the SSH session with the running job. I the following sections a solution to this is configured. It should also be possible to configure this with the **pam_slurm_adopt** module, but it has not been thoroughly tested yet.

Adding pam_exec to /etc/pam.d/sshd
----------------------------------

Add the following line to the /etc/pam.d/sshd to the end of this configuration file:

.. code-block:: bash

    session    optional     pam_exec.so /sbin/pam_ssh_exec.sh

Adding pam_ssh_exec.sh script to /sbin
--------------------------------------

In the system directory of the distribution the **pam_ssh_exec.sh** script can be found. Copy this script to **/sbin** on the nodes. The script contains the following code:

.. code-block:: bash

    #!/bin/sh

    SLURMDIR=/usr/bin

    [ "$PAM_USER" = "root" ] && exit 0
    [ "$PAM_TYPE" = "open_session" ] || exit 0

    squeue=$SLURMDIR/squeue

    if [ ! -x $squeue ]; then
    exit 0
    fi

    uidnumber=$(id -u $PAM_USER)
    echo "uidnumber = "$uidnumber >> /var/log/pam_exec.log
    host=$(hostname -s)

    # last job the user started is where these tasks will go
    jobid=$($squeue --noheader --format=%i --user=$PAM_USER --node=localhost | tail -1)

    [ -z "$jobid" ] && exit 0

    for system in freezer cpuset; do
        cgdir=/sys/fs/cgroup/$system/slurm

        # if the cgdir doesn't exist skip it
        [ -d $cgdir ] || continue
        # first job step is where we'll put these tasks
        cgtasks=$(find $cgdir/uid_$uidnumber/job_$jobid -mindepth 2 -type f -name tasks -print -quit)
        [ -f $cgtasks ] && echo $PPID > $cgtasks
        [ -f $cgtasks ] && echo $PPID >> /var/log/pam_exec.log

    done

    exit 0

This script will add the SSH session to the same cgroups task group, enabling the same resource limits as for other jobs on the node. A log file /var/log/pam_exec.log will be created on the node for debugging purposes.

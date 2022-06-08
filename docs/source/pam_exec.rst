Configuring compute nodes
=========================

To be able launch application in the same context as the placeholder job running on the node, a special pam module and script must be used.

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
#!/bin/sh

SLURMDIR=/usr/bin

[ "$PAM_USER" = "root" ] && exit 0
[ "$PAM_TYPE" = "open_session" ] || exit 0

squeue=$SLURMDIR/squeue

if [ ! -x $squeue ]; then
   exit 0
fi

uidnumber=$(id -u $PAM_USER)
#echo "uidnumber = "$uidnumber >> /var/log/pam_exec.log
#host=$(hostname -s)

# last job the user started is where these tasks will go
jobid=$($squeue --noheader --format=%i --user=$PAM_USER --node=localhost | tail -1)

[ -z "$jobid" ] && exit 0

for system in freezer cpuset; do
    cgdir=/cgroup/$system/slurm

    # if the cgdir doesn't exist skip it
    [ -d $cgdir ] || continue
    # first job step is where we'll put these tasks
    cgtasks=$(find $cgdir/uid_$uidnumber/job_$jobid -mindepth 2 -type f -name tasks -print -quit)
    [ -f $cgtasks ] && echo $PPID > $cgtasks
    #[ -f $cgtasks ] && echo $PPID >> /var/log/pam_exec.log

done

exit 0


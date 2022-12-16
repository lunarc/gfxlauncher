#!/bin/bash

#SBATCH --time=08:30:00

echo "Starting at `date`"
echo "Running on hosts: $SLURM_NODELIST"
echo "Running on $SLURM_NNODES nodes."
echo "Running on $SLURM_NPROCS processors."
echo "SLURM JobID $SLURM_JOB_ID processors."
echo "Node has $SLURM_CPUS_ON_NODE processors."
echo "Node has $SLURM_MEM_PER_NODE total memory."
echo "Node has $SLURM_MEM_PER_CPU memory per cpu."
echo "Current working directory is `pwd`"
echo "Current path is $PATH"

while true; do sleep 5; done

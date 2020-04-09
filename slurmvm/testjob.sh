#!/bin/sh
#SBATCH -p win -A lvis-test 
#SBATCH --mem=100
#SBATCH --oversubscribe --gres=win10m
#SBATCH --time=00:60:00

while true; do date; sleep 5; done

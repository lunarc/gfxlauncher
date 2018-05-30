#!/bin/env python

import os, sys, argparse

from lhpcdt import *

if __name__ == '__main__':

    slurm = lrms.Slurm()
    slurm.query_partitions()
    features = slurm.query_features("lvis")
    gres = slurm.query_gres("lvis")
    print(features)
    print(gres)

    job = jobs.Job(account = "LVIS2017-5-1", partition="lvis")
    job.add_constraint("mem64G")
    job.add_constraint("gpu2k20")
    job.gres = "gpu:1"
    job.update()
    print(job)


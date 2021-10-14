#!/bin/env python

from datetime import datetime
import os, time, glob, sys, getpass

from lhpcdt import jobs
from lhpcdt import lrms
from lhpcdt import remote
from lhpcdt import settings
from lhpcdt import config
from lhpcdt import resource_win


def has_project():
    """Check for user in grantfile"""

    tool_path = os.path.dirname(os.path.abspath(sys.argv[0]))
    sys.path.append(tool_path)

    launch_settings = settings.LaunchSettings.create()
    launch_settings.tool_path = tool_path

    cfg = config.GfxConfig.create()   

    slurm = lrms.Slurm()
    slurm.verbose = False
    tool_path = settings.LaunchSettings.create().tool_path

    feature_ignore = cfg.feature_ignore[1:-1]
    exclude_set = set(feature_ignore.split(","))
    print(exclude_set)

    user = getpass.getuser()
    part = "lu"

    slurm.query_partitions()
    #features = slurm.query_features(part)

    for p in slurm.partitions:
        print("Partition: %s Features:" % p)
        print("\t"+", ".join(slurm.query_features(p, exclude_set)))

    grantfile_list = []

    # --- If we have a explicit grantfile use that only.

    if cfg.grantfile_dir != "":

        # --- Grant file directory given. Search it for grantfiles

        print("Searching for grantfiles in %s." % cfg.grantfile_dir)

        grant_files = glob.glob(cfg.grantfile_dir+'/grantfile.*')

        for grant_filename in grant_files:
            if (not '~' in grant_filename) and (len(grant_filename.split("."))==2):
                suffix = grant_filename.split('.')[1]
                if cfg.grantfile_suffix=='':
                    print("Parsing grantfile: %s" % grant_filename)
                    grantfile_list.append(lrms.GrantFile(grant_filename))
                elif cfg.grantfile_suffix == suffix:
                    print("Parsing grantfile (suffix match): %s" % grant_filename)
                    grantfile_list.append(lrms.GrantFile(grant_filename))
    else:

        # --- Do we have a grantile_base directive?

        grant_filename = config.grantfile_base % part
        if os.path.exists(grant_filename):
            grantfile_list.append(lrms.GrantFile(grant_filename))

    active_projects = []
            
    if len(grantfile_list)>0:

        for grant_file in grantfile_list:
            active_projects += grant_file.query_active_projects(user)

        if len(active_projects) > 0:
            account = active_projects[0]
            return True
        else:
            return False
    else:
        return False


if __name__ == "__main__":

    has_project()


import os, sys, getpass

sys.path.append("..")

from lhpcdt import *

if __name__ == "__main__":

	grantfile = lrms.GrantFile("/sw/pkg/slurm/local/grantfile.lu")
	print(grantfile.query_active_projects(getpass.getuser()))

	accmgr = lrms.AccountManager()
	print(accmgr.query_active_projects(getpass.getuser()))

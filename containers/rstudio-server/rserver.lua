help([[
RStudio Server - web-based R IDE, launched per SLURM job by gfxlauncher's
RStudio job type (see src/lhpcdt/jobs.py:RStudioJob in the gfxlauncher repo).

Single-user, no-auth: reachability is gated by the SSH tunnel gfxlauncher
sets up to the compute node, the same trust model already used for the
Jupyter Notebook/Lab job types.

Provides `rserver` on PATH - a wrapper that runs RStudio Server inside
this module's Apptainer/Singularity image (bin/rserver alongside this
file; image pulled directly from docker://rocker/rstudio:4.4.2, no
custom build). Not meant to be loaded interactively for desktop use;
for the RStudio Desktop app, use the `rstudio` module instead.
]])

whatis("Description: RStudio Server (single-user, launched per SLURM job)")
whatis("URL: https://posit.co/products/open-source/rstudio-server/")

local version    = myModuleVersion()
local install_ct = "/sw/pkg/rserver/" .. version

prepend_path("PATH", pathJoin(install_ct, "bin"))

setenv("XDG_RUNTIME_DIR", "")
setenv("LC_ALL", "en_US.UTF-8")

conflict("rserver")

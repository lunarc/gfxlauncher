# RStudio Server module install pattern

Backend for gfxlauncher's `rstudio` job type (`src/lhpcdt/jobs.py:RStudioJob`).

## Status: deployed

Installed and loadable as the Lmod module `rserver/4.4.2`
(`/sw/easybuild_milan/modules/all/Core/rserver/4.4.2`), built from the
pulled, community-maintained `docker://rocker/rstudio:4.4.2` image
rather than the custom `.def` recipe below - pulling needs no build
host or root, so it was the simpler path and is now the one actually
in use:

```
singularity pull docker://rocker/rstudio:4.4.2
```

Image lives at `/sw/pkg/rserver/4.4.2/rstudio_4.4.2.sif`, wrapper at
`/sw/pkg/rserver/4.4.2/bin/rserver` (identical to `bin/rserver` in this
directory). `module load rserver/4.4.2` confirmed to put a working
`rserver` on `PATH`.

Exercised end-to-end via `tests/run_test_rstudio.sh` and confirmed
working (see "Known issue" below for how it got there).

## Security: always tunnel-only, never on the node's real interface

`RStudioJob` runs `rserver` with `--auth-none=1` - no login at all.
Early on it bound `--www-address=$HOSTNAME` (the node's real network
address) whenever the site's `jupyter_use_localhost` setting was off
(the default), which meant literally anyone who could route to that
compute node's IP and port could drive R as that user, no credentials
needed - worse than Jupyter's default, which at least has a token in
the URL even when not tunneled.

Fixed by making `RStudioJob` bind `127.0.0.1` unconditionally,
independent of the shared `jupyter_use_localhost` toggle (which
someone could flip for Jupyter's convenience without realizing it was
also RStudio's only line of defense). `launcher.py`'s
`on_notebook_url_found` now checks `self.job.use_localhost` (the
job's own actual state) rather than the site-level setting, so it
always sets up the SSH tunnel for RStudio regardless of site config -
reachable only by whoever can SSH into that specific compute node,
which on a properly configured SLURM cluster (`pam_slurm_adopt` or
similar) is restricted to the job's owner.

## Known issue: connects, then spins forever (2026-08-12, resolved)

`rserver` answers HTTP fine (page loads, spinner shows), but the
session never comes up. That failure wasn't visible at all in the
SLURM `.out` file, because the image's default
`/etc/rstudio/logging.conf` sends log messages to `logger-type=syslog`
- and nothing is listening for syslog inside an unprivileged job, so
they just vanished.

Fixed in `bin/rserver` (there's no CLI flag for this - checked
`rserver --help` directly against the image; a `--log-stderr=1` flag
I'd guessed at doesn't exist and errors out):
- bind-mounts a generated `logging.conf` with `logger-type=stderr` over
  `/etc/rstudio/logging.conf`, so logs stream into the job's `.out`
  file directly, live (`log-level=debug` while this is being
  diagnosed - drop to `warn` once it's working, to cut noise)
- `cleanup()` now also copies `$WORKDIR/var-log` to
  `$HOME/.lhpc/rserver-logs/$SLURM_JOB_ID/` before removing the scratch
  dir, so logs survive a cancelled job, as a second line of defense

**Root cause confirmed** via the stderr logging fix, tested with a real
browser against a live job:

```
[rsession-bmjl] ERROR system error 13 (Permission denied)
[message: User 'bmjl' has id 424, which is lower than the minimum
user id of 1000 (this is controlled by the the auth-minimum-user-id
rserver option)]
```

`rsession` refuses to launch for any uid below `--auth-minimum-user-id`
(default `auto`, resolves to 1000 here) - LUNARC accounts can have
lower uids than that (the reporting account here is uid 424). Fixed by
adding `--auth-minimum-user-id=0` to the `rserver` invocation in
`bin/rserver`. Safe to disable entirely: this container only ever
serves the single user whose SLURM job it's running under, enforced by
the OS via `singularity exec`'s own uid, not by this rserver-level
check.

Validated the fix as far as `curl` can go: ran `rserver` directly here
(outside SLURM) against the deployed image with the flag added -
startup, sqlite schema creation, auth, and user/session creation all
complete cleanly with no privilege/PAM/uid errors. `curl` can't
execute the frontend JS that makes the follow-up API call that
actually launches `rsession`, though, so this doesn't 100% close the
loop by itself - that needs a real browser via gfxlauncher.

**Not yet copied to the deployed module** - `/sw/pkg/rserver/4.4.2/bin/rserver`
still has the old version. Copy this file over it, then re-run
`tests/run_test_rstudio.sh`.

**Note:** right after the module file was added, `module avail rserver`
didn't list it even though `module load rserver/4.4.2` worked fine -
almost certainly Lmod's spider cache lagging the on-disk module tree,
not a real problem. Worth a `module avail` recheck (or a cache
refresh) before assuming it's visible to users/tab-completion.

## Files

- `rstudio-server_ubuntu.def` - optional Apptainer/Singularity build
  recipe for a custom image (same base/toolchain as
  `/sw/pkg/rstudio/rstudio-desktop_ubuntu.def`, installing the
  `rstudio-server` `.deb` instead of the desktop app). **Not what's
  deployed** - kept around in case a custom image is ever needed
  (extra R packages, baked-in `/lunarc` `/projects` binds, etc.)
  beyond what the plain `rocker/rstudio` pull provides.
- `bin/rserver` - the wrapper that's actually deployed. Filename must
  stay exactly `rserver`: `RStudioJob`'s generated job script invokes
  the command `rserver`, and that's what needs to resolve on `PATH`
  after `module load rserver/4.4.2`. Forwards all arguments
  (`--www-address`, `--www-port`, `--auth-none`, and any site
  `extra_args` from the job settings dialog) straight through to the
  real `rserver` inside the container, after adding
  `--server-daemonize=0 --server-user="$USER"` and bind-mounting
  writable `/var/run`, `/var/lib`, `/var/log`, `/tmp` state dirs from a
  per-job scratch directory (the image's rootfs is read-only, and
  rserver normally wants root to spawn per-user sessions via PAM,
  which this unprivileged singularity exec doesn't have).
- `rserver.lua` - Lmod modulefile, matches what's deployed: prepends
  `/sw/pkg/rserver/<version>/bin` to `PATH`.

## Config

`rstudio_module` (in `etc/gfxlauncher.conf`'s `[rstudio]` section, and
`config.py`/`config_template.py`'s defaults) is set to `rserver/4.4.2`
to match.

## Still to confirm

- `--auth-none=1` (set by `RStudioJob`) disables login entirely -
  matches Jupyter's trust model here (SSH tunnel is the only gate),
  but confirm that's acceptable before enabling this job type site-wide.
- Whether `--server-user="$USER"` behaves as expected against the
  `rocker/rstudio` image specifically (its normal Docker entrypoint/init
  scripts, which usually set up the `rstudio` system user and PAM
  config, don't run under `singularity exec` - only the bare `rserver`
  command does).
- End-to-end run through gfxlauncher: `tests/run_test_rstudio.sh`,
  confirm the `RSTUDIO_URL:` marker line gets scraped correctly and the
  SSH tunnel/browser launch works.
- R package/library paths, proxy settings, and any site-specific R
  environment modules aren't wired in yet.

# Ollama chat module install pattern

Backend for gfxlauncher's `ollama` job type (`src/lhpcdt/jobs.py:OllamaChatJob`).

## Status: deployed, confirmed working end-to-end

Ollama itself is **not containerized** - it's a native binary, installed
and loadable as the Lmod module `ollama/0.32.14`
(`/sw/pkg/ollama/0.32.14`). This wrapper (`bin/ollama-chat` in this
directory, identical to `/sw/pkg/ollama/0.32.14/bin/ollama-chat`) is
packaged alongside it in the same module, so `module load ollama/0.32.14`
puts both `ollama` and `ollama-chat` on `PATH`.

Open WebUI has no equivalent native package, so it runs as an unprivileged
Apptainer/Singularity container instead, pulled directly the same way
RStudio's image is (see `containers/rstudio-server/README.md`):

```
singularity pull docker://ghcr.io/open-webui/open-webui:main
```

Image lives at `/sw/pkg/open-webui/open-webui_main.sif`.

Exercised end-to-end via `tests/run_test_ollama.sh` and confirmed
working: model pulls with visible progress, model loads and answers chat
messages through the browser, all without authentication prompts.

## Security: always tunnel-only, never on the node's real interface

Same trust model as `RStudioJob` (see `containers/rstudio-server/README.md`'s
"Security: always tunnel-only" section, including the incident that
motivated it there): `OllamaChatJob` sets `use_localhost = True`
unconditionally, and both `ollama serve` and Open WebUI are bound to
`127.0.0.1` only - never `$HOSTNAME`. Open WebUI's own auth is disabled
(`WEBUI_AUTH=False`, confirmed to actually skip the login/signup screen
entirely rather than just relaxing it), so the SSH tunnel gfxlauncher sets
up is the *only* access gate. Open WebUI's own default bind address is
`0.0.0.0` (every interface) - getting `HOST=127.0.0.1` wrong here would be
strictly worse than the RStudio `--www-address` incident, since there'd be
no credential at all standing between an unauthenticated chat UI and
anyone who can route to the compute node.

## How it works

`bin/ollama-chat` runs two services under one SLURM job:

1. **`ollama serve`**, invoked directly (native install, no `--nv`/container
   GPU passthrough needed - GPU access comes straight from the host
   driver). `OLLAMA_KEEP_ALIVE=-1` keeps the model resident in GPU memory
   for the job's whole lifetime rather than Ollama's default 5-minute idle
   unload - safe here because the job has the GPU exclusively for its
   entire walltime, unlike a shared multi-tenant Ollama deployment.
2. Streams `POST /api/pull`'s newline-delimited JSON progress through a
   small `python3` parser (not the `ollama pull` CLI - its `\r`-updating
   output doesn't produce clean lines in the SLURM `.out` file gfxlauncher
   polls), throttled to whole-percent changes, emitting
   `OLLAMA_PULL_PROGRESS: <0-100>` marker lines that
   `OllamaChatJob.do_process_output` turns into the launcher's progress bar.
3. **Warms the model up** with an empty-prompt `/api/generate` call right
   after the pull completes. `ollama pull` only downloads weights - the
   model doesn't actually load into GPU memory until the first real
   inference request, which for a multi-GB model is slow enough to be
   confusing if it happens silently on the user's first chat message
   instead of here, while the launcher still shows "waiting for chat
   interface to start".
4. **Open WebUI**, via `singularity exec ... bash /app/backend/start.sh`.
   There is no `open-webui` binary on `PATH` inside the image - confirmed
   by inspecting the deployed `.sif` directly, `singularity exec` bypasses
   whatever environment setup the image's normal Docker `ENTRYPOINT` would
   have done. The real entrypoint is `/app/backend/start.sh` (read
   directly from the image), which does honor `HOST`/`PORT`/
   `WEBUI_SECRET_KEY` exactly as this wrapper sets them. One thing to know
   if a job's "extra Open WebUI arguments" field is ever used: `start.sh`
   passes any args it receives straight to `uvicorn ... "$@"`, **replacing**
   its own default `--workers 1` rather than adding to it - so that field
   means raw uvicorn flags, not `open-webui`-style ones.
5. Both services are polled via a `wait_for_port` helper that checks the
   background process is still alive on every iteration and times out
   (120s for Ollama, 300s for Open WebUI, which does DB migrations on
   first run) - printing the last 40 lines of the relevant log instead of
   spinning forever. This exists because a backgrounded (`&`) command's
   failure doesn't trip `set -e`; without it, a bad image path or wrong
   entrypoint fails completely silently, which is exactly what happened
   during initial testing (see "Known issues" below).
6. Prints `OLLAMA_CHAT_URL: http://localhost:$WEBUI_PORT/` - `localhost`,
   not `$HOSTNAME`, matching the Jupyter/RStudio convention
   `jobs.py:386-392` explains (the tunnel rewrite relies on it).

## Known issues (resolved during initial testing)

- **Model cache defaulted to a site-wide path the user couldn't write to**
  (`/sw/data/ollama-models`, permission denied). Fixed by defaulting
  `[ollama] ollama_models_dir` to `$HOME/.lhpc/ollama-models` instead - a
  literal `$HOME` in the config value, which `RawConfigParser` (no
  interpolation) passes through unexpanded all the way into the generated
  SLURM batch script's `export OLLAMA_MODELS_DIR="$HOME/..."` line, where
  bash expands it against the actual submitting user's home at job
  runtime. No site-wide path needs to exist by default; a site admin can
  still point it at a real shared, group-writable location so different
  users' launches reuse each other's already-pulled models.
- **Job hung forever with zero output** waiting for Open WebUI's port.
  Root cause: the `singularity exec ... open-webui serve` command didn't
  exist in the image at all (`FATAL: "open-webui": executable file not
  found in $PATH`), but that failure happened inside a backgrounded `&`
  process, so `set -e` never saw it and the plain `/dev/tcp` poll this
  used to use just spun silently until the job's walltime ran out. Fixed
  two ways: (1) discovered the real entrypoint is `/app/backend/start.sh`
  by reading it directly out of the deployed image, and (2) added the
  `wait_for_port` liveness-check-plus-timeout helper described above so
  the *next* wrong assumption fails fast with a log excerpt instead of
  hanging silently again.
- **`$WORKDIR` under `/tmp` didn't exist** when checking logs on the
  compute node mid-hang. Turned out `TMPDIR` is set per-job to
  `/local/slurmtmp.<jobid>` on this site, not `/tmp` - the wrapper's
  `${TMPDIR:-/tmp}` already handled this correctly, it just wasn't where
  a human expected to look first.
- **First chat response was slow** even after the pull finished - `ollama
  pull` only downloads weights, it doesn't load the model into GPU memory.
  Fixed by the warm-up call and `OLLAMA_KEEP_ALIVE=-1` described above.

## Still to confirm

- Whether the shared-cache path (`ollama_models_dir` pointed at a real
  group-writable location instead of the per-user `$HOME` default) is
  actually safe under concurrent `ollama pull` of the same model from two
  simultaneous jobs. Believed safe - Ollama's blob store is
  content-addressed - but not verified here.
- Model/GPU memory sizing: no admission control yet ties the selected
  Ollama model to the GPU memory available on the allocated partition, so
  a user could pick a model too large for the node they land on.

## Files

- `bin/ollama-chat` - the wrapper that's actually deployed (also lives at
  `/sw/pkg/ollama/0.32.14/bin/ollama-chat`, kept in sync manually - copy
  this file over that path after any change here). Invoked by
  `OllamaChatJob` as `ollama-chat --ollama-port=<port> --webui-port=<port>
  --model "<tag>"`.

There is no `.def` build recipe or Lmod modulefile checked into this
directory (unlike `containers/rstudio-server/`) - the `ollama/0.32.14`
module itself, including its Lmod modulefile, was built and deployed
directly on the cluster rather than through this repo.

## Config

`etc/gfxlauncher.conf`'s `[ollama]` section (mirrored in
`config.py`/`config_template.py` defaults):

| Variable                 | Purpose                                                                 |
|---------------------------|--------------------------------------------------------------------------|
| `ollama_module`           | Lmod module providing `ollama`/`ollama-chat` on `PATH`.                 |
| `ollama_model`            | Default model tag pre-filled in the job settings dialog.                |
| `ollama_models_dir`       | Model cache directory; supports a literal `$HOME` (see above).          |
| `ollama_popular_models`   | Comma-separated list populating the model drop-down in the settings dialog. |

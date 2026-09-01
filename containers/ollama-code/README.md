# Ollama code-model module install pattern

Backend for gfxlauncher's `codemodel` job type (`src/lhpcdt/jobs.py:CodeModelJob`).

Ollama itself is **not containerized** - it's a native binary, installed and
loadable as the same Lmod module used by the `ollama` chat job type (e.g.
`ollama/0.32.14`, `/sw/pkg/ollama/0.32.14`). This wrapper (`bin/ollama-code-api`
in this directory, identical to `/sw/pkg/ollama/0.32.14/bin/ollama-code-api`)
is packaged alongside it in the same module, so `module load ollama/0.32.14`
puts both `ollama` and `ollama-code-api` on `PATH`.

## How this differs from `containers/ollama-chat`

`ollama-chat` runs Ollama *and* an Open WebUI frontend under one job, for
browser-based chat. `ollama-code-api` runs Ollama alone and exposes its native
API directly - there is no browser page to open, since the client here is an
IDE extension (VS Code's Continue) rather than a person typing into a web UI.
Everything else - loopback-only binding, `OLLAMA_KEEP_ALIVE=-1`, the
`OLLAMA_PULL_PROGRESS:` streaming-pull marker, the warm-up `/api/generate`
call, and log archiving to `$HOME/.lhpc/` before the scratch dir is cleaned up
- is the same pattern as `ollama-chat`, so see
`containers/ollama-chat/README.md` for the full rationale on each of those.

## Security: always tunnel-only, never on the node's real interface

Same trust model as `OllamaChatJob`/`RStudioJob`: `CodeModelJob` sets
`use_localhost = True` unconditionally, and `ollama serve` is bound to
`127.0.0.1` only - never `$HOSTNAME`. Ollama has no authentication of its
own, so gfxlauncher's SSH tunnel is the *only* access gate. This also means
the Continue config snippet the launcher generates needs no API key - the
tunnel already restricts the endpoint to the user who launched the job.

## How it works

`bin/ollama-code-api` runs one service under the SLURM job:

1. **`ollama serve`**, invoked directly (native install, no `--nv`/container
   GPU passthrough needed).
2. Streams `POST /api/pull`'s progress into `OLLAMA_PULL_PROGRESS: <0-100>`
   marker lines, exactly like `ollama-chat` - `CodeModelJob.do_process_output`
   drives the same progress bar UI code, unchanged.
3. **Warms the model up** with an empty-prompt `/api/generate` call so the
   slow first-load cost happens here, not on the user's first completion
   request in the IDE.
4. Prints `CODE_MODEL_URL: http://localhost:$OLLAMA_PORT/` once ready -
   `localhost`, not `$HOSTNAME`, matching the tunnel-rewrite convention
   `jobs.py:386-392` explains.

## Files

- `bin/ollama-code-api` - the wrapper that's actually deployed (also lives at
  `/sw/pkg/ollama/0.32.14/bin/ollama-code-api`, kept in sync manually - copy
  this file over that path after any change here). Invoked by `CodeModelJob`
  as `ollama-code-api --ollama-port=<port> --model "<tag>"`.

## Config

`etc/gfxlauncher.conf`'s `[codemodel]` section (mirrored in
`config.py`/`config_template.py` defaults):

| Variable                  | Purpose                                                                     |
|----------------------------|------------------------------------------------------------------------------|
| `codemodel_module`         | Lmod module providing `ollama`/`ollama-code-api` on `PATH`.                 |
| `codemodel_model`          | Default model tag pre-filled in the job settings dialog.                    |
| `codemodel_models_dir`     | Model cache directory; supports a literal `$HOME` (see `ollama-chat`'s README). |
| `codemodel_popular_models` | Comma-separated list populating the model drop-down in the settings dialog. |

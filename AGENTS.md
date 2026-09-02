# Broken Spleeter — Agent Instructions

> `AGENTS.md` and `CLAUDE.md` are byte-identical mirrors. Any edit to one must be applied
> identically to the other. Verify with `diff AGENTS.md CLAUDE.md` before committing.

## What this project is

An offline experimental audio tool that deliberately abuses Spleeter's pretrained
source-separation models to produce controllable, repeatable model failure as sound-design
material.

**This is its own project, not a Spleeter fork under maintenance.** It began as a fork of
`deezer/spleeter` and does not track upstream. Inherited conventions — code layout, test
structure, packaging choices, CI assumptions — are starting material, not a standard to
preserve. Change them when the project is better for it.

Upstream provenance stays useful for one thing: diagnosing inherited behavior. When
something breaks in code this project did not write, knowing what upstream assumed is
usually the fastest route to the cause.

## Where context lives

- `ENVIRONMENT.md` — **live and authoritative.** Setup, verified commands, platform
  support, known issues. Keep it current; do not duplicate its content elsewhere.
- `PROJECT_SPRINGBOARD.md` — technical and product concept. Design context, **not** a
  specification.
- `WORKFLOW_SPRINGBOARD.md` — workflow and bootstrap assumptions. Questions settled by a
  later session are annotated inline.
- `WINDOWS_INIT_SESSION.md` — spent bootstrap brief, kept as history. Not maintained, not
  guidance.

Both springboards are working hypotheses. Repository evidence outranks either document.

## Instruction precedence

```
latest direct user instruction
  → explicitly named implementation brief, if one is in use
    → AGENTS.md / CLAUDE.md
      → WORKFLOW_SPRINGBOARD.md
        → PROJECT_SPRINGBOARD.md
          → inherited Spleeter documentation
```

A planning document is not a work queue. Treat a brief or plan as an implementation
contract only when the user names it as the source for the current task.

## Inherited baseline

Forked from `deezer/spleeter` at `c8854001ac8acad34a9bc2bd15f28475541828b1`
(Spleeter 2.4.2). Pretrained checkpoints are downloaded on first use from the upstream
`v1.4.0` release into `pretrained_models/` (gitignored).

The unmodified pretrained model is the project's reference state. Experimental behavior
should be an intervention applied to ordinary inference, and should be independently
bypassable.

That reference state covers **model behavior**, not inherited code style or structure.
Protect the former; feel free to change the latter.

## Constraints

- **Do not modernize dependencies as ordinary cleanup.** Changes to Python, TensorFlow,
  packaging, or model loading can alter the baseline behavior this project exists to
  manipulate. Investigate and raise them explicitly.
- **Do not rename the `spleeter` package or distribution.** `spleeter/options.py` resolves
  `--version` through `importlib.metadata.version("spleeter")`.
- **Do not set `GITHUB_REPOSITORY`.** `spleeter/model/provider/github.py` falls back to it
  when locating checkpoints; GitHub Actions sets it automatically, which silently redirects
  model downloads at this fork and fails.
- **`audio_example.mp3` and `audio_example_mono.mp3` are test fixtures**, referenced by
  `tests/test_separator.py` and `tests/test_ffmpeg_adapter.py`. Do not remove them.
- `configs/` is inherited musdb *training* material and is not read at runtime. Inference
  configuration lives in `spleeter/resources/*.json`, loaded via `importlib.resources`.

## Environment

Python **3.11**, TensorFlow **2.12.1**, `ffmpeg` on `PATH`, Poetry **>= 2.0**. The project
venv is `.venv/` at the repository root.

Verified working on Windows 11 as of 2026-09-02. **See `ENVIRONMENT.md` for setup, and
read it before debugging any environment problem** — it records why several pins exist.

Two things that surprise people:

- **`poetry.lock` and `pyproject.toml` carry platform markers that are load-bearing on
  Windows.** `tensorflow-intel` is Windows-only, and `tensorflow-io-gcs-filesystem`
  resolves to 0.31.0 there because 0.32.0 ships no Windows wheels. Removing either marker
  breaks `poetry install` on Windows.
- **No GPU on Windows at this TensorFlow version.** TF dropped native Windows GPU support
  after 2.10, so everything runs on CPU. Restoring it is an open decision with real
  tradeoffs against baseline fidelity — do not resolve it by bumping TensorFlow.

## Verification

Confirmed on Windows 11, 2026-09-02, with the venv activated:

```bash
pytest tests/
black spleeter --check
isort spleeter --check
spleeter separate -p spleeter:2stems -o output audio_example.mp3
```

All pass. `pytest tests/` downloads the 2stems, 4stems and 5stems checkpoints on first
run (~417 MB); `pytest tests/test_separator.py -k 2stems` avoids the larger two.

`--forked` was removed from the pytest `addopts` — `pytest-forked` needs `os.fork()`,
which does not exist on Windows. The suite passes without process isolation; `--forked`
remains available as an opt-in flag on POSIX.

## Working style

- Inspect before redesigning. Read the inherited code, tests, and configuration before
  making broad changes.
- Distinguish findings from decisions. Surface consequential choices for acceptance rather
  than adopting them silently.
- Prefer reversible exploration. Prototyping is welcome; keep exploratory work easy to
  identify and discard.
- Do not over-preserve upstream structure. Inherited organization is kept only where it
  remains useful.

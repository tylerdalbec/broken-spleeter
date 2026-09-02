> **Status: completed and superseded — 2026-09-02. Retained as history, not guidance.**
>
> This was the brief for the first Windows bootstrap session. That session ran to
> completion; every stage below was carried out. The document is preserved unchanged
> as a record of what was asked and why, and to make the original assumptions
> available when diagnosing environment problems later.
>
> **It is not project documentation and is not maintained.** The outcomes it produced
> live in `ENVIRONMENT.md`, which is the canonical and current reference for setup,
> verification, and known issues. Where the two disagree, `ENVIRONMENT.md` is correct.
>
> Two assumptions in the text below turned out to be wrong and are corrected in
> `ENVIRONMENT.md`: the inherited `poetry.lock` could not install on Windows at all,
> and the inherited pytest configuration could not run on Windows. Both were fixed
> during the session.

---

This is the first local Windows bootstrap session for Broken Spleeter.

Read first:
1. AGENTS.md/CLAUDE.md (they are mirrored)
2. WORKFLOW_SPRINGBOARD.md
3. PROJECT_SPRINGBOARD.md

For this session, do not implement Broken Spleeter features, redesign architecture,
modernize dependencies, or perform general cleanup.

The purpose of this session is to establish the inherited Spleeter environment
incrementally and determine exactly where it works or fails on this Windows machine.

Work in explicit stages. Do not skip ahead. If a stage fails, diagnose that failure
before moving to the next stage. Do not modify dependency constraints or source code
to make a failing stage pass without discussing the finding with me first.

Stage 1 — Repository sanity

Verify:
- git status
- current branch
- configured remotes
- current HEAD commit

Confirm that the checkout is clean and corresponds to the Broken Spleeter bootstrap.

Stage 2 — Interpreter

Inspect pyproject.toml and confirm the inherited Python and TensorFlow constraints.

The current expectation is that Python 3.11 is the first baseline candidate because
TensorFlow 2.12.1 and the project metadata require Python <3.12.

First inspect which Python interpreters are already available on this Windows machine.

Do not create a virtual environment until we have confirmed which Python 3.11
interpreter will be used.

If Python 3.11 is not installed, recommend the smallest practical way to install or
manage it without changing my system/default Python installation. Explain the tradeoffs
before making that choice.

Verify the selected interpreter explicitly with commands such as:
- where.exe python
- py -0p, if the Python launcher is available
- <selected interpreter> --version

Stage 3 — Project virtual environment

Only after Python 3.11 is verified, create a project-local .venv using that exact
interpreter.

Activate it and verify:
- python --version
- where.exe python
- python -c "import sys; print(sys.executable)"

Do not install project dependencies yet.

Stage 4 — Native prerequisite

Check whether FFmpeg is available:
- ffmpeg -version
- where.exe ffmpeg

If it is missing, stop and discuss the cleanest Windows installation strategy before
continuing.

Stage 5 — Dependency tooling

Inspect poetry.lock and pyproject.toml.

Determine:
- whether Poetry is already installed
- which Poetry version is present
- whether using the inherited Poetry workflow is practical with this repository

Do not regenerate poetry.lock.

Do not upgrade or loosen dependencies.

Before installing anything, tell me exactly which installation command you recommend
and why.

Stage 6 — Dependency installation

Install the inherited dependency set into the verified Python 3.11 .venv.

If dependency resolution or installation fails, stop and diagnose the exact conflict.
Do not modernize packages as a workaround.

After installation, verify at minimum:
- python version
- TensorFlow import and version
- NumPy import and version
- Spleeter import
- installed spleeter package metadata/version

Stage 7 — CLI smoke test

Only after imports succeed, verify that the inherited Spleeter CLI starts normally.

Do not run separation yet.

Confirm that CLI startup itself is functional.

Stage 8 — Ordinary inference

Inspect the model-loading path and pretrained-model location before first inference.

Then run the smallest practical unmodified 2-stem separation using one of the existing
repository audio fixtures.

Record:
- exact command
- whether model download occurs
- where checkpoints are cached
- output location
- whether the render succeeds

Do not introduce any Broken Spleeter modifications.

Stage 9 — Tests

Only after ordinary inference succeeds, inspect the inherited tests and choose a small
baseline subset that exercises the functionality we just verified.

Run that subset first.

Only consider a wider test run after the small baseline is understood.

At the end, summarize verified facts only:
- exact Python interpreter/version
- how it was selected or installed
- exact .venv creation and activation commands
- FFmpeg location/version
- Poetry/dependency installation procedure
- installed TensorFlow/Spleeter versions
- model download/cache behavior
- successful baseline Spleeter command
- tests run and their results
- any failures or Windows-specific behavior
- documentation changes that now appear justified
- unresolved decisions requiring my input

Do not update AGENTS.md or CLAUDE.md merely because a command seems likely to work.
Only propose changes based on commands actually verified in this session, and keep
those two files byte-identical if I approve edits.
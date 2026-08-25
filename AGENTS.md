# Broken Spleeter — Agent Instructions

> `AGENTS.md` and `CLAUDE.md` are byte-identical mirrors. Any edit to one must be applied
> identically to the other. Verify with `diff AGENTS.md CLAUDE.md` before committing.

## What this project is

An offline experimental audio tool that deliberately abuses Spleeter's pretrained
source-separation models to produce controllable, repeatable model failure as sound-design
material. A fork of `deezer/spleeter`, not tracking upstream.

## Where context lives

- `PROJECT_SPRINGBOARD.md` — technical and product concept. Design context, **not** a
  specification.
- `WORKFLOW_SPRINGBOARD.md` — workflow and bootstrap assumptions.

Both are working hypotheses. Repository evidence outranks either document.

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

`tensorflow` is pinned to `2.12.1`, which constrains the project to **Python 3.11 or
older**. `ffmpeg` must be on `PATH`. No local environment has been established or verified
yet; that is the Windows workstation session's responsibility.

## Verification

No verified baseline commands exist yet. The inherited upstream CI used:

```bash
poetry install
poetry run pytest tests/
poetry run black spleeter --check
poetry run isort spleeter --check
```

Treat these as unconfirmed. Update this section once a session has actually run them —
do not present them as required gates before that.

## Working style

- Inspect before redesigning. Read the inherited code, tests, and configuration before
  making broad changes.
- Distinguish findings from decisions. Surface consequential choices for acceptance rather
  than adopting them silently.
- Prefer reversible exploration. Prototyping is welcome; keep exploratory work easy to
  identify and discard.
- Do not over-preserve upstream structure. Inherited organization is kept only where it
  remains useful.

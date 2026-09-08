# Changelog

Dated entries, newest first.
This project has no releases and does not use semantic versioning; entries are grouped by working session.

Historical entries are records and are not rewritten.
`ROADMAP.md` holds intent; this file holds what actually happened.

> The inherited `deezer/spleeter` changelog was removed at bootstrap and remains in Git history.
> This file is a fresh document that reuses the filename.

---

## 2026-09-08 — Inference path mapped, documentation scaffold

No source changes.
Reconnaissance and documentation only.

### Findings

- **The mask is already a first-class tensor.**
  `EstimatorSpecBuilder` exposes `masks`, `masked_stfts`, `model_outputs` and `stft_feature` as lazy cached properties.
  Fetched live at `(frames, 2049, 2)` float32 in `[0.0, 1.0]` per instrument.
- **A direct-session inference path exists and is bit-identical to the estimator path.**
  `Separator._get_builder()`, `_get_features()` and `_get_session()` are unreachable from `separate()`.
  Built by hand, restored with a plain `Saver`, they produce byte-identical output to `tf.estimator`, so bypassing the estimator costs nothing in baseline fidelity.
- **Renders are bitwise deterministic across processes.**
  No `tf.config.experimental.enable_op_determinism()` needed, and its speed cost is avoided.
  Verified at both the array and the written-WAV level; recorded with a manual re-check procedure in `ENVIRONMENT.md` §3.4.
- **Weight and BatchNorm corruption needs no checkpoint rewriting.**
  148 global variables, 96 of them BatchNorm (`gamma`, `beta`, `moving_mean`, `moving_variance`), assignable in-session.

### Added — `broken/`, the mask interception mechanism (roadmap A2)

First Broken Spleeter source.
Nothing under `spleeter/` was modified.

- `broken.BrokenSeparator` owns its own `tf.Graph` and session instead of going through `tf.estimator`.
  Graph construction happens inside an explicit graph context, so eager execution is not disabled process-wide and several separators can coexist — which later ensemble work needs.
- `broken.builder.InterceptingSpecBuilder` splices a `placeholder_with_default` between the estimated mask and reconstruction.
  Unfed, it passes the model's own estimate through, so **bypass is structural rather than a code path that has to be kept honest.**
- `broken.masks.time_shift` — the first corruption operation, proving the NumPy round-trip contract.
- Fed masks are validated before reaching reconstruction, against the estimated masks when those are on hand.
  The frame axis is statically unknown in the graph, so a truncated mask cannot be caught by tensor shape alone.

Verified: bypass reproduces the recorded baseline WAV hashes exactly; an explicit no-op mask function round-trips identically; corruption changes output and repeats deterministically; malformed masks are rejected with legible errors.

**Feeding a mask prunes the U-Net from the render** — 0.33 s against 3.42 s for `audio_example.mp3`.
TensorFlow skips ops whose consumers are all fed, so a sweep that analyzes once and re-renders many corruptions pays roughly a tenth per variation.
This makes NumPy-side corruption cheaper than the in-graph alternative rather than more expensive.

### Documentation

- Added `CHANGELOG.md` and `ROADMAP.md`.
- Added `ENVIRONMENT.md` §3.4 recording render determinism and the periodic manual check.
- Resolved answerable questions inline in `PROJECT_SPRINGBOARD.md` §17.
- Listed the new documents in `AGENTS.md` / `CLAUDE.md`, kept byte-identical, along with the `BRIEF_<description>.md` convention.
- Added `BRIEF_MASK_MANIPULATION.md`, specifying the remainder of roadmap A2.
  Written to be self-contained, since the implementer may be a different agent or model.
- Made two facts durable in the repository that had been held only in agent memory:
  the requirement to re-verify a TensorFlow pin change against a *fresh* venv, since an already-satisfied environment passes without exercising platform selection (`ENVIRONMENT.md` §5);
  and that GPU acceleration is an actively wanted feature with hardware already present, rather than a shelved one (`ROADMAP.md`).

---

## 2026-09-02 — Windows development environment

Commits `08ed4f2`, `00f5d3c`.

- Established a reproducible Windows environment: Python 3.11.16 via uv in a project-local `.venv`, Poetry >= 2.0 as an isolated tool, FFmpeg from winget.
  The system Python 3.14.3 was left untouched.
- Added platform markers to `pyproject.toml` and `poetry.lock` making Windows a first-class target.
  The inherited lock could not install on Windows at all; `tensorflow-intel` is Windows-only and `tensorflow-io-gcs-filesystem` resolves to 0.31.0 there because 0.32.0 ships no Windows wheels.
  These markers are load-bearing.
- Relaxed the mp3 duration assertion in `tests/test_ffmpeg_adapter.py` to a tolerance.
  Newer FFmpeg accounts for LAME encoder delay and padding, a ~1704-sample difference at 44.1 kHz.
- Removed `--forked` from the pytest `addopts`; `pytest-forked` requires `os.fork()`, which Windows lacks.
- Verified the full inherited test suite, ordinary 2stems separation, and pretrained model download and caching.
- Added `ENVIRONMENT.md` as the live environment reference, and `WINDOWS_INIT_SESSION.md` as spent bootstrap history.
- Established Markdown semantic-line-break conventions and rewrote existing documents to follow them.

**Left open:** GPU support.
TensorFlow dropped native Windows GPU support after 2.10, so everything runs on CPU.

---

## 2026-08-25 — Bootstrap from the inherited fork

Commit `7cf2dba`.

- Reoriented the untouched `deezer/spleeter` fork into a Broken Spleeter project tree.
- Removed inherited publication, packaging, release and community infrastructure: `.github/`, `docker/`, `conda/`, `images/`, the JOSS paper, the upstream changelog, and the Colab demo notebook.
  All remain available through Git history and the upstream repository.
- Preserved everything involved in ordinary Spleeter execution and testing, including both `audio_example` mp3 files, which are test fixtures rather than samples.
- Added `PROJECT_SPRINGBOARD.md`, `WORKFLOW_SPRINGBOARD.md`, byte-identical `AGENTS.md` / `CLAUDE.md`, and a minimal README.
- Recorded provenance: forked from `deezer/spleeter` at `c8854001ac8acad34a9bc2bd15f28475541828b1`, Spleeter 2.4.2.
- Dependency definitions deliberately untouched.

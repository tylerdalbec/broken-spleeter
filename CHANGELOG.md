# Changelog

Dated entries, newest first.
This project has no releases and does not use semantic versioning; entries are grouped by working session.

Historical entries are records and are not rewritten.
`ROADMAP.md` holds intent; this file holds what actually happened.

> The inherited `deezer/spleeter` changelog was removed at bootstrap and remains in Git history.
> This file is a fresh document that reuses the filename.

---

## 2026-10-12 — Agent instruction files no longer mirrored

### Changed — Agent instructions

- `AGENTS.md` is now the single source of agent instructions; `CLAUDE.md` imports it with `@AGENTS.md` instead of mirroring it byte-for-byte.
- Added a `## Claude Code Specific` section to `CLAUDE.md` covering the Claude desktop app's AppData redirect and the Windows platform-marker details.
- Updated the `README.md` documentation table to match.
- Annotated `WORKFLOW_SPRINGBOARD.md` §`AGENTS.md` and `CLAUDE.md` as superseded.

---

## 2026-09-13 — Mask manipulation slice complete (roadmap A2)

Implemented `BRIEF_MASK_MANIPULATION.md`.
Delivers controllable, reproducible mask corruption operations, JSON recipe representation, CLI entry points, and pure NumPy unit tests.

### Added — Mask operations (`broken/masks.py`)

- Implemented eight pure float32 mask operations: `contrast`, `gain_bias`, `threshold`, `quantize`, `time_shift`, `freq_shift`, `complement_blend`, and `noise`.
- Preserved values outside `[0.0, 1.0]` across operations; clamping is optional and applied only at the end of the recipe pipeline.
- Implemented edge-wrapping (`wrap=True`) and zero-fill (`wrap=False`) displacement semantics for both time and frequency shifts, handling shifts exceeding axis lengths.
- Added input validation ensuring all operations reject non-positive gammas, negative softness, levels below 2, and non-integer shift or quantization parameters.

### Added — Recipe representation (`broken/recipe.py`)

- Structured dataclasses (`MaskOp`, `MaskConfig`, `Recipe`) with bidirectional JSON serialization and file I/O helpers (`load_recipe`, `save_recipe`).
- Preserves explicit operation ordering and rejects unknown operation names or parameters with informative errors.
- Added deterministic seeding: explicit operation-level seeds win; otherwise seeds derive deterministically from `recipe.seed` and the operation's chain index.
- Structural bypass enforcement: recipes with `enabled: false` or an empty operations list bypass mask feeding entirely.

### Added — CLI interface (`broken/__main__.py`)

- Invoked via `python -m broken` without modifying package console scripts.
- `render INPUT --recipe R.json -o DIR`: renders audio through the specified recipe.
- `sweep INPUT --op OP --param NAME --values V1,V2,... -o DIR [--recipe BASE.json]`: sweeps parameter values, executing `estimate_masks` once and pruning the U-Net for subsequent variations (~0.4 s per variation on CPU).
- Millisecond conversion support via `--unit ms` for `time_shift`, converting to frame counts using the model configuration's `frame_step` and sample rate with warnings for collapsed frame values.
- `verify-bypass INPUT`: renders uncorrupted baseline audio via structural bypass and compares SHA-256 stem checksums against reference values.

### Added — Verification & tests (`tests/test_broken_masks.py`)

- 22 fast unit tests verifying arithmetic correctness, float32 dtypes, input immutability, boundary shifts, noise seeding, recipe serialization round-trips, and error validation.
- All 22 tests pass in ~3.5 s without requiring model downloads or network access.
- Confirmed `verify-bypass audio_example.mp3` bit-identically reproduces the recorded CPU baseline hashes in `ENVIRONMENT.md` §3.4.

### Fixed — review against the brief

- A `noise` op without its own seed serialized as `"seed": null`, which the loader rejected, so every recipe emitted by a noise sweep failed in `render`.
  `seed` is now accepted only on `noise`, and is omitted when absent.
- `noise` drew a float32 normal stream, which differs from the brief's default float64 draw for the same seed.
  It now matches §5.1, before any noise recipes were kept.
- Millisecond sweep values resolving to the same frame count wrote to the same directory, the later overwriting the earlier.
  Labels now carry the requested value, e.g. `time_shift.frames=0_10ms`, and any sweep whose values would still produce duplicate labels is rejected before rendering.
- Sweeping onto a base recipe with `mask.enabled: false` silently rendered bypass under corrupted labels; it now fails with an error.

### Added — closing gaps in the brief

- `sweep --set NAME=VALUE`, repeatable, holds other parameters of the swept op fixed.
  Without it, `time_shift` with `wrap=true`, `threshold.softness` and `noise.seed` could not be swept at all.
  Booleans accept only `true` or `false`, and every variation's op is validated before any audio is loaded.
- Recipes carry an optional `"audio": {"offset", "duration"}` block, written by `sweep`, so an emitted recipe re-renders the same excerpt.
  Explicit `--offset` / `--duration` flags override it.
- `tests/test_broken_cli.py` covers argument parsing and the sweep checks that run before a model is built.

### Documentation

- Split verification into a fast tier (`tests/test_broken_*.py` plus lint, about 5 seconds) and the full suite (about 4 minutes), recorded in `AGENTS.md` / `CLAUDE.md` and `ENVIRONMENT.md` §3.3.
  The full suite is for changes upstream of inference; the policy question is parked in roadmap B3.

### Observations for A3

From the implementer's brief §8 report, checked against the code, with corrections noted.
None of this has been listened to; these are things to listen for, not findings.

- **Noise is identical across stems.**
  A `noise` op resolves one seed and applies it to every stem's mask, so vocals and accompaniment receive the same realization.
  Independent noise would need a per-stem seed, for example derived from the stem name.
  Which is more useful is undecided.
- **Unclamped values reach reconstruction.**
  Mask values above 1 boost their bins and can push a stem past full scale, where WAV output is likely to clip (not verified).
  Negative values invert the phase of the affected bins.
- **Everything above about 11 kHz is already zero in the mask.**
  The 2stems model estimates the lower 1024 of 2049 bins, and `mask_extension: "zeros"` fills the rest.
  `complement_blend` near 1, or a positive `gain_bias` bias, opens that band in every stem.
- **Frequency shift interacts with that zero band**, which the implementer's report missed; it expected upward wrap to fold high-frequency content into the lows.
  Positive shift: the lowest bins go silent and the mask slides up into the band above 11 kHz.
  For shifts up to 1025 bins, `wrap=true` and `wrap=false` produce identical masks, since what wraps around is the zero band.
  Negative shift: the zero band slides down, cutting the top of the spectrum below 11 kHz; with `wrap=true` the lowest bins' mask values land above 11 kHz.
- **Frequency bins are linear, about 10.8 Hz each**, so a fixed bin shift is a large interval in the bass and a small one in the treble.
- **Time shift fill modes.**
  Zero fill gates the start of the file (positive) or the end (negative); wrap folds the end onto the start or the reverse.
  Resolution is one frame, about 23.2 ms at 2stems settings.
- **The soft threshold has hard corners** at the ends of its linear ramp; the implementer expects audible chatter compared with a smooth curve such as a sigmoid.
- **Contrast with gamma below 1 lifts low mask values steeply**, likely raising the bleed Spleeter leaves in quiet regions.

### Not done

- `broken` is still not declared in `pyproject.toml`; the brief kept packaging files untouched.
  Carried under the PEP 621 item in `ROADMAP.md`.

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

# Roadmap

Intent, not commitment.
Ordering changes when experiments reveal a more productive direction — that is the expected behavior for this project, not a failure of planning.

`CHANGELOG.md` records what actually happened.
`PROJECT_SPRINGBOARD.md` holds the design context each project item derives from; section references point there.

Item IDs are stable and are not reused once retired, so briefs and commit messages can cite them.

---

## Workstream A — Project

The experimental substance.

### A1 — Baseline and inference map — **done**

Environment, verified ordinary separation, inherited test suite, and the map of where interventions can attach.
Completed 2026-09-02 and 2026-09-08.

### A2 — Mask manipulation slice — **done**

The first vertical slice, script-driven.
Covers springboard §6.1 and §18 experiments 1–3.
Deliberately ahead of the GUI: controls cannot be designed for knobs nobody has heard yet.

**Landed 2026-09-08** — the interception mechanism.
`broken/` owns its graph and session, splices a feedable tensor into the mask stage, and validates fed masks before they reach reconstruction.
Bypass is bit-identical to the recorded baseline and structural rather than asserted.

**Landed 2026-09-13** — the remainder of the slice (`BRIEF_MASK_MANIPULATION.md`).
- Eight mask operations in `broken/masks.py`: contrast, gain/bias, threshold, quantize, time shift, frequency shift, complement blend, and Gaussian noise.
- Pure float32 NumPy array contract preserving un-clamped values until final recipe stage.
- Recipe representation in `broken/recipe.py` with ordered operations, validation, JSON serialization, and deterministic seeding.
- CLI in `broken/__main__.py` (`python -m broken`) with `render`, `sweep`, and `verify-bypass`.
- Sweep runner reuses a single `estimate_masks` analysis across all variations, cutting per-variation render time to ~0.4 s on CPU.
- Unit tests in `tests/test_broken_masks.py` covering operations, edge cases, shifts, seeding, and recipe round-trips.

Declaring `broken` in the `pyproject.toml` `packages` list was not done, since the brief kept packaging files untouched.
It is carried under the PEP 621 migration item below.

### A3 — Musical triage

Listen to the A2 sweeps and decide which corruption families deserve first-class treatment.
This is a judgment call about sound, not an engineering task, and it is the point of A2.

Depends on B2.

Things to listen for are recorded in `CHANGELOG.md` under 2026-09-13, "Observations for A3".
One of them is an open design question rather than a sound: a `noise` op applies the identical realization to every stem.
Whether stems should get independent noise is best settled by ear.

Sweep and listening work needs only the fast test tier in `AGENTS.md`, not the full suite.

### A4 — Checkpoint, weight and BatchNorm corruption

Springboard §6.2 and §6.3.
Unblocked by the A1 finding that all 148 variables are addressable in-session, so mutation is assignment at load time rather than checkpoint rewriting.

### A5 — Activation hooks

Springboard §6.4.
The first item requiring real changes to `spleeter/model/functions/unet.py`, which builds from Keras layers with no named intermediate handles.

Triggers B4.

### A6 — Recursive processing

Springboard §6.7.
Cheap once A2 exists, since recursion is a driver-level loop over an existing render path.

### A7 — Multi-model disagreement and ensembles

Springboard §6.6 and §6.8.
Multiplies render cost, so it wants A2's preview loop to be tolerable first.

### A8 — Reconstruction and phase abuse

Springboard §6.9 and §6.10.
A different artifact class from mask corruption and largely independent of A4–A7.

### A9 — GUI

Springboard §4, §8, §12.
Starts once the parameter set is known from A3 onward.
The process-separation design in §12 should be re-validated against whatever A2 actually builds.

---

## Workstream B — Infrastructure

Supporting work. Kept deliberately small; added only when friction earns it.

### B1 — Documentation scaffold — **done**

`CHANGELOG.md`, `ROADMAP.md`, determinism recorded in `ENVIRONMENT.md`, springboard §17 resolved inline.
Completed 2026-09-08.

### B2 — Test audio fixtures

`audio_example.mp3` is 10.88 seconds of one thing.
Judging whether a corruption is musically productive needs material chosen to provoke failure — dense mixes, solo sources, material Spleeter already handles badly.

Tyler's picks; not an agent decision.
Blocks A3 meaningfully, and does not block A2.

### B3 — Verification policy

The inherited suite tests ordinary Spleeter, not deliberate failure.
What a passing test should mean once corruption exists is unsettled, as is whether render verification stays manual.

**Interim test split, 2026-09-13.**
The full suite takes about 4 minutes, nearly all of it inherited tests of ordinary Spleeter that `broken/` work cannot affect.
Agents run a fast tier by default — the `tests/test_broken_*.py` files plus lint, about 5 seconds — and the full suite only when something upstream of inference changes.
The rule lives in `AGENTS.md`.
It is convention, not tooling: `pytest tests/` still runs everything.

Open: whether to enforce the split with a pytest marker or default `addopts` so the slow tests become opt-in, and whether any milestone, such as marking a roadmap item done, should require a full run.

The original trigger — A2 landing — has fired.
**Revisit when** the full suite's cost or a wrongly skipped full run causes real friction, or when a corruption exists whose correctness is not obvious by listening.

### B4 — Architecture reference

Deferred until A5.
The inference map currently fits as resolved questions in springboard §17; it stops fitting when instrumented layers need describing.

---

## Deferred

Parked with a reason and a condition for revisiting.
None of these gate anything above.

### GPU acceleration

**This is a wanted feature, not a shelved one.**
Tyler has an RTX 3080 Ti and wants the finished application to use it, stated 2026-09-02 explicitly as a later goal rather than a baseline blocker.
The hardware is present and idle; only the pin stands in the way.

TensorFlow dropped native Windows GPU support after 2.10, so the 2.12.1 pin means CPU only regardless of installed hardware.
Restoring it means choosing between:

- **WSL2 with CUDA** — keeps TF 2.12.1 and the exact baseline, but complicates the GUI and audio-device plans in springboard §11.
- **A newer TensorFlow** — native GPU returns, but the pretrained-model reference state has to be re-validated.
- **`tensorflow-directml-plugin`** — native Windows and vendor-neutral, but pinned to old TF versions and poorly maintained.

**Do not bump TensorFlow to chase this**, and do not treat it as a dependency upgrade.
It trades against baseline fidelity, which makes it Tyler's call rather than an implementation detail — present it priced, as above.

**Revisit when** render times make the A2 preview loop painful, when the GUI in A9 starts being designed, or when a baseline-fidelity re-validation is being done deliberately for another reason.

### Continuous integration

GitHub Actions sets `GITHUB_REPOSITORY` automatically, which `spleeter/model/provider/github.py` falls back to when locating checkpoints — silently redirecting model downloads to this fork, where they do not exist.
A stock workflow file is actively harmful here, and a single developer on one machine gets little from CI.

**Revisit when** a second machine or contributor exists, and handle the environment variable deliberately.

### Packaging and distribution

Nothing to distribute.
**Revisit when** someone other than Tyler needs to run this.

### PEP 621 `[project]` migration

`pyproject.toml` uses legacy `[tool.poetry]` metadata.
Poetry 2.x supports it; `poetry check` warns per field.
Migration changes how the distribution name, version, extras and console scripts are declared, and `spleeter --version` resolves through `importlib.metadata.version("spleeter")`.

`broken` is not declared in the `packages` list either.
It imports only because the editable install of `spleeter` puts the repository root on `sys.path`, which is incidental and would not survive a built distribution.
`python -m broken` from the repository root works regardless, since the working directory is on `sys.path`.
Declare it as part of this migration rather than as a separate packaging change.

**Revisit when** the warnings become real friction, or packaging is needed.
Verification steps are recorded in `ENVIRONMENT.md` §7.

### Linux and macOS verification

Unverified since the fork.
The lock resolves and upstream CI exercised them, but no session has run them here.

**Revisit when** cloud sessions start running tests, or a second machine appears.

### Upstream synchronization

Not planned.
The project does not track `deezer/spleeter`; provenance stays useful only for diagnosing inherited behavior.

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

### A2 — Mask manipulation slice — **in progress**

The first vertical slice, script-driven.
Covers springboard §6.1 and §18 experiments 1–3.
Deliberately ahead of the GUI: controls cannot be designed for knobs nobody has heard yet.

**Landed 2026-09-08** — the interception mechanism.
`broken/` owns its graph and session, splices a feedable tensor into the mask stage, and validates fed masks before they reach reconstruction.
Bypass is bit-identical to the recorded baseline and structural rather than asserted.

**Remaining** — specified in `BRIEF_MASK_MANIPULATION.md`, and mechanical enough to delegate:

- the rest of the mask operations — contrast/exponent, gain/bias, threshold, quantization, frequency displacement, inversion and complement blending
- a recipe representation with explicit seeding, serialized to JSON
- a CLI entry point and a sweep runner for §18 experiments 1–3
- turning the spike's bypass check into a repeatable verification, which overlaps B3
- declaring `broken` in the `pyproject.toml` `packages` list
  It currently imports only because the editable install of `spleeter` puts the repository root on `sys.path`, which is incidental and would not survive a built distribution.
  Touching packaging is a deliberate change, not cleanup — see the deferred PEP 621 item.

Sweeps should reuse one analysis via `BrokenSeparator.estimate_masks` and the `masks=` argument.
Feeding a mask prunes the network from the render, so a variation costs roughly a tenth of a full pass.

### A3 — Musical triage

Listen to the A2 sweeps and decide which corruption families deserve first-class treatment.
This is a judgment call about sound, not an engineering task, and it is the point of A2.

Depends on B2.

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

Revisit when A2 lands and there is something whose correctness is not obvious by listening.

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

**Revisit when** the warnings become real friction, or packaging is needed.
Verification steps are recorded in `ENVIRONMENT.md` §7.

### Linux and macOS verification

Unverified since the fork.
The lock resolves and upstream CI exercised them, but no session has run them here.

**Revisit when** cloud sessions start running tests, or a second machine appears.

### Upstream synchronization

Not planned.
The project does not track `deezer/spleeter`; provenance stays useful only for diagnosing inherited behavior.

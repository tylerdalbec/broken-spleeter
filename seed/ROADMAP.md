# Roadmap

Intent, not commitment.
Ordering changes when listening reveals a more productive direction; that is the expected behavior for this project.

`CHANGELOG.md` records what actually happened.
`CONCEPT.md` holds the design context each item derives from; section references point there.

Item IDs are stable and are not reused once retired.
IDs of the form `A1` or `B2` in carried code or old notes refer to the archived prototype's roadmap, not this one.

---

## Workstream P — Project

### P0 — Initialize the repository

Tyler's actions, on the workstation.

- Copy this seed into a new folder and run `git init`.
- Settle the project name, or keep the working title.
- Choose a license.
- Archive `tylerdalbec/broken-spleeter` on GitHub.

### P1 — Environment and stock baseline

Get an unmodified `htdemucs` render running on the GPU and record everything in `ENVIRONMENT.md`.

- Python and a PyTorch build with CUDA, installed and verified on Windows 11.
- `demucs` installed; `torch` and `demucs` declared in `pyproject.toml` with the wheel index pinned.
- Render a region of a full mix with the stock model.
- Measure render time for a 10 to 20 second region.
- Run the same render twice and compare, with and without PyTorch's deterministic mode, and record the speed cost.

Done when a fresh clone can reproduce the render from documented steps.

### P2 — Engine core

One function that takes audio and a recipe and returns stems, with the model resident between calls.
Covers `CONCEPT.md` sections 6 and 8.

- Region rendering.
- Seeded randomness everywhere, including the global `random` state `demucs.apply.apply_model` uses for shifts.
- The tether stage, with both mask derivations.
- The existing mask operations attached at full tether.
- The heard/filtered split, with a first few transforms and cross-audio rendering (sections 9.1 and 9.2).
- Caching of model output, so tether and mask changes do not re-run the network.
- A recipe schema that describes all of the above; the carried version 1 schema is mask-only.

Keep this thin.
It exists to make P3 and P4 possible, not to be complete.

### P3 — Minimal GUI

The audition surface from `CONCEPT.md` section 10, at its minimum: load, region, extremity, tether, render, A/B, image, export.

This comes before most interventions on purpose.
The prototype stalled because listening was the expensive step.

### P4 — Intervention spikes

Breadth-first and shallow, covering `CONCEPT.md` sections 9.3 to 9.5.
Each spike is small, has an identity setting at zero, and is exposed in the GUI as soon as it makes sound.

- Skip-connection gain per level.
- Time shift and channel permutation in the latent.
- Each branch soloed, and the difference between branches.
- Weight blend toward a perturbed copy, with structured and Gaussian variants.
- Variance across time-shifted passes.

No validation layers, recipe polish, or test suites at this stage beyond the identity check.

### P5 — Musical triage

Listen, and decide which families deserve first-class treatment.
A judgment about sound, made by Tyler, and the point of P2 through P4.

Depends on I1.

### P6 — Build out the survivors

Proper parameter ranges, recipe support, tests, and GUI controls for whatever P5 keeps.
Drop the rest.

---

## Workstream I — Infrastructure

Kept deliberately small; added only when friction earns it.

### I1 — Test audio set

Material chosen to provoke failure: dense full mixes, solo sources, loops, non-musical audio.
Tyler's picks, not an agent decision.
Keep it out of Git; `audio/` is ignored.

Blocks P5, and is useful from P1 onward.

### I2 — Verification policy

Interim rule, recorded in `AGENTS.md`: the fast test tier is the default, and every intervention carries one test that its zero setting is the identity.

Open: what, if anything, should be asserted about the sound of a deliberately broken render.

**Revisit when** an intervention exists whose correctness is not obvious by listening.

---

## Deferred

Parked with a reason and a condition for revisiting.
None of these gate anything above.

### Spleeter weight port

`CONCEPT.md` section 7.
**Revisit when** listening to Demucs suggests that a weaker, mask-based, per-stem model has a character worth adding.

### Other separator architectures

**Revisit when** P5 shows that variety between models matters more than depth on one.

### Recursion, phase experiments, gradient-based methods

`CONCEPT.md` sections 9.7 to 9.9.
**Revisit when** P5 is done and the cheaper families have been heard.

### Batch harvesting

Processing a sample library across recipes and seeds, and exporting only regions that score high on some artifact metric.
**Revisit when** a recipe exists that is worth running at scale.

### Packaging, distribution, continuous integration

Nothing to distribute, one developer, one machine.
**Revisit when** someone other than Tyler needs to run this, or a second machine appears.

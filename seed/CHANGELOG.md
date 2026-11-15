# Changelog

Dated entries, newest first.
This project has no releases; entries are grouped by working session.

Historical entries are records and are not rewritten.
`ROADMAP.md` holds intent; this file holds what actually happened.

---

## 2026-11-15 — Seeded from the Broken Spleeter prototype

No code written.
A review of the prototype, a change of direction, and the seed for this repository.

### Decided

Accepted by Tyler during the review session.

- **Stem-separation abuse is the point; Spleeter is not.**
  Divergence from any upstream project does not matter.
- **PyTorch replaces TensorFlow**, and `htdemucs` from the `demucs` package is the first model.
  A port of the Spleeter weights is optional and deferred.
- **A new repository** instead of rebuilding inside the `deezer/spleeter` fork.
- **Extremity and tether as global controls**, so that how weird a result is and how recognizable it stays are chosen separately.
- **A minimal GUI before most interventions**, with PySide6 as the recommended toolkit.
- **Interventions built breadth-first and shallow**, with engineering effort going only to what survives listening.

The reasoning is in `CONCEPT.md`, sections 5 to 7 and 12.

### Carried over from `tylerdalbec/broken-spleeter`

Copied unchanged from that repository at commit `24c0681`.

- `broken/masks.py` — eight mask operations, pure NumPy.
- `broken/recipe.py` — the version 1 recipe schema, validation, and seed derivation.
  It still names `spleeter:2stems` as its default model and describes mask operations only.
  It is starting material for the schema in roadmap item P2, not a commitment.
- `tests/test_broken_masks.py` — 27 tests covering both.
- `.flake8`, and the documentation conventions in `AGENTS.md`.

`broken/__init__.py` was rewritten to export only the recipe helpers.

### Not carried over

- The TensorFlow separator and graph builder, the command-line interface, and its tests.
  The sweep design they implemented — analyze once, re-render many variations — survives as an idea in `CONCEPT.md` section 10.
- The inherited `spleeter` package, its tests, configurations, and audio fixtures.
- The Poetry lock and its TensorFlow platform markers.
- The prototype's planning documents and its environment record.

### Verified

- The carried tests pass on Python 3.13 and NumPy 2.x.
- Facts about the `demucs` 4.1.0 package and the `htdemucs` forward pass, by reading its source.

Details and limits are in `ENVIRONMENT.md` section 1.

### Not done

- Nothing has been listened to.
- No model has been run.
- The Windows environment is not set up; roadmap item P1.

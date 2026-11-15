# Broken Stems — Agent Instructions

> `AGENTS.md` is the single source of agent instructions.
> `CLAUDE.md` imports it with `@AGENTS.md` and adds only a Claude Code-specific section.
> Edit shared instructions here, not in `CLAUDE.md`.

"Broken Stems" is a working title; see `ROADMAP.md` P0.

## What this project is

An offline experimental audio tool that deliberately abuses pretrained stem-separation models to produce controllable, repeatable model failure as source material for sampling.

The end product is a small desktop GUI with the most interesting model parameters exposed, built for fast iteration by ear.

It is a reboot of an earlier prototype, Broken Spleeter (`tylerdalbec/broken-spleeter`, archived).
That repository is history and a reference for Spleeter's internals, nothing more.
`CONCEPT.md` section 12 records why the reboot happened; read it before proposing process.

## Where context lives

- `CONCEPT.md` — the technical and product concept.
  Design context, **not** a specification.
  A working hypothesis; repository evidence and listening results outrank it.
- `ROADMAP.md` — **live.** What is planned, what is deferred and why.
  Deferred items carry a revisit trigger.
  Item IDs are stable and citable, and are not reused once retired.
- `ENVIRONMENT.md` — **live and authoritative** for setup, verified commands, and platform facts.
  It distinguishes verified facts from intentions; keep that distinction.
- `CHANGELOG.md` — **record.** What actually happened, newest first, grouped by session.
  Historical entries are not rewritten.

When a session changes something worth remembering, record it where it belongs rather than in a new file:
a verified environment fact goes in `ENVIRONMENT.md`, a plan or a deferral goes in `ROADMAP.md`, and what happened goes in `CHANGELOG.md`.

Do not create briefs, planning documents, or analysis documents unless Tyler asks for one.

## Instruction precedence

```
latest direct user instruction
  → AGENTS.md / CLAUDE.md
    → ROADMAP.md
      → CONCEPT.md
```

A planning document is not a work queue.
Work on a roadmap item when Tyler names it for the current task.

## Principles

These come from `CONCEPT.md` section 4, which gives the reasoning.

- **Every intervention has an identity setting.**
  At zero it does nothing, and the render equals the unmodified model's output.
  The pretrained model as this project loads it is the reference state.
- **Determinism, not fidelity.**
  The same input, recipe, seed, and versions must reproduce the same sound.
  Matching any upstream project's output is not a goal.
- **Listening precedes engineering.**
  Build interventions breadth-first and shallow.
  Validation, tests, recipe support, and polish go only to what survives listening.
- **Whether something sounds good is Tyler's call.**
  Report what an intervention does and what to listen for; do not rank results by predicted musical value as if it were a finding.
- **No abstraction for hypothetical models.**
  Use PyTorch's own module naming, hooks, and state dictionaries until a second concrete model is in use.
- **Keep documentation proportionate.**
  The prototype had about twice as much Markdown as code.

## Constraints

- **PyTorch is the only ML framework.**
  Do not add TensorFlow or a second framework.
- **Do not retrain or fine-tune models.**
  The project manipulates pretrained models at inference time.
- **Seed every source of randomness**, including library-internal ones.
  `demucs.apply.apply_model` draws its shift offsets from Python's global `random` module.
- **Do not commit audio or model checkpoints.**
  Test audio is Tyler's own collection and may be copyrighted; `audio/`, `output/`, and `pretrained_models/` are ignored.
- **Dependency and Python version changes are decisions, not cleanup.**
  A change to `torch`, `demucs`, or the CUDA build can change renders and break recall of saved recipes.
  Raise them explicitly.

## Environment

Target: Windows 11, RTX 3080 Ti, PyTorch with CUDA.
**Nothing is verified yet** — see `ENVIRONMENT.md`, and read it before debugging any environment problem.

## Verification

**Fast — the default.**
Pure NumPy, no model, under a second.

```bash
pytest
black broken tests --check
isort broken tests --check
flake8 broken tests
```

**Model tier — to be defined in `ROADMAP.md` P1**, once a model render exists.
It should stay opt-in: nothing that downloads checkpoints or needs a GPU belongs in the default tier.

Every intervention carries one test that its zero setting is the identity.
Beyond that, do not write tests for an intervention before it has survived listening.

The lint tools are carried over from the prototype and are not a decision; replacing them is fine if raised.

## Markdown formatting

Use semantic line breaks in Markdown documentation.

- Do not hard-wrap prose at a fixed column width.
- Write prose as one sentence per physical line.
- Keep a one-sentence bullet on one line.
- For multi-sentence bullets, put each supporting sentence on its own indented continuation line.
- Preserve required Markdown structure for headings, tables, code blocks, lists, and examples.
- Do not reflow unrelated documentation while making content changes.

## Working style

- Inspect before redesigning.
  Read the model code you are about to hook; do not work from memory of an architecture.
- Distinguish findings from decisions.
  Surface consequential choices for acceptance rather than adopting them silently.
- Distinguish predictions from findings.
  A claim about how something sounds is a prediction until someone has listened.
- Prefer reversible exploration.
  Keep exploratory work easy to identify and discard.
- Measure before optimizing.
  Render cost on the GPU is unknown until P1 measures it.

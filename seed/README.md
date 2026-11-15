# Broken Stems

*Working title.*

An offline experimental audio tool that deliberately abuses pretrained stem-separation models to generate source material for sampling.

Instead of treating stem separation as an accuracy problem, it treats the trained model as a structured artifact generator.
The goal is **repeatable, controllable model failure**: output that stays connected to the musical structure of the input while revealing material conventional effects would not produce.

The intended end product is a small desktop GUI where how extreme the result is, and how closely it stays tied to the source, are fast choices made by ear.

It is not a better stem separator, not a realtime plugin, and not a production separation product.

## Status

Seeded on 2026-11-15 from an earlier prototype.
No model runs yet.
The repository holds the concept, the plan, and a small amount of carried NumPy code with passing tests.

The next step is roadmap item P1: the Windows environment and a stock model render.

## Documents

| File | Role |
|---|---|
| [`CONCEPT.md`](CONCEPT.md) | What the project is and why it is shaped this way. |
| [`ROADMAP.md`](ROADMAP.md) | What is planned, and what is deferred. |
| [`ENVIRONMENT.md`](ENVIRONMENT.md) | Setup and verified facts. |
| [`CHANGELOG.md`](CHANGELOG.md) | What has happened. |
| [`AGENTS.md`](AGENTS.md) | Instructions for coding agents; `CLAUDE.md` imports it. |

## Provenance

A reboot of Broken Spleeter (`tylerdalbec/broken-spleeter`), a prototype built on a fork of `deezer/spleeter`.
`CONCEPT.md` section 12 records why the project was restarted on a different model and framework.

## License

Not yet chosen.

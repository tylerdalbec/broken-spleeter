# Broken Spleeter

An offline experimental audio tool built by deliberately abusing [Spleeter](https://github.com/deezer/spleeter)'s pretrained source-separation models.

Instead of treating source separation as an accuracy problem, Broken Spleeter treats the trained model as a structured artifact generator.
The goal is **repeatable, controllable model failure** — false detections, displaced masks, unstable spectral residues, and other material that is useful as sound-design source rather than as faithful stems.

It is intended for experimental electronic music workflows.
It is not a better stem separator, not a realtime plugin, and not a production separation product.

## Status

Early bootstrap.
No Broken Spleeter functionality exists yet — the repository currently contains the inherited Spleeter runtime plus project documentation.
The immediate next step is establishing a working local environment and a verified ordinary Spleeter baseline.

## Relationship to Spleeter

This project is a fork of `deezer/spleeter` and inherits its separation runtime, model definitions, and test suite.
It does **not** track upstream and is expected to diverge freely; upstream is retained as provenance and as a reference for inherited behavior.

The unmodified pretrained model is treated as the project's reference state.
Every experimental behavior should be expressible as an intervention applied to ordinary inference, and should be independently bypassable — a configuration with all interventions disabled should behave as closely as practical to normal Spleeter.

## Provenance

| | |
|---|---|
| Upstream | [`deezer/spleeter`](https://github.com/deezer/spleeter) |
| Baseline commit | `c8854001ac8acad34a9bc2bd15f28475541828b1` (`master`) |
| Baseline version | Spleeter 2.4.2 |

Inherited publication, packaging, release, and community infrastructure (JOSS paper, Docker and Conda recipes, GitHub Actions, issue/PR templates, upstream changelog) has been removed from the working tree.
It remains available through Git history and the upstream repository.

## License

MIT, inherited from Deezer SA.
See [`LICENSE`](LICENSE).
Pretrained model checkpoints are distributed by Deezer under their own terms and are downloaded at runtime rather than vendored here.

## Documentation

| File | Purpose |
|---|---|
| [`PROJECT_SPRINGBOARD.md`](PROJECT_SPRINGBOARD.md) | Technical and product concept — design context, not a specification |
| [`WORKFLOW_SPRINGBOARD.md`](WORKFLOW_SPRINGBOARD.md) | Development workflow and bootstrap assumptions |
| [`AGENTS.md`](AGENTS.md) / [`CLAUDE.md`](CLAUDE.md) | Instructions for coding agents (byte-identical mirrors) |

Both springboards are working hypotheses.
Where repository evidence contradicts them, the repository wins.

## Environment

Not yet established.
The inherited stack pins `tensorflow==2.12.1`, which constrains the project to **Python 3.11 or older** — the workstation's default interpreter cannot be used directly.
`ffmpeg` must be available on `PATH`.
Pretrained checkpoints are downloaded on first use into `pretrained_models/` (gitignored).

Setting up a reproducible local environment is the subject of the next session.

## Inherited baseline commands

Recorded from upstream CI before it was removed.
**These have not been verified in this project yet** and are kept only as a starting point for local setup:

```bash
poetry install
poetry run pytest tests/
```

`audio_example.mp3` and `audio_example_mono.mp3` in the repository root are fixtures used by the inherited test suite.

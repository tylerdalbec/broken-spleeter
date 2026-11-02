# Broken Spleeter

An offline experimental audio tool built by deliberately abusing [Spleeter](https://github.com/deezer/spleeter)'s pretrained source-separation models.

Instead of treating source separation as an accuracy problem, Broken Spleeter treats the trained model as a structured artifact generator.
The goal is **repeatable, controllable model failure** — false detections, displaced masks, unstable spectral residues, and other material that is useful as sound-design source rather than as faithful stems.

It is intended for experimental electronic music workflows.
It is not a better stem separator, not a realtime plugin, and not a production separation product.

## Status

The first mask-manipulation slice is implemented as an offline command-line prototype.
It supports eight mask operations, JSON recipes, parameter sweeps, and a structural bypass path that preserves ordinary Spleeter inference.
The next roadmap step is musical triage of those sweeps, after choosing more representative test audio.
The planned desktop GUI and other model-corruption experiments are not implemented yet.
See [`ROADMAP.md`](ROADMAP.md) for current plans and [`CHANGELOG.md`](CHANGELOG.md) for completed work.

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
| [`AGENTS.md`](AGENTS.md) / [`CLAUDE.md`](CLAUDE.md) | Instructions for coding agents; `CLAUDE.md` imports `AGENTS.md` and adds a Claude Code-specific section |

Both springboards are working hypotheses.
Where repository evidence contradicts them, the repository wins.

## Environment

Verified on Windows 11 with Python 3.11, TensorFlow 2.12.1, Poetry 2.x, and FFmpeg on `PATH`.
The project environment lives in `.venv/`; Windows inference runs on CPU with this TensorFlow version.
Pretrained checkpoints download on first use into `pretrained_models/` (gitignored).
See [`ENVIRONMENT.md`](ENVIRONMENT.md) for setup, verified commands, and platform details.

## Commands

Run ordinary Spleeter separation:

```powershell
spleeter separate -p spleeter:2stems -o output audio_example.mp3
```

Inspect the Broken Spleeter command-line interface from the repository root:

```powershell
python -m broken --help
```

`audio_example.mp3` and `audio_example_mono.mp3` in the repository root are fixtures used by the inherited test suite.

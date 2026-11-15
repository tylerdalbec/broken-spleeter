# Concept

Design context for the project.
A working hypothesis, **not** a specification: repository evidence and listening results outrank anything written here.

Written 2026-11-15, at the reboot of the project from the Broken Spleeter prototype.
Section 12 records why the reboot happened.

Nothing described in this document has been listened to.
Every statement about how something will sound is a prediction, and is marked as one.

---

## 1. The idea

An offline tool that deliberately abuses pretrained stem-separation models to generate source material for sampling.

Stem separation is normally an accuracy problem.
Here the trained model is treated as a structured artifact generator: false detections, displaced decisions, unstable regions, contradictory classifications, and output from a network whose internals have been tampered with.

The target is not better stems.
The target is **repeatable, controllable model failure**.

The intended use is experimental electronic music production — deconstructed club, IDM, glitch, collage, resampling — where unusual intermediate material is worth more than faithful reconstruction.

Stem-separation abuse is the point; no particular model is.
The project began on Spleeter only because it was familiar.

## 2. Definition of success

The project succeeds if it becomes a fast way to generate material that would be difficult to produce with conventional audio effects.

The guiding question is not "how badly can the model be broken?" but:

> Which forms of controlled model failure produce artifacts that stay connected to the musical structure of the input while revealing unexpected spectral, rhythmic, or timbral material?

There is a fine line here, stated by Tyler on 2026-11-15.
If the output is not recognizable at all, it raises the question of why not just use synthesis.
But the tool should be able to get very weird and experimental.
The resolution is that **how extreme the result is must be a fast, continuous choice made by ear**, which is the main reason the tool has to exist as a GUI.

## 3. Product shape

A small desktop GUI for offline file processing, with the most interesting model parameters exposed, built for fast iteration.

The interaction loop:

1. Load an audio file.
2. Select a short preview region.
3. Choose interventions and set how extreme they are.
4. Render the preview, audition, compare against the previous render.
5. Adjust and repeat.
6. Export the result, with the recipe that produced it.

Source material is primarily **full mixes**, which should produce interesting results on their own.
A range of other material — loops, single sounds, non-musical audio — should also work, and deliberately mismatched material is expected to pay off in the decoupling and cross-audio paths of section 8.

It is not a realtime processor, a plugin, a DAW integration, a production-quality stem separator, a training framework, or a polished commercial application.

## 4. Design principles

**Every intervention has an identity setting.**
At zero, an intervention does nothing, and the render equals the unmodified model's output.
This replaces the prototype's "bit-identical to upstream" baseline: the reference state is the pretrained model as this project loads it, not any upstream project's output.

**Determinism, not fidelity.**
The same input, recipe, seed, model, and software versions should reproduce the same sound.
Matching another implementation's output is not a goal.

**Extremity and tether are separate global controls.**
See section 6.
Weirdness and recognizability get separate knobs.

**Listening precedes engineering.**
Interventions are built breadth-first and shallow, auditioned, and only the survivors get validation, tests, recipe support, and polish.
Section 12 explains what happened when this order was reversed.

**The GUI comes early.**
Controls cannot be designed for knobs nobody has heard, but nobody hears anything without a comfortable way to audition.
A minimal GUI is therefore a prerequisite for triage, not a reward at the end.

**No abstraction for hypothetical models.**
PyTorch already names every layer of every model and exposes hooks and weights uniformly.
That is the abstraction layer; do not build another until a second concrete model is actually in use.

## 5. The filter constraint

This is the finding that redirected the project.

A mask-based separator such as Spleeter computes a real-valued mask per stem, multiplies it into the complex STFT of the mixture, and resynthesizes with the mixture's phase.
Each Spleeter stem network ends in a sigmoid multiplied by its own input, and the outputs are then ratio-normalized.

Consequences:

- No corruption of weights, normalization statistics, or activations can produce energy that is not already in the mix.
  It can only change which time-varying filter is applied to the mix.
- The useful test for any model-internal corruption of such a model is whether it yields a more interesting mask than a few lines of NumPy could.
- The constraint guarantees the output stays tied to the input, and it also caps how strange the output can get.

Six of the prototype's eight mask operations (contrast, gain/bias, threshold, quantize, complement blend, noise) are pointwise remaps of that filter gain.
**Prediction, moderate confidence:** on their own they sound like a spectral gate with a different knee — usable as final shaping, not unique.

A separator that synthesizes its output is not bound by this constraint.
That is the reason for the change of substrate in section 7, and the reason the constraint becomes a control in section 6 instead of a fixed property.

## 6. Extremity and tether

Two global controls, independent of which intervention is active.

**Extremity** is the amount of the active intervention.
Zero is the identity setting from section 4.
Most interventions have a natural amount: a shift distance, a noise level, a blend factor between the original weights and a corrupted copy.

**Tether** is how strongly the output is forced back onto the source audio.
It reintroduces the filter constraint of section 5 by degrees:

| Tether | Output |
|---|---|
| None | The raw output of the corrupted model. |
| Middle | The model output's magnitudes, resynthesized with the source's phase. |
| Full | The model output reduced to a mask and applied to the source, so the result is a filtered copy of the source. |

With tether at full, any separator behaves like a mask-based one, and the mask operations in `broken/masks.py` apply.

Two ways to derive a mask from a stem `S` of a mixture `X`, both worth having:

- **Ratio between stems:** `|S_i| / (sum_j |S_j| + eps)`.
  Masks sum to one, so stems partition the source.
- **Against the source:** `min(|S_i| / (|X| + eps), 1)`.
  Masks do not sum to one, which exposes energy no stem claims and energy several stems claim — disagreement inside a single model, with no ensemble needed.

How the tether middle point should be interpolated, and whether it is one continuous control or a three-position switch, is undecided and best settled by ear.

## 7. Substrate

### PyTorch, with Demucs first

PyTorch is the only framework.
On the Windows workstation it gives native CUDA on the RTX 3080 Ti, forward hooks on any layer, and direct edits to model weights.
The prototype's TensorFlow 2.12 stack had no Windows GPU support and needed the model definition rewritten before any activation could be reached.

The first model is `htdemucs` from the `demucs` package.
Facts below were verified on 2026-11-15 by reading the `demucs` 4.1.0 source distribution from PyPI; nothing was executed.

- Version 4.1.0, MIT licensed, homepage `github.com/adefossez/demucs`, whose README describes it as the officially maintained Demucs.
- Requires Python >= 3.10 and `torch >= 2.1`.
- `htdemucs` has two U-Net branches that share a cross-domain transformer at the bottleneck: one over the spectrogram, one over the waveform.
- The spectrogram branch runs with `cac=True` by default, so it emits a complex spectrogram directly and ignores the mixture STFT.
  It is not a mask.
- The waveform branch emits samples directly.
- The final output is the sum of the two branches (`x = xt + x` at the end of `HTDemucs.forward`).
- Neither branch is bound by the filter constraint, so corrupted output is synthesized, not filtered.
- `demucs.apply.apply_model` splits long input into overlapping segments and offers `shifts`: it shifts the input by a random offset up to half a second, separates, and undoes the shift.
  The offset comes from Python's global `random` module, which must be seeded for a render to be reproducible.
- Pretrained variants include `htdemucs` (four stems: drums, bass, other, vocals), `htdemucs_ft` (fine-tuned from `htdemucs`, four times slower), and `htdemucs_6s` (adds guitar and piano; the README calls its piano stem poor, which may be an asset here).

Not verified: installation on the workstation, GPU render speed, and how the package's audio I/O behaves on Windows.
Those belong to roadmap item P1.

### Spleeter, optionally, later

Spleeter is no longer the base.
Its distinct character — weaker separation, an 11 kHz ceiling in the default configuration, and a fully independent network per stem — might be worth having as a second model.

Port its weights only if that character is missed after listening to Demucs.
The network is small (six strided 5x5 convolutions down, six transposed convolutions up, batch normalization throughout, 74 variables per stem).
Known hazards of a port: TensorFlow's asymmetric `same` padding on strided convolutions, and the cropping of transposed-convolution output.

The archived prototype repository, `tylerdalbec/broken-spleeter`, holds the detailed map of Spleeter's inference path in its `CHANGELOG.md` entry for 2026-09-08.

### Other separators

Band-split transformer models and the MDX family are all PyTorch and would attach through the same hooks.
Architectural variety probably matters more here than separation quality.
None of this is planned; see section 4 on hypothetical models.

## 8. Signal path

A sketch, to be corrected by the first implementation.

```text
source audio ───────────────────────────────┐
     │                                      │
     ▼                                      │
heard audio = transform(source)             │   (default: identical to source)
     │                                      │
     ▼                                      │
separator ◄── weight edits                  │
     │    ◄── activation edits (hooks)      │
     ▼                                      │
raw stems (of the heard audio)              │
     │                                      │
     ▼                                      │
inverse transform, where one exists         │
     │                                      │
     ▼                                      ▼
tether ◄──────────────────────────── filtered audio
     │                               (default: the source; may be another file)
     ▼
mask operations (only where the tether has produced a mask)
     │
     ▼
output stems, plus derived outputs (residuals, differences, variance)
```

The key structural idea is that **what the model hears and what gets filtered are two separate signals**.
By default they are the same audio.
Section 9 lists what happens when they are not.

Open structural question: at low tether the raw stems are stems of the heard audio, so a transform needs an inverse (varispeed back, reverse back) to land on the source's timeline.
Transforms without an inverse, and cross-audio rendering, only make sense toward full tether.

## 9. Intervention catalog

Ranked by expected novelty per unit of effort.
The ranking is a set of predictions made from reading model code, not from listening.

### 9.1 Hear/filter decoupling

Estimate on a transformed copy of the source, then apply the result to the untouched source.
The network stays intact and behaves exactly as trained, on wrong evidence, so the failure is learned and structured.

Candidate transforms of the heard audio:

- varispeed or pitch shift, so material lands in a register the model associates with a different source
- time reversal
- input gain and spectral tilt, since models respond to level nonlinearly
- mid/side encoding, channel swap
- spectral inversion
- a second sound mixed into the heard audio only: a decoy the model reacts to but which is never rendered

Cost is low, and at full tether no model internals are touched.

### 9.2 Cross-audio masks

The limiting case of 9.1: the mask estimated from track A filters track B.
This turns the separator into a learned modulation source.
Cost is low; the two signals need matching length.

### 9.3 Activation edits through hooks

Cheap in PyTorch.
Prefer edits that respect the network's topology over a generic menu of gain, clip, and noise:

- gain per skip-connection level, which controls how much input detail bypasses the deep layers
- time shifts and channel permutations in the latent, so later layers must reconcile displaced features with aligned skips
- edits inside the cross-domain transformer
- each Demucs branch soloed, and the difference between the two branches

**Prediction:** displacement inside the network is more interesting than the same displacement applied to a finished mask, because subsequent layers respond to the conflict instead of passing it through mechanically.

**Risk:** neither Demucs branch was trained to stand alone, so a soloed branch may be noise.

### 9.4 Weight edits

A blend between the original weights and a corrupted copy gives the extremity control directly.

Structured corruption is expected to beat Gaussian noise: channel permutation, filter sign inversion, whole-filter dropout, normalization-parameter scaling, permutation of the output head's stem channels.

**Prediction, moderate confidence:** plain Gaussian weight noise has a narrow useful range, and different seeds sound alike.
Test this with a short spike before designing anything around it.

Unverified idea: `htdemucs_ft` is fine-tuned from `htdemucs`, so their channels may still be aligned and interpolation between the two may be smooth instead of collapsing in the middle.

### 9.5 Instability as an audio source

Run the same input several times under small variations and output a statistic other than the mean: variance, range, or the difference between two passes.

Sources of variation: Demucs's random time shifts, seeds of a weight perturbation, segment boundaries.
Cost multiplies with the number of passes, so this wants the GPU.

### 9.6 Mask operations

The eight carried operations: contrast, gain/bias, threshold, quantize, time shift, frequency shift, complement blend, noise.
Available at full tether for any model.
Expected to be most useful as final shaping, with time and frequency shift the most distinctive of the set.

Open question carried from the prototype: a `noise` operation applies the same realization to every stem.
Whether stems should get independent noise is best settled by ear.

### 9.7 Recursion

Feed an output back through the separator.
**Prediction:** plain recursion approximates mask sharpening and is dull.
It becomes interesting with a transform, a different stem target, or a different recipe between passes.

### 9.8 Phase and reconstruction

The tether middle point is one instance.
Others: phase from a different stem, a different time, or a different file.

### 9.9 Gradient-based methods

Optimize the input, or a mask, to increase a stem's claim or a chosen channel's activation.
PyTorch makes this possible.
High variance, expensive, and likely to need the regularization tricks that image-domain feature visualization needed.
Later, if at all.

## 10. GUI direction

Compact and operational, function over appearance.

Minimum useful surface:

- load a file, show the waveform, select and loop a preview region
- extremity and tether
- a small set of interventions, each with a clear bypass
- render, audition, and A/B against the previous render
- a spectrogram or mask image next to the audio, since seeing what an intervention did speeds up understanding
- export, with the recipe saved alongside
- drag a rendered file out to the DAW

Continuous parameters support direct manipulation and numeric entry.
Seeds are explicit, with a quick reseed.

**Parameter cost tiers.**
Some parameters need the network to run again; others only re-run the tether and mask stages on cached model output.
In the Spleeter prototype this was 3.42 s against 0.33 s for an 11-second file on CPU.
The GUI should make the cheap tier feel immediate.
The actual costs on GPU with Demucs are unmeasured.

**Toolkit.**
PySide6 is the recommended default, because dragging rendered files into a DAW matters for a sampling workflow and Qt does it natively.
Not yet validated against the environment.

**Process structure.**
The model should stay resident between renders, and rendering must not block the GUI thread.
Whether that needs a separate worker process or only a thread is undecided.

## 11. Open questions

For Tyler:

- The project name.
  `broken-stems` in `pyproject.toml` and "Broken Stems" in the documents are working titles.
- The license.
  The carried code is this project's own, so nothing is inherited.
- The test audio set: material chosen to provoke failure, including dense mixes, solo sources, and material separators handle badly.
  Musical triage is blocked without it.

Technical, to be answered by measurement:

- Render time for a 10 to 20 second region on the GPU, per tier.
- The cost of bitwise-deterministic GPU rendering in PyTorch, and whether near-identical recall is acceptable instead.
- Whether a soloed Demucs branch is usable material.
- How segment boundaries and overlap in `apply_model` interact with activation edits.
- The recipe schema.
  The carried `broken/recipe.py` is version 1 and describes mask operations only; it needs interventions, extremity, tether, and the heard/filtered split.

## 12. Why the project was rebooted

The prototype, Broken Spleeter, was a fork of `deezer/spleeter` planned in August 2026 and worked on through September 2026.
A review on 2026-11-15 led to this reboot.

What the prototype got right, and what is kept:

- Interventions as bypassable modifications of ordinary inference.
- Deterministic recipes with explicit seeds.
- Analyzing once and re-rendering many variations cheaply.
- The original list of experimental areas, most of which survives in section 9.

What went wrong:

- **Work was ordered by implementation convenience, not expected novelty.**
  The first family built was mask manipulation, which section 5 argues is the least distinctive.
- **One family was engineered deeply before anything was heard.**
  The original plan called for quick experiments across seven families; the roadmap instead produced a recipe schema, validation, a command-line interface, and unit tests for a single family.
- **The project stalled at the listening step.**
  Triage was blocked on choosing test audio, and the only way to audition was to run command-line sweeps and open WAV files.
- **Documentation outweighed code about two to one.**
- **Upstream fidelity was treated as a requirement.**
  The TensorFlow pin, the bit-identical baseline, and most of the environment documentation existed to protect a property the project does not need.

A new repository was chosen over rebuilding in place because the old one was a GitHub fork whose history, package name, and constraints all described Spleeter, and about 95% of its tree would have been deleted.

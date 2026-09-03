# Broken Spleeter / Corrupted Stem Separator
## Project Springboard

**Repository:** `tylerdalbec/broken-spleeter`

**Status:** Working starting point for design and implementation.
This is intentionally **not** an authoritative roadmap or frozen specification.
It captures the current concept, likely high-value directions, and technical assumptions so they can be challenged and refined once a coding agent is working directly against the local repository.

---

## 1. Project Idea

Broken Spleeter is an offline experimental audio-processing tool built around deliberately abusing Spleeter's pretrained source-separation models.

Instead of treating source separation as an accuracy problem, the project treats the model as a structured artifact generator.
The goal is to make Spleeter produce useful mistakes: false vocal detections, unstable spectral residues, displaced masks, contradictory classifications, recursively degraded stems, and other material that can become samples or sound-design source material.

The musical target is not "better stems."
The target is **repeatable, controllable model failure**.

The project is primarily intended for experimental electronic music workflows such as deconstructed club, IDM, glitch, collage, resampling, and related production techniques where unusual intermediate material is often more valuable than faithful reconstruction.

---

## 2. Why Spleeter Is a Good Substrate

Spleeter is a useful foundation because it is open source, uses accessible TensorFlow model infrastructure, and exposes a relatively understandable signal path.

At a high level:

1. Audio is converted into a time-frequency representation.
2. A trained model estimates source-specific spectral masks.
3. Those masks are applied to the mixture representation.
4. The separated spectra are reconstructed into audio.

The standard 2-stem model separates:

- `vocals`
- `accompaniment`

Spleeter also ships 4-stem and 5-stem configurations.

The U-Net-based separator is especially interesting for deliberate corruption because there are several distinct places where the inference process can be modified:

- model/checkpoint weights
- BatchNorm state
- intermediate activations
- estimated masks
- reconstruction assumptions
- relationships between multiple models
- repeated/recursive processing

This allows Broken Spleeter to become more than a "randomly damaged checkpoint" utility.

---

## 3. Core Design Principle

The normal pretrained model should remain the reference state.

Every experimental behavior should be describable as an intervention applied to normal inference:

```text
input audio
    ↓
optional input corruption
    ↓
STFT / spectral representation
    ↓
U-Net encoder
    ↓
optional activation corruption
    ↓
bottleneck / decoder
    ↓
estimated source mask
    ↓
optional mask corruption
    ↓
reconstruction / phase manipulation
    ↓
output audio
    ↓
optional recursive processing
```

Each intervention should be independently bypassable.

A configuration with every intervention disabled should behave as closely as practical to normal Spleeter.

This gives the project an important baseline and makes A/B comparison straightforward.

---

## 4. Product Shape

The intended application is a small desktop GUI for offline file processing.

It is **not** intended to be:

- a realtime plugin
- a production-grade stem-separation product
- a DAW-integrated processor
- a polished commercial application
- a new source-separation training framework

The initial interaction model should be simple:

1. Load an audio file.
2. Select a model and corruption configuration.
3. Optionally select a short preview region.
4. Render the preview.
5. Audition and adjust.
6. Render the desired output.
7. Save or recall the corruption configuration.

The UI should prioritize function over appearance.

Important parameters should generally support both:

- direct manipulation, such as a knob/slider
- precise numeric entry

---

## 5. Working Processing Architecture

A useful architectural model is to treat the application as a set of independent processing modules.

```text
Audio Input
    │
    ├── Input / Analysis Manipulation
    │
    ▼
Spleeter Model
    │
    ├── Weight Corruption
    ├── BatchNorm Corruption
    ├── Activation Corruption
    │
    ▼
Estimated Masks
    │
    ├── Mask Manipulation
    │
    ▼
Reconstruction
    │
    ├── Phase / Reconstruction Manipulation
    │
    ▼
Output
    │
    ├── Recursion
    ├── Ensemble / Model Comparison
    └── Export
```

The modules do not all need to exist in the first implementation.

The architecture should make it possible to add them without requiring a rewrite of the GUI or render pipeline.

---

# 6. High-Value Experimental Areas

## 6.1 Mask Manipulation

This is probably the best first experimental system to implement.

The trained network can be allowed to make its normal source classification, after which Broken Spleeter deliberately alters the resulting mask.

This preserves much of the useful learned structure while making the final separation wrong in controlled ways.

Candidate operations include:

### Mask contrast / exponent

```text
M' = M^γ
```

This changes confidence structure.

Possible behavior:

- `γ > 1`: emphasize high-confidence regions
- `γ < 1`: flatten distinctions and admit weak detections

### Bias and gain

```text
M' = gain * M + bias
```

Useful for forcing normally rejected material into a stem.

### Thresholding

Hard or soft thresholds may convert probabilistic masks into more discontinuous spectral gates.

### Quantization

```text
M' = quantize(M, levels)
```

Reducing the mask to a small number of values may create stepped or fragmented spectral behavior.

### Temporal displacement

```text
M'(t, f) = M(t - Δt, f)
```

The model's classification from one moment is applied to another moment.

Potential result:

- displaced attacks
- spectral ghosts
- broken rhythmic gating
- false continuity between events

### Frequency displacement

```text
M'(t, f) = M(t, f - Δf)
```

The model's classification is applied to the wrong frequency region.

Potential result:

- pseudo-formants
- harmonic misclassification
- strange vocal-like residues
- structurally related but spectrally misplaced fragments

### Mask inversion / complement blending

Blend between:

```text
M
```

and:

```text
1 - M
```

rather than treating the two as strictly separate outputs.

### Mask blur

Blur along either axis:

- time
- frequency
- both

### Mask noise

Inject controlled random or correlated noise into the mask.

### Mask feedback

Use prior mask state when generating the next result.

This could eventually become a simple stateful corruption system even though the underlying separator is offline.

---

## 6.2 Pretrained Weight Corruption

The original project idea is to directly modify pretrained model parameters without retraining.

The mutation should ideally be reproducible from:

```text
original checkpoint
+ corruption recipe
+ random seed
= mutant model
```

The application should initially avoid saving large numbers of complete mutated checkpoints unless caching becomes useful later.

Candidate weight-corruption modes:

### Gaussian perturbation

```text
W' = W + amount * std(W) * noise
```

Useful as a baseline.

### Layer gain

```text
W' = αW
```

Apply to selected layers or groups of layers.

### Filter/channel dropout

Zero complete filters or channels rather than isolated scalar weights.

This may produce more coherent model failure than sparse random damage.

### Sign inversion

Flip selected filters:

```text
W' = -W
```

### Filter swapping

Exchange learned filters within a layer.

### Channel permutation

Reorder channels at one stage without applying the corresponding inverse permutation downstream.

This intentionally breaks the learned internal representation.

### Selective targeting

Corruption should eventually be targetable to broad structural areas such as:

- encoder
- bottleneck
- decoder
- output layers
- all layers

The likely musical behavior may differ substantially:

- early-layer corruption may destroy basic spectral feature extraction
- late-layer corruption may preserve recognizable structure while producing incorrect classification
- decoder corruption may be particularly useful for "structured wrongness"

---

## 6.3 BatchNorm Corruption

Batch normalization is a promising target because it encodes assumptions about expected internal activation distributions.

Possible parameters:

- scale `gamma`
- shift `beta`
- perturb moving mean
- perturb moving variance
- swap statistics between layers or stems
- interpolate between original and corrupted statistics

This may produce stable, reproducible miscalibration without destroying the complete network representation.

It should be treated as a separate corruption type from generic weight noise.

---

## 6.4 Activation Corruption

A later, potentially high-value system would modify intermediate feature maps during inference rather than altering stored model weights.

This is conceptually similar to patching inside the network.

Candidate operations:

- gain
- clipping
- quantization
- channel dropout
- channel permutation
- channel rotation
- noise
- temporal shift
- frequency shift
- feature-map feedback
- crossfeed between stem networks

Example:

```text
activation(t, f, c) → activation(t - Δt, f, c)
```

This lets the decoder receive temporally stale learned features.

Another possibility:

```text
activation(t, f, c) → activation(t, f - Δf, c)
```

This intentionally violates the network's learned spectral organization.

Activation corruption may ultimately produce more controllable and musically useful behavior than arbitrary checkpoint damage.

---

## 6.5 Vocal / Accompaniment Model Crossbreeding

The 2-stem configuration creates corresponding source-specific networks.

A possible experiment is parameter-space interpolation:

```text
V' = (1 - a)V + aA
A' = (1 - a)A + aV
```

where:

- `V` is a vocal-model tensor
- `A` is the corresponding accompaniment-model tensor
- `a` is the morph amount

This does **not** imply that internal channels have matching semantic meaning.

The experiment is interesting precisely because they may not.

Possible extensions:

- interpolate only selected layers
- swap decoder layers between stems
- replace BatchNorm state across stems
- crossfeed intermediate activations instead of weights

---

## 6.6 Multi-Model Disagreement

Spleeter's multiple pretrained stem configurations can be treated as different opinions about the same audio.

For example, compare the 2-stem vocal estimate to the 5-stem vocal estimate.

A disagreement representation might be:

```text
D = abs(M_vocal_2stem - M_vocal_5stem)
```

The result represents spectral areas where the two models disagree.

Possible operations:

- intersection
- union
- absolute difference
- exclusive/disagreement mask
- weighted blend
- confidence comparison

More unusual comparisons may be even more useful:

- 2-stem accompaniment vs. 5-stem `other`
- 2-stem vocals vs. 5-stem guitar
- drums vs. vocals
- bass vs. vocal confidence

These categories do not need to be semantically compatible.

The mismatch is part of the experiment.

---

## 6.7 Recursive Separation

An output can be fed back through the separator.

Example:

```text
input
  ↓
corrupted vocal extraction
  ↓
vocal output
  ↓
corrupted vocal extraction
  ↓
vocal output
  ↓
...
```

Potential controls:

- iteration count
- feedback mix
- same seed every pass
- new seed every pass
- corruption growth per pass
- alternating stem target
- alternating model
- alternating corruption recipe

Example alternating process:

```text
vocals → accompaniment → vocals → accompaniment
```

This may progressively force audio toward increasingly pathological interpretations of a learned category.

---

## 6.8 Mutant Ensembles

Run the same input through multiple corrupted model variants.

Example:

```text
input
 ├── mutant seed 100
 ├── mutant seed 101
 ├── mutant seed 102
 └── mutant seed 103
```

Possible reductions:

- mean
- median
- maximum
- minimum
- difference
- range
- variance

Variance is especially interesting:

> Output the spectral regions where corrupted models are least stable.

This effectively turns classifier instability into an audio source.

This should probably be treated as a later feature because it multiplies render cost.

---

## 6.9 Analysis and Reconstruction Abuse

The model itself does not need to be the only target.

Potential future experiments include:

- STFT window-size changes
- hop-size changes
- alternate overlap
- mask exponent changes
- sample-rate mismatch
- spectral cropping or extension
- unconventional reconstruction

Some Spleeter analysis parameters are tied to expected model dimensions, so not every parameter can safely change independently.

The implementation should distinguish between:

1. parameters that can be manipulated freely
2. parameters that require compensating tensor transformations
3. parameters that simply invalidate the model architecture

---

## 6.10 Phase Manipulation

A useful future experimental area is deliberately breaking reconstruction-phase assumptions.

Potential sources for output phase:

- original mixture phase
- opposite-stem phase
- delayed phase
- randomized phase
- phase interpolated between sources
- phase from another audio file
- phase from another processing iteration

This could create a very different class of artifacts from mask corruption.

It is likely better treated as a later module rather than an initial requirement.

---

# 7. Reproducibility as a Musical Feature

Randomness should be deterministic whenever practical.

A useful sound should be recallable.

Parameters that invoke randomness should therefore use explicit seeds.

Example:

```text
Corruption Type: decoder channel dropout
Amount:          0.12
Seed:            1847
```

The same input, model version, application version, recipe, and seed should ideally produce the same output.

Presets should store the full processing recipe in a plain-text format such as JSON.

Example:

```json
{
  "model": "2stems",
  "seed": 1847,
  "weight_corruption": {
    "enabled": true,
    "mode": "channel_drop",
    "amount": 0.12,
    "target": "decoder"
  },
  "mask": {
    "enabled": true,
    "quantize_levels": 8,
    "time_offset_ms": 43,
    "contrast": 1.7
  },
  "recursion": {
    "enabled": false,
    "iterations": 1
  }
}
```

A coding agent should review whether JSON remains the best internal representation once the application architecture is clearer.

---

# 8. GUI Direction

The GUI should be compact and operational rather than decorative.

A rough structure:

```text
┌──────────────────────────────────────────────────────┐
│ Input.wav                              [Load]         │
│ waveform / preview-region selection                  │
├───────────────┬──────────────────────────────────────┤
│ Processing    │ Current Module                       │
│               │                                      │
│ Model         │ Amount        [knob]  0.083          │
│ Activation    │ Seed                  1847           │
│ Mask          │ Target                Decoder        │
│ Reconstruction│ Mode                  Channel Drop   │
│ Recursion     │ ...                                  │
│ Ensemble      │                                      │
├───────────────┴──────────────────────────────────────┤
│ [Preview Region]        [Render]        [Batch]       │
├──────────────────────────────────────────────────────┤
│ Outputs / render log / audition controls             │
└──────────────────────────────────────────────────────┘
```

Possible UI characteristics:

- module list or tabs on the left
- parameters on the right
- every continuous parameter supports direct numeric entry
- coarse/fine drag behavior
- reset-to-default gesture
- clear bypass state for every module
- obvious render status
- no unnecessary modal dialogs
- presets accessible without obscuring the processing page

The first UI does not need a sophisticated visual design system.

Correct parameter exposure and fast iteration matter more.

---

# 9. Preview Workflow

Previewing a short source region should be a first-class feature.

A typical sound-design loop should be:

```text
select 5–20 second region
        ↓
render preview
        ↓
audition
        ↓
adjust
        ↓
render preview again
```

This is much more important than realtime behavior.

Potential future quality-of-life additions:

- A/B compare current render against previous render
- history of recent corruption recipes
- quick reseed
- "next seed" audition workflow
- waveform region looping
- render several seeds as a batch
- drag rendered result into the DAW
- automatic output naming based on preset/seed

---

# 10. Output Types

Normal stem outputs should remain available.

Potential outputs:

- vocals
- accompaniment
- drums
- bass
- piano
- other
- residual/difference
- mask-derived outputs
- disagreement outputs
- ensemble statistics

For debugging and exploration, the application may also optionally export:

- raw mask image
- corrupted mask image
- mask arrays
- processing recipe
- render metadata

Visualizing masks may be especially useful during early experimentation because it gives a direct view into what each corruption operation is doing.

---

# 11. Initial Technology Direction

The initial implementation should probably remain in Python.

Reasoning:

- Spleeter is already Python/TensorFlow
- model internals are immediately accessible
- experimental hooks can be added with relatively little translation overhead
- this project values rapid experimentation over runtime purity

A plausible starting stack:

```text
PySide6        GUI
pyqtgraph      waveform / basic analysis visualization
Spleeter       separation and model infrastructure
TensorFlow     model execution and intervention
NumPy          corruption algorithms
soundfile      simple audio I/O where useful
```

This stack should be treated as a working hypothesis rather than a requirement.

A coding agent working directly against the repository should inspect:

- current Spleeter Python/TensorFlow compatibility
- dependency age
- GPU behavior
- easiest points for hooking masks and activations
- whether PySide6 introduces any awkward packaging constraints
- whether a smaller GUI toolkit would materially reduce complexity

---

# 12. GUI / Render Process Separation

The render engine should probably not run directly on the GUI thread.

A useful architecture may be:

```text
GUI process
    │
    │ RenderSpec / recipe
    ▼
worker process
    │
    ├── load model
    ├── apply corruption recipe
    ├── process audio
    ├── export outputs
    └── report status
```

Reasons:

- TensorFlow is heavyweight
- GPU/session state can be awkward
- deliberately malformed inference experiments may crash
- a failed render should not necessarily terminate the GUI
- later batch/ensemble processing becomes easier

The exact process architecture should be validated against how the current Spleeter code actually manages TensorFlow models.

---

# 13. Suggested Development Progression

This is a **working ordering**, not a commitment.

## Stage A — Establish a clean baseline

- get the fork running locally
- verify normal Spleeter separation
- establish representative test audio
- understand model download/cache behavior
- identify the exact inference path
- establish automated smoke tests where practical

## Stage B — Minimal application shell

- load audio
- select model
- select preview range
- perform normal separation
- render outputs
- basic GUI
- worker/process boundary if appropriate

The application should already be useful as a normal Spleeter frontend at this stage.

## Stage C — Mask manipulation

Implement the first set of experimental controls:

- contrast/exponent
- gain/bias
- threshold
- quantization
- temporal displacement
- frequency displacement
- inversion/blending

This stage should establish the general "processing module" architecture.

## Stage D — Checkpoint/model corruption

Add reproducible mutations:

- random perturbation
- layer gain
- sign flip
- channel dropout
- channel permutation
- targeted encoder/decoder corruption
- BatchNorm corruption

## Stage E — Activation hooks

Expose selected intermediate tensors and apply runtime modifications.

This stage may require more invasive changes to the Spleeter model implementation.

## Stage F — Recursive processing

Add repeat/feedback workflows.

## Stage G — Multi-model and ensemble systems

Add:

- 2-stem / 4-stem / 5-stem disagreement
- model blending
- mutant ensembles
- statistical reductions

## Stage H — Reconstruction experiments

Explore:

- phase abuse
- analysis mismatch
- unusual resynthesis behavior

The ordering should change if early experiments reveal a much more productive direction.

---

# 14. What Should Not Be Overdesigned Initially

Avoid spending early effort on:

- plugin formats
- realtime audio
- polished theming
- elaborate preset browsers
- cloud services
- model retraining
- user accounts
- distribution installers
- extensive DAW integration
- optimization before render cost is measured
- a large abstraction layer around hypothetical future models

The purpose of the first implementation is to discover which corruptions produce worthwhile audio.

The software architecture should support experimentation without attempting to anticipate every future feature.

---

# 15. Repository Strategy

The project currently exists as a GitHub fork:

```text
deezer/spleeter
      │
      ▼
tylerdalbec/broken-spleeter
```

The fork can be cloned and worked on like a normal repository.

A conventional remote setup would be:

```text
origin   → tylerdalbec/broken-spleeter
upstream → deezer/spleeter
```

Normal feature branches can then be created inside the fork.

For now, working directly from the fork makes sense because early experiments may modify Spleeter internals substantially.

Later, revisit whether Broken Spleeter should remain a direct Spleeter fork or become an independent project that incorporates only the required Spleeter/model infrastructure.

Factors that may influence that decision:

- how invasive the changes become
- whether upstream Spleeter updates remain useful
- dependency modernization
- packaging needs
- how much original Spleeter behavior remains visible to users

---

# 16. Meta-Plan for the First Coding-Agent Session

The first coding-agent session should **not** immediately begin implementing the entire feature set.

The agent should first inspect the local repository and reconcile this document with the actual codebase.

A useful initial task would be:

1. Inspect current repository structure and Spleeter version.
2. Confirm how pretrained checkpoints are downloaded and restored.
3. Trace normal 2-stem inference end-to-end.
4. Identify the cleanest point to capture raw masks.
5. Determine whether masks can be modified without substantially rewriting model execution.
6. Inspect layer/checkpoint naming sufficiently to determine how targeted mutations can be implemented.
7. Evaluate TensorFlow-version and Python-version constraints.
8. Propose a minimal architecture for:
   - GUI
   - render jobs
   - model loading
   - corruption recipes
   - output management
9. Identify which assumptions in this document are wrong, outdated, unnecessarily difficult, or incomplete.
10. Recommend a first implementation slice that proves the concept with the least architectural commitment.

The expected output from that session should be a refined implementation proposal, not merely code.

---

# 17. Open Questions for Repository-Aware Refinement

These questions are intentionally left unresolved.

## Spleeter internals

- Where is the cleanest interception point for masks in the current code?
- Can masks be exposed without duplicating the full separator path?
- How are the two U-Net instances named in checkpoints?
- Are corresponding vocal/accompaniment tensors reliably shape-compatible?
- Can individual encoder/decoder blocks be addressed robustly by name?
- Which BatchNorm parameters are stored in the checkpoint?
- Are there graph/session constraints that make runtime mutation awkward?
- Is TensorFlow eager execution involved anywhere relevant, or is this effectively TF1-style graph execution?

## Model mutation

- Is it cleaner to mutate checkpoint tensors before graph restoration or assign new values after restore?
- What mutation representation best survives upstream model naming changes?
- Should corruption recipes target semantic groups such as `decoder`, or explicit tensor names?
- How should unsupported/mismatched mutation recipes fail?
- Is mutation-on-load fast enough for interactive preview work?
- Is caching mutated models worthwhile?

## Activation hooks

- What is the least invasive way to expose intermediate activations?
- Should the project modify the existing U-Net function directly or create an instrumented parallel implementation?
- Can activation corruption remain compatible with normal pretrained checkpoints?
- Which layers are the best initial hook points?

## Mask pipeline

- Should mask corruption happen inside TensorFlow or after exporting mask arrays to NumPy?
- Does moving mask manipulation outside the graph materially hurt performance?
- Which mask representation gives the easiest support for temporal/frequency displacement?
- How should mask values outside the nominal range be treated?
- Should reconstruction clamp them, normalize them, or deliberately allow pathological values?

## Preview and performance

- How expensive is model startup compared with processing a short preview?
- Should models stay resident in a long-lived worker?
- How many model variants can reasonably remain loaded?
- Is GPU use worth supporting immediately?
- What preview duration gives a useful interaction loop?

## GUI

- Is PySide6 + pyqtgraph a good fit for the current dependency environment?
- Would a minimal waveform selector be enough for the first version?
- Should audition playback be handled inside the app or delegated to the OS?
- Is drag-and-drop export to Ableton practical enough to prioritize?
- What is the minimum UI needed to make rapid seed exploration pleasant?

## Presets and reproducibility

- What information is required for true deterministic recall?
- Should presets record:
  - Broken Spleeter version?
  - upstream Spleeter commit?
  - checkpoint checksum?
  - TensorFlow version?
- Should recipes be JSON, TOML, YAML, or an internal dataclass serialized to JSON?
- How should presets evolve when new parameters are added?

## Project structure

- How much upstream Spleeter code should be modified directly?
- Should experimental code live under a separate package namespace immediately?
- Should upstream behavior be wrapped rather than edited wherever possible?
- At what point would converting the fork into an independent project become cleaner?

## Musical/product questions

- Which operations create genuinely new sample material rather than generic degradation?
- Are discrete/random controls more productive than continuous macro controls?
- Should "randomize" operate on all parameters or only explicitly enabled modules?
- Would a constrained randomization system be useful?
- Should the application expose macro controls such as:
  - `Misclassification`
  - `Instability`
  - `Temporal Smear`
  - `Spectral Displacement`
  while retaining the underlying technical parameters?
- Is automatic batch generation across seeds more useful than deeper single-model control?
- Are disagreement and recursive modes more musically valuable than fine-grained checkpoint hacking?

---

# 18. Early Experiments Worth Prioritizing

Before building a large GUI, a small command-line or script-based experimental harness could compare a few interventions on the same short source material.

Particularly promising candidates:

### Experiment 1 — Mask time shift

Sweep:

```text
0 ms
10 ms
25 ms
50 ms
100 ms
250 ms
```

### Experiment 2 — Mask frequency shift

Sweep small and large bin offsets.

### Experiment 3 — Mask quantization

Compare:

```text
2
4
8
16
32
```

levels.

### Experiment 4 — Decoder-only corruption

Compare several corruption amounts using a fixed seed.

### Experiment 5 — BatchNorm corruption

Perturb moving statistics while leaving convolution kernels intact.

### Experiment 6 — Recursive vocal extraction

Run the same extracted stem through multiple passes.

### Experiment 7 — 2-stem / 5-stem disagreement

Render only spectral regions where the two vocal estimates differ.

The purpose is not to optimize these systems.

The purpose is to determine which families of failure are musically productive enough to deserve first-class GUI modules.

---

# 19. Possible Later Directions

These are speculative and should not constrain the first architecture.

## Cross-audio masks

Use the mask inferred from one source to process another.

Example:

```text
track A → vocal mask A
track B × vocal mask A → output
```

This turns Spleeter into a learned spectral modulation generator.

## Cross-audio activation injection

Use intermediate activations from one source while decoding another.

Potentially much stranger, but substantially more complex.

## Corruption automation curves

Allow a corruption parameter to vary over the duration of an offline render.

For example:

```text
decoder corruption:
0.00 → 0.20 → 0.03
```

This would create movement without requiring realtime processing.

## Seed interpolation

If practical, interpolate between two deterministic corruption states rather than jumping seeds.

## Dataset-scale harvesting

Batch-process a sample library across selected recipes and seeds, then export only short/high-energy/disagreement-heavy regions.

## Artifact detection

Use simple metrics to automatically locate:

- high disagreement
- unusually sparse masks
- unstable regions
- strong non-vocal "vocal" detections

This could turn the tool from a processor into an artifact-mining system.

## Additional separator architectures

If the project eventually becomes independent of Spleeter, the same corruption framework could be applied to other source-separation networks.

That should be considered only after Spleeter itself proves the concept.

---

# 20. Working Definition of Success

The project is successful if it becomes a fast way to generate material that would be difficult to produce with conventional audio effects.

The important question is not:

> How badly can the model be broken?

It is:

> Which forms of controlled model failure produce artifacts that remain connected to the musical structure of the input while revealing unexpected spectral, rhythmic, or timbral material?

The implementation should stay biased toward answering that question.

---

## Final Note

This document is a starting hypothesis.

A coding agent with direct access to the local `tylerdalbec/broken-spleeter` repository should be encouraged to challenge:

- the proposed implementation order
- the GUI stack
- assumptions about TensorFlow internals
- which corruption points are easiest to expose
- which features belong in the first prototype
- whether modifying the fork directly remains the cleanest structure

The first repository-aware design pass should refine this document into a smaller, technically grounded implementation plan while preserving room for exploratory work.

# Brief — Mask Manipulation Slice

**Roadmap item:** A2.
**Status:** the interception mechanism is landed; this brief covers the remainder.
**Prerequisite:** none. The tree is clean and `broken/` is committed.

This document is an implementation contract.
It is self-contained on purpose: every constraint that matters is restated here rather than referenced, because the implementer may not be the agent that wrote it.

Where this brief and another document disagree about *what to build*, this brief wins.
Where they disagree about a **constraint**, the constraint wins — those are listed in §2 and are not negotiable by this brief.

---

## 1. What this is for

Broken Spleeter makes Spleeter produce useful mistakes.
This slice builds the first family of them: deliberate corruption of the estimated separation mask, driven from a script, with reproducible recipes.

The point is **not** to build a good abstraction.
The point is to render enough variations, cheaply enough, that a human can listen and decide which kinds of failure are musically worth keeping.
Everything here is in service of that listening loop.

Do not build a GUI.
Do not generalize beyond mask corruption.

---

## 2. Constraints

These are load-bearing.
Violating one silently breaks something that took a previous session real effort to establish.

- **Do not modify anything under `spleeter/`.**
  All new code goes in `broken/`.
  The unmodified pretrained model is this project's reference state; the inherited package is the thing being wrapped, not edited.
- **Do not change `pyproject.toml` or `poetry.lock`.**
  They carry platform markers that are the only reason `poetry install` works on Windows: `tensorflow-io-gcs-filesystem` resolves to 0.31.0 there because 0.32.0 ships no Windows wheels, and `tensorflow-intel` is declared Windows-only because the Windows `tensorflow` wheel is a ~2 KB metadata stub that requires it.
  Collapsing or tidying those markers re-breaks installation.
- **Do not add, remove, or bump any dependency.**
  The TensorFlow 2.12.1 pin protects the model behavior this project exists to distort.
  If you believe you need a new package, stop and say so instead.
- **Do not set the `GITHUB_REPOSITORY` environment variable**, and do not add CI that would.
  `spleeter/model/provider/github.py` falls back to it when locating checkpoints, which silently redirects model downloads to this fork, where they do not exist.
- **Do not rename the `spleeter` package or distribution.**
  `spleeter/options.py` resolves `--version` through `importlib.metadata.version("spleeter")`.
- **Everything runs on CPU.**
  TensorFlow dropped native Windows GPU support after 2.10, so this pin has no CUDA path regardless of installed hardware.
  Do not add GPU code paths, device placement logic, or optimizations that assume a GPU.
- **Do not commit, branch, stage, or otherwise touch git state.**
  Leave changes in the working tree.
- **Markdown uses semantic line breaks** — one sentence per line, no hard wrapping at a column width.
  This applies to any document you edit.
- `AGENTS.md` and `CLAUDE.md` are byte-identical mirrors.
  You should not need to touch them; if you do, apply the edit to both and verify with `diff AGENTS.md CLAUDE.md`.

---

## 3. Environment

Python 3.11 in a project-local venv at `.venv/`, TensorFlow 2.12.1, `ffmpeg` on `PATH`.

```powershell
.\.venv\Scripts\Activate.ps1
```

Verification commands, all of which currently pass:

```powershell
pytest tests/
black broken spleeter --check
isort broken spleeter --check
flake8 broken
```

`pytest tests/` downloads the 2stems, 4stems and 5stems checkpoints on first run (~417 MB).
`pytest tests/test_separator.py -k 2stems` avoids the larger two.

`ENVIRONMENT.md` is the authoritative environment reference and records why the pins exist.

---

## 4. What already exists

`broken/` contains the interception mechanism, verified working.
Read these three files before writing anything; they define the contract you are building on.

- `broken/builder.py` — `InterceptingSpecBuilder` splices a `placeholder_with_default` between the estimated mask and reconstruction.
  Unfed, the model's own estimate passes through, so bypass is structural rather than a code path.
- `broken/separator.py` — `BrokenSeparator` owns its own `tf.Graph` and session.
- `broken/masks.py` — `time_shift`, the first operation, which establishes the array contract.

### API you will use

```python
sep = BrokenSeparator("spleeter:2stems")

waveform = sep.load_audio("audio_example.mp3")           # optional offset=, duration=
masks    = sep.estimate_masks(waveform, "audio_example.mp3")

# ordinary separation, bit-identical to upstream Spleeter
sources = sep.separate(waveform, "audio_example.mp3")

# corrupt via a callable
sources = sep.separate(waveform, "audio_example.mp3", mask_fn=lambda m: ...)

# or feed pre-computed masks, skipping the network
sources = sep.separate(waveform, "audio_example.mp3", masks=corrupted)

sep.save_to_file(sources, "audio_example.mp3", "output/somewhere")
sep.close()                                               # also a context manager
```

`sep.instruments` lists the stems.
`sep.sample_rate` is the model's rate.
The model config is on `sep._params`, which is where `frame_step` lives — you will need it for millisecond conversion.

### The performance fact that shapes the sweep design

**Feeding a mask prunes the U-Net from the render.**
TensorFlow does not execute ops whose consumers are all fed, so a render with `masks=` supplied costs about a tenth of a full pass — measured at 0.33 s against 3.42 s on `audio_example.mp3`.

Therefore every sweep must call `estimate_masks` **once** and then loop over `separate(..., masks=...)`.
Calling `separate(..., mask_fn=...)` in a loop re-runs the network every time and is roughly ten times slower for identical output.

---

## 5. Work items

### 5.1 Mask operations

All operations live in `broken/masks.py` alongside the existing `time_shift`.

**Array contract.**
A mask is a `np.ndarray` shaped `(frames, bins, channels)`, dtype `float32`, nominally in `[0.0, 1.0]`.
Operations are pure — they must not modify their input — and must return `float32`.

The dtype requirement is not cosmetic.
Multiplying a float32 array by a Python float upcasts it to float64, and the graph's mask placeholders are float32.
Cast explicitly on return from every operation.

**Values are allowed to leave `[0, 1]`.**
Do not clamp inside operations.
Pathological mask values are a legitimate output of this project, not a bug to defend against.
Clamping is available once, at the end of the chain, and is off by default (§5.2).

Implement:

| Operation | Signature | Definition |
|---|---|---|
| Contrast | `contrast(mask, gamma)` | `sign(M) * abs(M) ** gamma`, sign-preserving so that composing after an operation that produced negatives does not yield NaN. `gamma > 0`. |
| Gain and bias | `gain_bias(mask, gain=1.0, bias=0.0)` | `gain * M + bias` |
| Threshold | `threshold(mask, threshold, softness=0.0)` | `softness == 0`: hard, `(M >= threshold)` as float32. `softness > 0`: `clip((M - threshold) / softness + 0.5, 0, 1)`. |
| Quantize | `quantize(mask, levels)` | `round(M * (levels - 1)) / (levels - 1)`, `levels >= 2`. |
| Time shift | `time_shift(mask, frames, wrap=False)` | Existing. Add the `wrap` parameter. Displace along axis 0. |
| Frequency shift | `freq_shift(mask, bins, wrap=False)` | Displace along axis 1, same fill semantics. |
| Complement blend | `complement_blend(mask, amount)` | `(1 - amount) * M + amount * (1 - M)`. At `amount=1` this is full inversion; at `0.5` it is flat. |
| Noise | `noise(mask, amount, seed)` | `M + amount * rng.standard_normal(M.shape)` using `np.random.default_rng(seed)`. |

**Shift fill semantics.**
`wrap=False` (default) fills vacated positions with zeros, so a shift removes material at one edge.
`wrap=True` rolls, folding the displaced edge around.
These sound meaningfully different; both are wanted.

Positive `frames`/`bins` delays or raises, negative advances or lowers.
The existing `time_shift` already establishes this direction — match it.

Do **not** implement blur or correlated noise in this slice.

### 5.2 Recipe representation

A recipe is a plain JSON document describing one complete corruption.
Implement in `broken/recipe.py` as a dataclass with `to_dict` / `from_dict` and file load/save helpers.

```json
{
  "version": 1,
  "model": "spleeter:2stems",
  "seed": 1847,
  "mask": {
    "enabled": true,
    "clamp": false,
    "ops": [
      { "op": "quantize", "levels": 8 },
      { "op": "time_shift", "frames": 4 }
    ]
  }
}
```

**`ops` is an ordered list and order is significant.**
Quantizing then shifting is not the same as shifting then quantizing.
This deviates from the flat dictionary sketched in `PROJECT_SPRINGBOARD.md` §7; the list is correct and the springboard sketch is not binding.

**`enabled: false`, or an empty `ops` list, must produce the bypass path** — that is, `separate()` with no mask feeding at all, not an identity operation fed through the placeholder.
Both give the same audio, but only the former proves the bypass is structural.

**`clamp`** applies `clip(M, 0, 1)` once after the whole chain.
Default `false`.

**Seeding.**
`noise` is the only stochastic operation.
An op entry may carry its own `"seed"`, which wins.
Otherwise derive it deterministically from the recipe seed and the operation's index in the chain, so two `noise` entries in one recipe do not produce identical realizations.
Document in a docstring that reordering or inserting operations changes derived seeds — that is expected, and an explicit per-op seed is the escape hatch.

Unknown `op` names, unknown parameters, and out-of-domain values (`levels < 2`, `gamma <= 0`) must raise a clear error naming the offending entry.
Do not silently ignore anything.

### 5.3 Command line

Add `broken/__main__.py`, invoked as `python -m broken`.

**Do not add a console script entry point.**
That requires editing `pyproject.toml`, which §2 forbids.

Subcommands:

- **`render INPUT --recipe R.json -o DIR`**
  Render one recipe.
  `--offset` and `--duration` in seconds, passed through to `load_audio`.
- **`sweep INPUT --op OP --param NAME --values V1,V2,... -o DIR [--recipe BASE.json]`**
  Render one operation across several values of one parameter.
  With `--recipe`, the swept operation is appended to that base chain; without, it is the only operation.
  Must call `estimate_masks` once and reuse it — see §4.
- **`verify-bypass INPUT`**
  Render with the mask stage disabled and print the SHA-256 of each written stem.
  See §5.5.

**Millisecond conversion.**
`time_shift` sweeps are natural in milliseconds and `PROJECT_SPRINGBOARD.md` §18 specifies them that way, but the recipe stores frames.
Accept `--unit ms` on `sweep`, convert using `frame_step` from the model config and the sample rate, and **write the resolved frame count into each emitted recipe** so the artifact on disk is unambiguous.

### 5.4 Sweep output

Every rendered variation must be self-describing.

```
DIR/<input stem>/<variation label>/vocals.wav
                                  /accompaniment.wav
                                  /recipe.json
```

The variation label identifies the operation and value, for example `time_shift.frames=4`.
Sanitize it for the filesystem; this runs on Windows, where `:` and `*` are illegal in paths and a negative value's `-` is fine but a leading one is worth checking.

The emitted `recipe.json` must be a complete, re-renderable recipe — not a fragment.
Rendering it with `render` should reproduce the audio beside it.

### 5.5 Verification

**Unit tests — `tests/test_broken_masks.py`.**
Pure NumPy against small synthetic arrays.
No model, no checkpoint download, no network, no audio files.
These run as part of the default `pytest tests/` and must be fast.

Cover, per operation:

- the arithmetic, against hand-computed expected values
- dtype is `float32` on return
- purity: the input array is unchanged after the call
- shifts in both directions, with `wrap` both ways, including shifts larger than the axis
- `quantize` at `levels=2` and at a level count that divides evenly
- `noise` reproduces with the same seed and differs with a different one
- invalid arguments raise

Plus recipe round-trip: `to_dict` → JSON → `from_dict` is lossless, and malformed recipes raise.

**Bypass check — a CLI subcommand, deliberately not a pytest gate.**

`verify-bypass` renders `audio_example.mp3` with the mask stage disabled and prints the SHA-256 of each stem.
Compare against the values recorded in `ENVIRONMENT.md` §3.4.

This is **not** a test.
Those hashes are specific to TensorFlow 2.12.1 on CPU, this checkpoint, and this FFmpeg build, and they will legitimately change if any of those change.
A failing build is the wrong way to learn that.
Print the comparison and let a human read it.

`ENVIRONMENT.md` §3.4 also documents a separate periodic determinism check that compares two fresh renders to each other rather than to a recorded constant.
Do not replace it, and do not turn either check into a default-gated test.

---

## 6. Definition of done

- Eight mask operations implemented, matching §5.1 exactly.
- Recipe load, save, validate, and apply, with ordered operations and deterministic seeding.
- `python -m broken render`, `sweep`, and `verify-bypass` all working.
- A sweep reuses one analysis and is visibly faster per variation than a full render.
- `pytest tests/` passes, including the new unit tests.
- `black broken spleeter --check`, `isort broken spleeter --check`, and `flake8 broken` are clean.
- `verify-bypass` reproduces the hashes in `ENVIRONMENT.md` §3.4.
- Nothing under `spleeter/` modified; `pyproject.toml` and `poetry.lock` untouched.
- `CHANGELOG.md` has an entry under a new dated heading, and `ROADMAP.md` item A2 is updated to reflect what landed.
- Nothing committed.

Report what you actually ran and what it printed.
If something does not pass, say so with the output rather than describing it as done.

---

## 7. Out of scope

Do not build any of this, even if it seems adjacent or easy:

- weight, checkpoint, or BatchNorm corruption (roadmap A4)
- activation hooks or any change to `spleeter/model/functions/unet.py` (A5)
- recursive processing (A6)
- multi-model disagreement or ensembles (A7)
- phase or reconstruction manipulation (A8)
- any GUI (A9)
- mask blur, correlated noise, or operations not listed in §5.1
- console script entry points, packaging changes, distribution
- continuous integration
- caching, parallelism, or performance work beyond reusing one analysis per sweep

---

## 8. Surface, do not decide

Some choices in this brief are provisional and belong to the project owner.
Implement them as written, then say what you noticed.

- **Clamping defaults to off** and shifts default to zero-fill.
  Both are guesses about what sounds useful.
  If working with them suggests otherwise, note it — do not change the default.
- **The `threshold` soft formula** is one plausible curve among several.
- **Operation order** in a recipe is the user's to compose; do not add reordering logic or "sensible" defaults.
- If an operation's specified math seems musically wrong, **implement it as specified and flag it.**
  The whole point of this slice is that nobody knows yet which failures are useful; a plausible-sounding correction made silently destroys the comparison.
- If you hit something in the codebase that contradicts this brief, trust the code and report the contradiction.

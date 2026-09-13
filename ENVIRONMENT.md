# Broken Spleeter — Development Environment

Canonical, maintained record of how the development environment is built and verified.
Every command here was executed successfully; nothing is aspirational.

**Keep this document current.**
When the environment changes, update this file rather than adding a new one.
`WINDOWS_INIT_SESSION.md` is the historical bootstrap brief and is not maintained.

**Verified on:** Windows 11 Home 10.0.26200, 2026-09-02.
Linux and macOS are unverified — see [Platform support](#platform-support).

---

## 1. Requirements

| Component | Version | Why pinned |
|---|---|---|
| Python | 3.11.x | `pyproject.toml` requires `>=3.8,<3.12`; 3.11 is the newest allowed |
| TensorFlow | 2.12.1 | The baseline this project manipulates — see [Baseline fidelity](#baseline-fidelity) |
| FFmpeg | any recent build | Audio I/O; must be on `PATH` |
| Poetry | >= 2.0 | `poetry.lock` is lock-version 2.1 and unreadable by Poetry 1.x |

Python 3.12+ will not work.
TensorFlow 2.12.1 publishes no wheels for it.

---

## 2. First-time setup (Windows)

Assumes nothing but `winget`.
The system Python is left untouched — this workstation's default is 3.14.3 and stays that way.

### 2.1 Interpreter

[uv](https://docs.astral.sh/uv/) supplies the interpreter.
It is not used for dependency resolution; that remains Poetry's job.

```powershell
winget install --id astral-sh.uv --source winget
uv python install 3.11.16
```

The interpreter lands in `%APPDATA%\uv\python\cpython-3.11.16-windows-x86_64-none\` and does not become any kind of system default.
uv does register it with the `py` launcher (visible as `py -V:Astral/CPython3.11.16`) and places `python3.11.exe` in `%USERPROFILE%\.local\bin`, but bare `python` is unaffected.

### 2.2 Virtual environment

```powershell
uv venv .venv --python 3.11.16 --seed
.\.venv\Scripts\Activate.ps1
```

`--seed` provides `pip`, `setuptools` and `wheel` inside the venv.

If `Activate.ps1` is blocked, check `Get-ExecutionPolicy -List`; `RemoteSigned` for `CurrentUser` is sufficient and is the default on this machine.

### 2.3 FFmpeg

```powershell
winget install --id Gyan.FFmpeg --source winget
```

Installs `ffmpeg`, `ffprobe` and `ffplay`, and adds them to `PATH`.
**A PATH change from winget is only visible in newly launched shells** — restart the terminal before continuing.

### 2.4 Poetry

Installed as an isolated tool so it never enters the project venv.
Poetry managing the environment it lives inside is a known source of breakage.

```powershell
uv tool install poetry==2.0.1
```

Pinned to the version that generated `poetry.lock`.
Any Poetry >= 2.0 should work.

### 2.5 Dependencies

Bind Poetry to the venv created above, otherwise it creates its own under `%APPDATA%\pypoetry\virtualenvs\` and ignores this one:

```powershell
poetry env use .venv\Scripts\python.exe
poetry install
```

`poetry install` installs the main and dev groups plus the `spleeter` package itself in editable mode, so `import spleeter` resolves to the working tree and source edits take effect without reinstalling.

Optional evaluation extras (`musdb`, `museval`) are already part of the dev group; they are *not* installed by `poetry install --only main`.

---

## 3. Verification

All of the following are confirmed working.

### 3.1 Environment

```powershell
python --version                                  # Python 3.11.16
python -c "import sys; print(sys.executable)"     # ...\broken-spleeter\.venv\Scripts\python.exe
ffmpeg -version
spleeter --version                                # Spleeter Version: 2.4.2
```

`spleeter --version` resolves through `importlib.metadata.version("spleeter")`, so it also confirms the package metadata is installed correctly.

### 3.2 Baseline separation

```powershell
spleeter separate -p spleeter:2stems -o output audio_example.mp3
```

Writes `output/audio_example/vocals.wav` and `accompaniment.wav`.
On first run this downloads the `2stems` checkpoint (~76 MB); expect roughly 20 s including the download on CPU, a few seconds after the model is cached.

`output/` and `pretrained_models/` are both gitignored.

### 3.3 Tests

Fast tier, covering `broken/` — about 5 seconds, no model build, no checkpoints:

```powershell
pytest tests/test_broken_masks.py tests/test_broken_cli.py
```

Full suite:

```powershell
pytest tests/
```

Passes in about 4 minutes on CPU (68 tests, 2026-09-13).
Nearly all of that time is inherited tests: `test_separator.py` separates real audio for every model and input combination, and `test_train.py` runs a training loop.
Which tier to run when is recorded in `AGENTS.md`.

Individual areas:

```powershell
pytest tests/test_ffmpeg_adapter.py               # audio I/O
pytest tests/test_separator.py -k 2stems          # separation, without pulling 4/5stems
```

`test_separator.py` parametrizes over 2stems, 4stems and 5stems.
Running it unfiltered downloads all three checkpoints (~417 MB total).

### 3.4 Render determinism

Separation is **bitwise reproducible across processes** on this machine, verified 2026-09-08 at both the NumPy array level and the written WAV.
FFmpeg embeds no varying metadata in the WAV output, so file hashes are a valid check.

This matters more here than in ordinary Spleeter use.
The project's premise is *repeatable* model failure, so if unmodified inference were not reproducible, every later question about whether a seed reproduces a sound would be confounded.

`tf.config.experimental.enable_op_determinism()` is **not** needed and should not be enabled — it carries a speed cost for a guarantee already held.

#### Periodic check

Run two full renders and compare them to each other:

```powershell
spleeter separate -p spleeter:2stems -o output\det_a audio_example.mp3
spleeter separate -p spleeter:2stems -o output\det_b audio_example.mp3
$a = (Get-FileHash output\det_a\audio_example\*.wav | Sort-Object Path).Hash
$b = (Get-FileHash output\det_b\audio_example\*.wav | Sort-Object Path).Hash
if (Compare-Object $a $b) { "DIFFERENT" } else { "identical" }
```

`output\det_a` and `output\det_b` are disposable; `output/` is gitignored.

This is a **self-comparison** and never goes stale.
It stays valid after a TensorFlow bump, a checkpoint change, or a threading change, because it pins no absolute value — it only asks whether two runs under whatever conditions currently hold agree with each other.

It is deliberately **not** a pytest gate.
A failing build is the wrong way to learn about this, and the check costs two full renders.
Run it when something upstream of inference changes, or when a seed stops reproducing a sound and the cause is unclear.

#### Absolute hashes, for drift diagnosis only

SHA-256 of the 2stems render of `audio_example.mp3`, recorded 2026-09-08:

| Stem | Hash |
|---|---|
| `vocals.wav` | `a4ceacf9e24656693d344dd0231b3ade323ab2be5256bffd65c5c0472bff30a3` |
| `accompaniment.wav` | `a3fd23625abe7003926255d65261c0a54acdb0cbd97f2efc597d8a67626a79f1` |

Valid only for TensorFlow 2.12.1 on CPU, the `2stems` checkpoint from the upstream `v1.4.0` release, and FFmpeg 9.0.1.

These are a diagnostic, not a guarantee.
A change here is **expected** if any of those conditions change and does not by itself indicate a problem — it answers "did the baseline move?", which is a different question from "is inference deterministic?".

---

## 4. Pretrained models

Downloaded on first use from the upstream `deezer/spleeter` `v1.4.0` release into `pretrained_models/<name>/`, checksum-validated on arrival, with a `.probe` marker written on success so later runs skip the download.

| Model | Size on disk |
|---|---|
| `2stems` | 76 MB |
| `4stems` | 152 MB |
| `5stems` | 190 MB |

Two environment variables affect this and should normally stay unset:

- **`GITHUB_REPOSITORY`** — the provider falls back to it when locating checkpoints.
  GitHub Actions sets it automatically, which silently redirects downloads to this fork and fails.
  Never set it.
- **`MODEL_PATH`** — overrides the `pretrained_models` cache directory.

---

## 5. Platform support

### Windows

Verified end to end.
Note that the environment could **not** be built from the inherited lock as it stood; `pyproject.toml` and `poetry.lock` now carry platform markers that make Windows a first-class target:

- `tensorflow-io-gcs-filesystem` resolves to **0.31.0 on Windows**, 0.32.0 elsewhere.
  Upstream published no Windows wheels for 0.32.0; 0.31.0 is the last version that has them.
- `tensorflow-intel==2.12.1` is declared for Windows only.
  The `tensorflow` wheel for Windows is a ~2 KB metadata stub that requires it; the actual 272 MB build is `tensorflow-intel`.

These markers are load-bearing.
Removing them breaks `poetry install` on Windows.

**If a future change touches the TensorFlow pin, re-verify by installing from the lock into a *fresh* venv, not the existing one.**
An already-satisfied environment reports success without ever exercising platform selection, so the check passes while the lock is still broken for anyone starting clean.

The relock that added these markers used plain `poetry lock`; Poetry 2.0 preserves existing versions and only `--regenerate` re-resolves.
It added exactly one package and drifted zero versions.

### GPU

**Not available on Windows at this TensorFlow version.**
Google dropped native Windows GPU support after TensorFlow 2.10, so `tf.config.list_physical_devices()` reports CPU only regardless of installed hardware.
All inference and training currently run on CPU.

Restoring GPU support means choosing between WSL2 with CUDA (keeps TF 2.12.1 and the exact baseline), a newer TensorFlow (requires re-validating the pretrained-model reference state), or `tensorflow-directml-plugin` (native Windows, poorly maintained).
This is an open decision, not a settled plan.

### Linux and macOS

Unverified since the fork.
The lock resolves for them and upstream CI exercised them, but no session has run them here.
Expect the markers above to route these platforms to the original dependency set.

---

## 6. Baseline fidelity

The unmodified pretrained model is this project's reference state, and the TensorFlow pin exists to protect it.
Changes to Python, TensorFlow, packaging, or model loading can alter the behavior this project exists to manipulate, so they are not ordinary cleanup — raise them explicitly rather than bundling them into unrelated work.

The two Windows deviations above were forced by upstream packaging and do not change model behavior: `tensorflow-intel` **is** TensorFlow 2.12.1 under the name Windows ships it as, and `tensorflow-io-gcs-filesystem` provides GCS/S3 filesystem plugins that local inference never touches.

---

## 7. Known issues

**FFmpeg version sensitivity in tests.**
Newer FFmpeg reports mp3 duration accounting for LAME encoder delay and padding; older versions did not.
The difference is ~1704 samples at 44.1 kHz.
`tests/test_ffmpeg_adapter.py` therefore asserts duration with a tolerance rather than an exact value.
Verified against FFmpeg 9.0.1.

**`pytest-forked` is unused.**
`--forked` was removed from the default `addopts` because `pytest-forked` requires `os.fork()`, which does not exist on Windows.
The package is still a dev dependency, so `pytest tests/ --forked` remains available on POSIX for opt-in per-test process isolation.
The suite has been verified to pass without it.

**Legacy Poetry metadata format.**
`pyproject.toml` declares project metadata under `[tool.poetry]` rather than PEP 621's `[project]`.
Poetry 2.x supports this and ordinary commands are silent about it, but `poetry check` reports a warning per field.

Migrating is a real decision, not cleanup.
`[project]` changes how the distribution name, version, classifiers, extras and console scripts are declared — and `spleeter --version` resolves through `importlib.metadata.version("spleeter")`, so a mistake there breaks the CLI.
Poetry also stops auto-deriving classifiers once they move to `[project]`.
Do this deliberately, with `spleeter --version` and `pytest tests/test_command.py` as the check.

# Development Environment

**Live and authoritative** for setup, verified commands, and platform facts.

This file separates what has been verified from what is intended.
Move an item from section 2 to section 1 only after running it, and date it.

---

## 1. Verified

### The carried NumPy code

Verified 2026-11-15 in a Linux cloud container, Python 3.13.18, NumPy 2.5.4, in an environment created by `uv sync` from the seed `pyproject.toml`.

```bash
uv sync
uv run pytest                          # 27 passed, under a second
uv run black broken tests --check
uv run isort broken tests --check
uv run flake8 broken tests
```

All five passed.
Not verified on Windows.
No `uv.lock` is committed; the first `uv sync` on the workstation creates it, and P1 should commit it once `torch` is declared.

The prototype pinned `numpy < 2.0`; the carried code passes on NumPy 2.x without changes.

### Facts about the `demucs` package

Verified 2026-11-15 by reading the 4.1.0 source distribution from PyPI.
Nothing was installed or executed.

- Latest version on PyPI is 4.1.0.
- `Requires-Python: >=3.10`.
- Requires `torch >= 2.1`, plus `einops`, `huggingface-hub`, `julius`, `lameenc`, `pyyaml`, `safetensors`, `sphn`, `tqdm`.
- `torchaudio` is required only by the `train` extra.

Architecture facts from the same reading are in `CONCEPT.md` section 7.

### The workstation, as of the prototype

Carried from the prototype's environment record, last verified there 2026-09-13.
Not re-verified for this project.

- Windows 11, RTX 3080 Ti.
- `uv` installed, and used to provide a project-local Python in `.venv/`.
- FFmpeg installed through winget and on `PATH`.
- The system Python is 3.14 and was deliberately left untouched.

---

## 2. Intended, not yet verified

Roadmap item P1 owns all of this.

- **Python version.**
  Any version from 3.10 that both `torch` and `demucs` support on Windows.
  The prototype used 3.11.
- **PyTorch with CUDA.**
  The CUDA builds are served from PyTorch's own wheel index, not from PyPI's default.
  Pin the index in `pyproject.toml` so a fresh install cannot silently resolve to a CPU build.
- **`demucs` 4.1.0** installed alongside it.
- **Tooling.**
  `uv` alone is the recommended default, since it is already installed and manages both the interpreter and the lock.
  The prototype also used Poetry; nothing here needs it.
- **GUI toolkit.**
  PySide6, when roadmap item P3 starts.

Checks to run and record:

1. `torch.cuda.is_available()` is true and names the 3080 Ti.
2. A stock `htdemucs` render of a region of a full mix succeeds on the GPU.
3. Render time for a 10 to 20 second region.
4. Two identical renders compared sample for sample, with and without `torch.use_deterministic_algorithms(True)`, and the speed difference.
5. Where the pretrained checkpoint is cached on disk, and its size.
6. How the package's audio loading and saving behave on Windows, and whether FFmpeg is needed at all.

---

## 3. Known issues

None recorded for this project yet.

One carried warning from the prototype: verify a dependency change by installing into a **fresh** environment.
An already-satisfied environment reports success without exercising platform-specific resolution.

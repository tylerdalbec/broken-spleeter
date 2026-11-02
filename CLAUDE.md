@AGENTS.md

## Claude Code Specific

### Claude desktop app AppData redirect

The Claude desktop app on this machine is an MSIX package (`C:\Program Files\WindowsApps\Claude_..._pzs8sxrjxfjjc\`).
Windows redirects writes to `%APPDATA%` / `%LOCALAPPDATA%` from it and from every process it spawns (Bash, PowerShell, the terminal pane, Run buttons) into `%LOCALAPPDATA%\Packages\Claude_pzs8sxrjxfjjc\LocalCache\`.
Inside Claude those files appear at the normal path; Explorer, ordinary terminals, and non-Claude agents do not see them.
Paths outside AppData (the repository, `~\.local\bin`) and winget installs are real.

- Never run user-level installs (`uv python install`, `uv tool install`, global `pip`, anything writing to AppData) from a Claude session.
  Give the user the command to run in their own terminal instead.
- A path check from inside a Claude session can pass while the thing is missing for everyone else.
  When a tool exists for Claude but not for another agent or Explorer, check `LocalCache` under the Claude package first.
- A stale real `~\.local\bin\poetry.exe` blocks a reinstall; `uv tool install poetry==2.0.1 --force` replaces it.

This is a Claude-side problem, not a project environment fact, so it stays out of `ENVIRONMENT.md` and `AGENTS.md`.

### Windows platform markers

`AGENTS.md` §Environment states that the platform markers in `pyproject.toml` and `poetry.lock` are load-bearing on Windows.
The marker block is:

```toml
tensorflow-io-gcs-filesystem = [
    {version = "0.32.0", markers = "platform_system != 'Windows'"},
    {version = "0.31.0", markers = "platform_system == 'Windows'"},
]
tensorflow = "2.12.1"
tensorflow-intel = {version = "2.12.1", markers = "platform_system == 'Windows'"}
```

- Do not clean up these markers or collapse the `tensorflow-io-gcs-filesystem` list back to a single pin.
- The Windows `tensorflow` wheel is a metadata stub that requires `tensorflow-intel`, which a Linux-resolved lock omits entirely.
- Neither marker changes model behavior: `tensorflow-intel` is TensorFlow 2.12.1 under the name Windows ships it as, and the tf-io package only provides GCS/S3 filesystem plugins that local inference never touches.
- If a change touches the TensorFlow pin, re-verify by installing from the lock into a fresh venv, not the existing one.
  An already-satisfied environment reports success without exercising platform selection.
- Relock with plain `poetry lock`, which preserves existing versions under Poetry 2.0; only `--regenerate` re-resolves.

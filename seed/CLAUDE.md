@AGENTS.md

## Claude Code Specific

### Claude desktop app AppData redirect

The Claude desktop app on the Windows workstation is an MSIX package (`C:\Program Files\WindowsApps\Claude_..._pzs8sxrjxfjjc\`).
Windows redirects writes to `%APPDATA%` / `%LOCALAPPDATA%` from it and from every process it spawns (Bash, PowerShell, the terminal pane, Run buttons) into `%LOCALAPPDATA%\Packages\Claude_pzs8sxrjxfjjc\LocalCache\`.
Inside Claude those files appear at the normal path; Explorer, ordinary terminals, and non-Claude agents do not see them.
Paths outside AppData (the repository, `~\.local\bin`) and winget installs are real.

- Never run user-level installs (`uv python install`, `uv tool install`, global `pip`, anything writing to AppData) from a Claude session.
  Give the user the command to run in their own terminal instead.
- A path check from inside a Claude session can pass while the thing is missing for everyone else.
  When a tool exists for Claude but not for another agent or Explorer, check `LocalCache` under the Claude package first.
- Before recording a model cache path in `ENVIRONMENT.md`, confirm from an ordinary terminal where the checkpoint actually landed.
  Caches under `~\.cache` are outside AppData and should be real, but this is unverified for this project.

This is a Claude-side problem, not a project environment fact, so it stays out of `ENVIRONMENT.md` and `AGENTS.md`.

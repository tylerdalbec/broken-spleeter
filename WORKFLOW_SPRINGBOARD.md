# Broken Spleeter
## Workflow Springboard

**Repository:** `tylerdalbec/broken-spleeter`  
**Companion document:** `PROJECT_SPRINGBOARD.md`  
**Status:** Provisional workflow/bootstrap guidance to be reviewed and refined with a repository-aware coding agent.

---

## 1. Purpose

This document is a starting point for setting up the development workflow around Broken Spleeter.

It is intentionally **not**:

- a project roadmap
- an implementation brief
- a frozen repository policy
- a final environment specification
- a requirement to reproduce the workflow structure of another project

Its purpose is to make the first repository-aware setup sessions efficient and deliberate.

The companion `PROJECT_SPRINGBOARD.md` describes the experimental software concept, likely technical directions, and open implementation questions.

This document describes the surrounding working method:

- how the inherited Spleeter fork should be cleaned up
- how Claude Code and Codex should be given project context
- how much agent infrastructure should exist initially
- how Git and Python setup should be approached
- how cloud and workstation sessions should divide responsibilities
- how planning, implementation, verification, and handoff should interact
- which decisions should remain open until an agent can inspect the actual repository and development environment

Both springboard documents are hypotheses.

A local or cloud coding agent should be encouraged to challenge them when repository evidence or tooling constraints justify a different approach.

---

## 2. Working Context

Broken Spleeter begins as a direct fork of `deezer/spleeter`.

At the time this workflow document was drafted, the fork had not yet received Broken Spleeter-specific code changes.

The useful consequence is that there is currently a clean boundary between:

1. inherited Spleeter history and infrastructure
2. the future Broken Spleeter project

That boundary should be preserved conceptually even if the repository continues to use Spleeter's Git history.

The project does **not** need to remain synchronized with upstream Spleeter.

Upstream compatibility should not constrain architecture, cleanup, dependency changes, or internal modifications.

The upstream repository is primarily relevant as provenance and as a historical reference for inherited behavior.

At the time of drafting, the inherited upstream baseline was `c8854001ac8acad34a9bc2bd15f28475541828b1` (Deezer Spleeter `master`).
The bootstrap agent should verify and record that provenance, but there is no current need to maintain an `upstream` remote or an upstream-sync workflow.

---

## 3. Workflow Goal

The desired workflow is lighter than the one used in `granular_tui`.

Broken Spleeter is intended to be a smaller, more exploratory project.

The workflow should provide enough structure that Claude Code and Codex can work safely and coherently across sessions without requiring a large process framework.

The initial workflow should optimize for:

- fast orientation
- explicit distinction between planning and implementation
- reproducible environment setup
- low documentation overhead
- clear session boundaries
- easy recovery after an interrupted or exploratory session
- minimal duplicated process machinery
- room to add stronger workflow structure later if the project actually grows into it

The project should not begin by copying a mature repository's full documentation taxonomy, skill set, audit system, or CI policy.

Those systems should appear only when repeated friction demonstrates a real need.

---

## 4. Initial Agent-Facing Documentation

A minimal initial documentation set is likely sufficient:

```text
README.md
AGENTS.md
CLAUDE.md
PROJECT_SPRINGBOARD.md
WORKFLOW_SPRINGBOARD.md
```

The exact layout may be refined by the first repository-aware agent.

### `PROJECT_SPRINGBOARD.md`

This is the product/technical concept document.

It explains what Broken Spleeter is trying to explore and identifies technical questions that should be reconciled against the real Spleeter codebase.

It should remain a working hypothesis rather than an executable roadmap.

### `WORKFLOW_SPRINGBOARD.md`

This document defines the initial workflow assumptions and bootstrap questions.

It should eventually either:

- remain as lightweight project context,
- be replaced by more concrete workflow documentation,
- or be reduced after the initial setup is stable.

### `AGENTS.md` and `CLAUDE.md`

These files are required because Codex and Claude Code are both first-class development agents for the project.

They should be **byte-identical mirrors**.

Any edit to one should be applied identically to the other.

The initial files should be deliberately short.

They should contain only instructions that an implementation agent needs on nearly every session, such as:

- where to find project context
- which source of instructions takes precedence
- baseline build/test/verification commands once known
- project-wide engineering constraints once discovered
- important environment assumptions
- documentation or workflow rules that are genuinely universal
- the mirroring requirement itself

The initial agent files should **not** attempt to contain the full project design.

They should point to the springboards rather than duplicate them.

### Skills

Do not seed a large `.agents/skills/` / `.claude/skills/` ecosystem merely because another project uses one.

If a repeated workflow later becomes cumbersome enough to deserve a dedicated skill, add it deliberately and mirror it between both agent systems.

Possible future candidates might include orientation, handoff, implementation-brief execution, or specialized verification.

None are initial requirements.

---

## 5. Instruction Precedence

The project should make task authority explicit.

A useful starting hierarchy is:

```text
latest direct user instruction
        ↓
explicitly named implementation brief, if one is being used
        ↓
AGENTS.md / CLAUDE.md
        ↓
WORKFLOW_SPRINGBOARD.md
        ↓
PROJECT_SPRINGBOARD.md
        ↓
inherited Spleeter documentation
```

Planning documents should not become executable merely because they exist in the repository.

An agent should only treat a brief or plan as an implementation contract when the user explicitly names it as the source for the current task.

`PROJECT_SPRINGBOARD.md` should be treated as design context, not a specification.

Repository evidence is allowed to contradict its technical assumptions.

---

## 6. General Agent Behavior

Agents working in this repository should initially follow a few broad principles.

### Inspect before redesigning

Inherited Spleeter code, tests, configuration, model behavior, and dependency constraints should be inspected before broad changes are made.

### Do not silently modernize dependencies

Dependency modernization may be desirable, but it is not ordinary cleanup.

Changes to Python, TensorFlow, packaging, or model-loading infrastructure can alter the baseline behavior that the project is trying to manipulate.

Such changes should be investigated and discussed explicitly.

### Distinguish findings from decisions

An agent may discover that an inherited assumption is outdated or that one architecture is easier than another.

That finding should not silently become permanent project policy.

Consequential choices should be surfaced so they can be accepted, rejected, or deliberately prototyped.

### Prefer reversible exploration

This is an experimental project.

Agents should be allowed to prototype and investigate rather than requiring every exploratory change to be preceded by a formal design process.

At the same time, exploratory work should remain easy to identify and discard.

### Do not over-preserve upstream structure

The project is not trying to remain merge-compatible with Deezer Spleeter.

Inherited organization should be kept only when it remains useful.

---

## 7. Recommended Pre-Clone Cloud Bootstrap

A Claude Code cloud session is a good place to perform the first repository bootstrap before the repository is ever cloned onto the Windows workstation.

Claude cloud sessions already operate on temporary branches, so no additional bootstrap-branch convention is required.

The cloud bootstrap should focus on repository-level changes that do not depend on the Windows runtime environment.

The agent should inspect the inherited repository before applying deletions, but the current working recommendation is:

### Likely removal candidates

- inherited `.github/` community and workflow infrastructure
- GitHub Actions for Conda, Docker, PyPI publishing, and upstream testing
- inherited `CODEOWNERS`, contribution instructions, issue templates, and PR template
- `docker/`
- `conda/` packaging recipes
- Spleeter paper/publication files
- paper images or other publication-only assets
- the demo notebook if it does not serve the Broken Spleeter workflow
- the inherited upstream changelog

These files remain available through Git history and the original upstream repository.

They do not need to remain in the active project tree merely for historical preservation.

### Likely preservation candidates

Do not aggressively remove material that may be needed to establish the inherited baseline.

Initially preserve:

- `spleeter/`
- `configs/`
- `tests/`
- `pyproject.toml`
- `poetry.lock`
- `.flake8`
- `.gitignore`
- `LICENSE`
- the small inherited audio examples
- any other files the agent determines are involved in ordinary Spleeter execution or testing

The inherited audio examples may be particularly useful as known inputs during baseline verification.

They can be reconsidered after Broken Spleeter has deliberate test fixtures.

### README and project identity

The inherited README should be replaced with a minimal Broken Spleeter README.

The first version does not need to document the future application in detail.

It should primarily establish:

- project identity
- experimental purpose
- relationship to Spleeter
- provenance/license context
- pointers to `PROJECT_SPRINGBOARD.md` and `WORKFLOW_SPRINGBOARD.md`

### Bootstrap commit

The first Broken Spleeter-specific commit should ideally form a clean project-bootstrap boundary.

It can contain:

- inherited repository cleanup
- the two springboard documents
- mirrored `AGENTS.md` / `CLAUDE.md`
- the initial project README

This makes later history easier to understand because experimental source changes begin after the repository has already been reoriented around Broken Spleeter.

---

## 8. Cloud vs. Workstation Responsibilities

The project currently expects two primary development environments.

### Claude Code cloud containers

Linux cloud sessions are suitable for:

- repository administration
- documentation work
- code inspection
- planning
- source changes that do not depend on Windows-specific behavior
- portable tests once the environment is understood
- pull requests or branch-based experimentation if useful

The project should not initially create elaborate Linux-vs-Windows rules.

Machine scoping can be formalized later if real differences begin affecting correctness.

### Windows workstation

The Windows workstation should initially be treated as the authoritative environment for establishing that the inherited application stack actually works.

This is where the first local agent should help with:

- Git setup after cloning
- Python interpreter strategy
- virtual environment setup
- FFmpeg or other native dependencies
- dependency installation
- model download/cache behavior
- baseline Spleeter execution
- later GUI/audio audition work

### Raspberry Pi

The Raspberry Pi is currently out of scope.

It should not shape initial architecture or workflow decisions.

If the project expands materially beyond the scope described in `PROJECT_SPRINGBOARD.md`, machine support can be reconsidered then.

---

## 9. Python Environment: Known Issue, Open Decision

> **Resolved 2026-09-02.**
> Python **3.11.16**, supplied by **uv**, in a project-local `.venv`.
> The system 3.14.3 was left untouched.
> Poetry was retained as the dependency manager.
> The hypothesis below was correct in substance; see `ENVIRONMENT.md` for the actual commands.
> One assumption was wrong: the inherited lockfile could not install on Windows at all, and `pyproject.toml` now carries platform markers to fix that.

The development workstation currently uses Python 3.14.3.

The inherited Spleeter project declares an older Python range and currently pins an older TensorFlow stack.

Therefore the first local agent should **not** assume that the system Python can be used directly.

Creating `.venv` from Python 3.14.3 would still create a Python 3.14 environment; a virtual environment isolates packages but does not provide a different interpreter version.

The first Windows environment session should explicitly investigate the interpreter strategy.

A likely low-risk path is to use a project-managed compatible Python interpreter for the initial baseline while leaving the workstation's system/default Python installation unchanged.

Tools such as `uv`, `pyenv-win`, or another appropriate interpreter manager may be considered.

No particular tool is mandated by this springboard.

The initial goal is:

> establish one reproducible environment in which inherited Spleeter behavior can be run and tested before major dependency or source modernization.

Once that reference environment exists, the project can separately evaluate whether upgrading TensorFlow, Python compatibility, packaging, or dependency management is worthwhile.

The local agent should explain the concrete commands during setup rather than assuming they are memorized.

This includes:

- installing or selecting the project interpreter
- creating `.venv`
- activating it
- installing dependencies
- verifying which interpreter and packages are active
- locating FFmpeg or other native dependencies
- running a baseline command
- documenting the resulting setup once it is known to work

The workflow document should not freeze those commands before the local environment has been inspected.

---

## 10. Git Setup Expectations

The first local agent should also treat Git setup as an interactive bootstrap task rather than assuming every command is already memorized.

The user is comfortable with Git/GitHub concepts but may want explicit guidance for the exact commands being used.

The local session should verify:

- current branch and repository status
- configured remotes
- authentication behavior if relevant
- normal pull/push workflow
- how Claude cloud branches and local branches interact
- how to inspect or recover changes before destructive operations

There is currently no need to configure a persistent `upstream` remote to `deezer/spleeter`.

The project is expected to diverge freely.

If an upstream reference is ever useful, it can be added later.

---

## 11. Lightweight Development Lifecycle

The default workflow should be simple:

```text
orient
  ↓
discuss / plan when necessary
  ↓
implement
  ↓
verify
  ↓
handoff only when useful
```

### Orient

Read the project-level instructions and only the repository areas needed for the current task.

The first repository-aware technical session is an exception because its purpose is broad reconnaissance.

### Discuss / plan

Not every task needs a formal planning artifact.

A direct user request can be sufficient for small or exploratory changes.

A named implementation brief becomes useful only when a change is large enough that preserving an agreed execution contract adds value.

### Implement

Follow the latest user instruction or explicitly named brief.

Do not treat unrelated planning files as work queues.

### Verify

Verification requirements should initially remain proportional to the change.

The project should establish real baseline commands before `AGENTS.md` / `CLAUDE.md` claim that particular commands are mandatory gates.

Audio-related work may eventually need render/listening verification distinct from ordinary tests, but that policy should emerge from actual project needs.

### Handoff

Do not create a handoff file automatically at the end of every session.

Use one when meaningful state must survive between sessions.

A lightweight handoff can initially contain:

- settled decisions
- open questions
- important findings
- next actions

A more formal routing system is unnecessary unless handoff management itself becomes a recurring problem.

---

## 12. What Not to Import From `granular_tui` Yet

Do not begin with equivalents of the mature project's full workflow infrastructure.

In particular, there is no current need for:

- a large `ARCHITECTURE.md`
- `MAP.md`
- a roadmap-management system
- a large glossary/reference corpus
- implementation-brief templates
- dedicated brief-audit workflows
- generalized documentation audits
- PR lifecycle skills
- specialist runtime/audio audits
- handoff routing queues
- mandatory CI
- a large mirrored skill tree

Some of these may become valuable later.

They should be introduced because Broken Spleeter needs them, not because they exist in another repository.

---

## 13. Suggested First Claude Cloud Session

The first cloud session should remain a bootstrap session rather than becoming the first feature-development session.

A useful goal is:

> transform the untouched Spleeter fork into a clean Broken Spleeter repository that is ready to clone locally and ready for a repository-aware environment/setup session.

The cloud agent should:

1. Read `PROJECT_SPRINGBOARD.md` and `WORKFLOW_SPRINGBOARD.md`.
2. Inspect the repository rather than blindly applying the cleanup list.
3. Verify which inherited files are clearly publication/release/community infrastructure versus actual runtime/test dependencies.
4. Propose any changes to the recommended cleanup before making broad deletions.
5. Perform the agreed repository cleanup.
6. Replace the README with a minimal Broken Spleeter landing page.
7. Create concise mirrored `AGENTS.md` and `CLAUDE.md`.
8. Keep those instruction files byte-identical.
9. Avoid adding a skill ecosystem unless a concrete need emerges during bootstrap.
10. Preserve the inherited dependency definitions until the local environment has been investigated.
11. Record the inherited Spleeter baseline/provenance.
12. Leave the repository in a state suitable for the first Windows clone.
13. Summarize what the local setup agent should investigate next.

The cloud agent should not begin implementing corruption systems, GUI features, or architectural changes from `PROJECT_SPRINGBOARD.md`.

---

## 14. Suggested First Windows Session

> **Completed 2026-09-02.**
> The brief used was `WINDOWS_INIT_SESSION.md` (retained as history); the outcomes are in `ENVIRONMENT.md`.
> Every topic listed below was covered except GPU expectations, which remain open.

After the cloud bootstrap is merged or otherwise accepted, clone the cleaned repository onto the Windows workstation.

The first local session should focus on the development environment and inherited baseline.

A useful goal is:

> establish a reproducible local environment, confirm what still works from inherited Spleeter, and convert unknown setup assumptions into documented facts.

Likely topics include:

- project-specific Python interpreter management
- `.venv`
- dependency installation
- Poetry versus another dependency workflow
- FFmpeg/native requirements
- TensorFlow behavior on the workstation
- CPU/GPU expectations
- pretrained model download/cache behavior
- ordinary Spleeter separation
- inherited tests
- practical verification commands
- any Windows-specific issues that should eventually be reflected in the mirrored agent instructions

The agent should guide Git and Python commands interactively and explain the purpose of each setup step.

This session should not feel pressure to solve the larger Broken Spleeter architecture at the same time.

Once the inherited baseline is understood, the project can move into the separate repository-aware design/reconnaissance work described in `PROJECT_SPRINGBOARD.md`.

---

## 15. Open Questions for Workflow Refinement

The first few coding-agent sessions should refine, rather than merely obey, this document.

Questions worth resolving include:

### Repository cleanup

- Does any apparently obsolete inherited infrastructure still support a useful baseline workflow?
- Should the demo notebook or audio examples survive beyond baseline verification?
- Is the inherited changelog useful enough to retain under a renamed historical location, or is Git history sufficient?

### Environment

- What Python version is the most practical baseline?
- What tool should manage the non-system Python interpreter?
- Should Poetry remain the dependency manager?
- Is the existing lockfile still usable on the selected interpreter/platform?
- Is dependency modernization necessary before meaningful experimentation?
- Which environment details need to be recorded for reproducibility?

> **All resolved 2026-09-02** — recorded in `ENVIRONMENT.md`.
> Python 3.11.16 · interpreter managed by uv · Poetry retained (>= 2.0, required to read the lock) · the lockfile was **not** usable as-is on Windows and now carries platform markers · no modernization was needed beyond those markers.
>
> **Still open:** GPU support.
> TensorFlow 2.12.1 has no native Windows GPU path, so all work is CPU-bound.
> Resolving it trades against baseline fidelity and is a real decision, not a cleanup task.

### Agent instructions

- What universal commands and constraints actually deserve to live in `AGENTS.md` / `CLAUDE.md`?
- Which instructions belong only in longer project documentation?
- Is any recurring workflow already complex enough to justify the first mirrored skill?

### Verification

- Which inherited tests are still meaningful for Broken Spleeter?
- What is the smallest reliable baseline verification set?
- At what point should audio/render verification become explicit?
- Does cloud Linux execution differ enough from the Windows workstation to justify formal machine-scoping rules?

> **Partly resolved 2026-09-02.**
> The full inherited suite passes on Windows and the verified command set is in `ENVIRONMENT.md`.
> The smallest useful baseline is `pytest tests/test_ffmpeg_adapter.py` plus `pytest tests/test_separator.py -k 2stems`, which avoids ~340 MB of checkpoint downloads.
>
> **Still open:** which inherited tests remain *meaningful* once Broken Spleeter features exist — the suite currently tests ordinary Spleeter, not deliberate failure.
> Audio/render verification is also still informal; there is no automated check that a render is non-silent or matches a reference.
> Linux has not been run since the fork, so machine-scoping remains unanswered.

### Git workflow

- Is direct local work on the default branch acceptable for this project's scale?
- When are temporary feature branches useful?
- Is a pull-request workflow useful for cloud-to-local handoff, or unnecessary ceremony?

These are workflow questions, not project-feature roadmap questions.

---

## 16. Likely Bootstrap End State

> **Reached 2026-09-02**, with two additions the list below did not anticipate: `ENVIRONMENT.md` as the live environment reference, and platform markers in `pyproject.toml` / `poetry.lock` making Windows a first-class target.

If the initial bootstrap succeeds, the repository should have:

- a clear Broken Spleeter identity
- unnecessary inherited release/community infrastructure removed
- preserved Spleeter runtime/test material
- `PROJECT_SPRINGBOARD.md`
- `WORKFLOW_SPRINGBOARD.md`
- concise byte-identical `AGENTS.md` / `CLAUDE.md`
- a minimal README
- recorded inherited provenance
- a known local Python/environment strategy
- a working `.venv`
- documented baseline commands
- at least one successful ordinary Spleeter run if practical
- enough repository knowledge to begin the first real technical springboard session

That state is more important than reproducing any particular directory layout or tooling convention.

---

## Final Note

The workflow should remain proportional to the project.

Broken Spleeter needs enough structure that multiple coding agents can share context, preserve decisions, and avoid damaging the inherited baseline accidentally.

It does not need to become a process project.

Start with the smallest workflow that makes the first few sessions reliable.

Add structure only when the project earns it.

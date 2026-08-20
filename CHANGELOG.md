# Changelog

All notable changes to the Doctrine System are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) ·
Versioning: [SemVer](https://semver.org/) (0.x — doctrine under active development).

## [Unreleased]

### Fixed — `--ci --ci-provider github` crashed whenever the source was itself an install

Every CI template now lives inside the corpus. `github` was sourced from
`.github/workflows/doctrine.yml` — the source repo's own **live** workflow,
outside `.Doctrine/` and therefore never installed into a consumer — while
`gitlab` and `azure` shipped templates under `.Doctrine/templates/ci/`.
Installing from Doctrine's own repo worked, so nothing caught it; a **chained**
install (target A installed from source, then B installed with A as
`--source`) crashed with `FileNotFoundError`, because A never received the
file github's entry pointed at. Reproduced, then fixed by adding
`.Doctrine/templates/ci/github-actions.yml` and sourcing from there. Two
copies of the same content is exactly the setup that let ADR-012's defect sit
unnoticed, so a parity test now asserts the template and the live workflow
have not drifted, and a second test performs a real chained install for every
provider.

### Fixed — two guard-hook tests failed in every consumer repo, permanently

`test_the_guard_hook_resolves_from_the_project_not_the_cwd` and
`test_the_guard_hook_still_decides_from_a_subdirectory` read both
`.claude/settings.json` and `plugin/hooks/hooks.json` unconditionally. The
installer ships `tests/` into every consumer but deliberately does not ship
`plugin/` (that is the Claude Code plugin's own packaging), so both tests died
with `FileNotFoundError` in any installed repo — reproduced in a real fresh
install. A `hook_configs()` helper now skips a config that isn't present, and
a new test asserts the **source** repo has both, so the tolerance cannot decay
into "no configs checked at all".

### Removed — the Bash arm of the `PreToolUse` guard (ADR-014), and a wrong diagnosis with it

`Bash` is out of the `PreToolUse` matcher in `.claude/settings.json` and
`plugin/hooks/hooks.json`. The guard no longer runs on shell commands at all:
no inspection, no Doctrine-sourced prompt, no per-command process spawn. The
shell path-analysis code is **deleted, not disabled** — 370 lines removed
against 48 added, across 22 symbols (`check_protected_in_command`,
`command_targets`, `command_is_read_only`, `command_has_write_redirect`,
`redirect_paths`, `strip_shell_noise`, `segment_verb`, `solobuilder_profile`
and the constants they served); the guard drops 1107 → 785 lines. Dead code
that looks like security is worse than an honest gap. Both earlier partial
holds go with it: the narrow "provably read-only verb" grant and the
`Delivery profile: solobuilder` blanket grant.

§7 and `05-packaging.md` have called that arm *"a tripwire, not a boundary"*
for several releases, after three independent security passes each found new
bypass spellings. Two findings closed the argument. **The cost side was
larger than recorded:** a live session reproduced the arm denying ordinary
read-only work — a diagnostic command refused with *"this command would
modify 'docs/releases/gold/v1.json'"* because the path sat in text the verb
classifier could not read. **And a load-bearing claim in the corpus was
simply wrong:** code comments and `FEATURES.md` asserted that registering a
`PreToolUse` hook removes a tool from the harness's own auto-approve path
("silence is not approval"). Checked against the runtime's documentation,
that is false — a hook exiting 0 with empty stdout is ignored and the normal
permission flow applies unchanged. The prompts blamed on hook registration
were in substantial part the guard genuinely objecting. Corrected wherever it
was asserted. The same check established the precedence that actually
matters: `permissions.deny`/`ask` outrank any hook decision, so a hook
`allow` can never grant more than the operator already allows themselves.

**Write/Edit is untouched in code** — secrets (§7 #2), protected paths,
control surface, test-weakening (§7 #4) all still decide, verified by
execution. **Its guarantee is now conditional, and a G5 audit found the
reason after the first draft of this entry claimed otherwise:** a shell
command is unchecked, and one thing a shell command can write is the guard's
own policy. `.doctrine-state/guard.json` holding a non-blanket `allow` (say
`tools/*`) is correctly not refused by `is_blanket()`, and `allow` exempts
those paths from the path *and* secret rules — so shell-write the policy
(`allow`, was `ask`) → Write the guard's source (`allow`) → Write an AWS key
(`allow`), with no prompt anywhere. Doctrine cannot close that from inside a
repo the agent can write to — **and the obvious mitigation is mostly theatre**,
which this entry states rather than banks: permission rules match per tool and
`Bash(...)` patterns match command *text*, not paths, so no rule means "any
command that writes this path". `Edit(...)` rules reach the file tools plus a
recognised subset of file commands (`cat`, `sed`, `head`, `tail`) — real but
partial — and say nothing about `echo x > path`. They were briefly shipped as
`permissions.ask` entries and removed the same day: an `ask` rule always
prompts (auto mode cannot clear it, no hook can override it), and since those
rules reach recognised Bash file commands, shipping them reintroduced the
Bash-level prompting this change existed to remove. Doctrine ships no
permission rules; add them to your own settings if you want that trade. The
only complete control is an isolation
tier, whose kernel-enforced `filesystem.denyWrite` **is unsupported on native
Windows**, so there the honest answer is WSL2 or a container, not a config
entry. Disclosed in ADR-014's Consequences, `05-packaging.md`, `FEATURES.md`
and the guard's docstring.
The command branch in
`evaluate()` is retained for a repo that deliberately re-adds `Bash` to its
matcher (secrets, §5, enforcement-config, test-weakening, then approve);
nothing analyses command paths any more on any profile. Stated plainly in
`.Doctrine.md` §7, `FEATURES.md` and the `05-packaging.md` strength table:
**Doctrine's hold on your shell is now prose, not mechanism** — the controls
that hold are your own `permissions.deny`/`ask` and an isolation tier
(`skills/sandboxing.md`).

### Added — `orchestration-ceremony` toggle: swarm/loop paperwork is togglable, the panel and safety rails are not

Multi-agent dispatch (`03-parallel-execution.md`) and disciplined looping
(`skills/loop-engineering.md`) are Doctrine's job, same as G3-G7 gating — but
neither was toggle-controlled the way the `PreToolUse` guard already is via
`autonomous-verification`. `off` drops work-package brief docs, loop-journal
lines, and formal `docs/reviews`/`docs/qa` filing — the panel's findings are
still obtained and acted on, just not written to a permanent file. It does
**not** touch the G4/G5 fresh-context verifier panel dispatch itself: a first
draft made that optional too (self-review allowed instead), corrected
same-day on direct instruction — dispatching a subagent is an autonomous tool
call, not something that costs friction to keep doing, so relaxing it bought
nothing and only reintroduced an author judging its own work. Self-review
still has exactly the two doors `02-role-protocol.md` has always named
(subagents unavailable; declared `Delivery profile: solobuilder`), both
still requiring disclosure. Also unchanged: `03-parallel-execution.md`'s
fan-out limits (width ≤ 4, no two packages on the same file) and
`skills/loop-engineering.md`'s execution caps (iteration budget, thrash
detector, token-jam rule) — those stop file corruption and unbounded token
burn, not paperwork. New default-on `FEATURES.md` row; both playbooks name
the boundary in their own text. See
`docs/adr/013-orchestration-ceremony-toggle.md` (records the correction
directly rather than silently rewriting it).

### Fixed — the CI templates carried a bug ADR-002 already fixed one layer down

`doctrine_verify.py` is scope-aware since ADR-002: it runs the full gate suite
(lint → ruff → tests → gold → state) only in Doctrine's own source repo, and
lint + gold + state only in a consumer repo, because ADR-002's own MAPLE
incident showed the unconditional form linting a host's code under Doctrine's
ruff config and hanging on the host's own test suite. That fix was never
carried into the three CI templates the installer ships under `--ci`
(`.github/workflows/doctrine.yml`, `.Doctrine/templates/ci/gitlab-ci.yml`,
`.Doctrine/templates/ci/azure-pipelines.yml`) — each had independently
re-implemented the same four raw steps, predating ADR-002, and still ran
`ruff check tools tests` / `unittest discover -s tests -v` unconditionally.
`doctrine.yml` installs byte-identical into a consumer repo, so any team that
opted into `--ci` inherited the exact defect ADR-002 already diagnosed and
fixed elsewhere. All three templates now call `python tools/doctrine_verify.py`
directly instead of shadowing its logic — one scope-aware entrypoint, not
three drifting copies. See `docs/adr/012-ci-templates-scope-aware-verify.md`.
Caught during a CI-reinforcement review, not from a live consumer report.

### Fixed — MAPLE positioning: Doctrine needs no agent runtime, and AGPL was never a gate

Three corrections from the framework owner, two of which the corpus had been
stating wrongly for several releases.

**1. Doctrine requires no runtime.** The corpus repeatedly called MAPLE "the
default workforce runtime **for every profile**" (`.Doctrine.md` §4),
"the default persistent workforce transport" (`03-parallel-execution.md`), and
"MAPLE by default — selected for every install" (`README.md`). Read plainly,
those say Doctrine depends on a runtime. It does not. The gates, roles,
artifacts, and state plane run on serial role-switching in a single session, or
on the host agent's native subagents; nothing in G0→G7 needs a broker, a
message bus, or a persistent fleet. The dependency direction has always been
ADR-003's `product → {doctrine, maple}` with `doctrine ⟂ maple`; the prose had
been implying a cycle the architecture never had.

**1b. MAPLE is one agent runtime among many, not a designated default.**
"Default" appeared in five files and read as a designation. Doctrine is
runtime-agnostic: it carries integration playbooks for runtimes the same way it
carries any other tool knowledge (`skills/tooling.md` — portfolio first,
adoption via `dependency-policy.md` and §5), and **scoped to
software-development use** — how work packages, gate verdicts, separation of
duties, and escalations map onto a runtime's primitives for building software.
MAPLE has the fullest document here for two ordinary reasons: it is
first-party, and it is what **OpenHawk** runs. Another runtime in the same slot
gets the same treatment and the same boundaries.

**2. AGPL is not a constraint.** `integrations/maple.md` carried a section
headed *"License verdict (dependency-policy §4: AGPL = explicit human
decision)"* — hedged, defensive, and a category error. AGPL-3.0 is a
free/open-source copyleft licence: **anyone may use, run, and build on MAPLE
freely, including commercially.** Reciprocity attaches to redistributing a
modified version or serving one over a network — not to use. And
`dependency-policy.md` §4 governs "GPL/AGPL **in a shipped library**";
Doctrine ships no such library, so the clause never applied and invoking it
manufactured a gate out of a non-issue. The section is now a short factual
note. The compatibility-manifest checkbox became conditional ("**if** this
product modifies and redistributes or network-serves `maple-oss`…"), with
ordinary use explicitly marked n/a.

The real reason `doctrineos` does not import `maple-oss` is unchanged and has
nothing to do with the licence: Doctrine stays stdlib-only so it installs into
any repo on any OS with zero dependencies, and so the gates keep working when
no broker exists.

**3. Pin moved 1.1.2 → 1.1.3**, and re-verified rather than merely bumped.
Against an ephemeral 1.1.3 install (scratchpad only; the host environment was
not modified), all real output: `register_handler("work.package")` normalizing
to `WORK.PACKAGE`; `MessageBroker.is_routable` present and `Agent.send`
accepting `require_routable`; `build_work_package` producing a typed
`WORK.PACKAGE`; `GATE_VERDICTS == {PASS, FAIL, BLOCKED, WAIVED}` with a bogus
`"LGTM"` verdict rejected; `tokens` present as a `ResourceRequest` field; and
`fresh_context_verifier_preset` **blocking a verifier→builder route** with
`SEPARATION_OF_DUTIES_VIOLATION`.

Touched: `.Doctrine.md` (§4 + routing row), `README.md`,
`.Doctrine/integrations/maple.md`, `03-parallel-execution.md`,
`05-packaging.md`, `skills/tooling.md`, `templates/compatibility-manifest.md`,
and both copies of `AGENTS.md` (root + `adapters/`, which are a synced pair).
ADR-009 is **not** superseded — its decision text ("Doctrine will not install,
vendor, or import MAPLE") was already correct; only the surrounding prose was
wrong.

### Added — `skills/sandboxing.md`: the tripwire finally names its boundary

`§7` and the `05-packaging.md` strength table have said for several releases
that the `PreToolUse` guard is *"a tripwire, not a boundary"* on Bash, and that
it should not be presented as containment. Both were honest. Both then **stopped
there** — naming the absence of a boundary without routing to the presence of
one. That silence was the defect, not the tripwire.

The containment answer was never a better parser. Shell is Turing-complete and
the path need not appear in the command at all —

```bash
p=$(echo L2dvbGQvcmVjb3Jk | base64 -d); rm "$p"   # names no path
```

— so text analysis is permanently incomplete, and four review rounds each
finding a new spelling was the evidence, not bad luck. A path mounted
**read-only** refuses that line and every spelling nobody has invented yet,
because the kernel never reads the command. The boundary is one layer down.

`skills/sandboxing.md` (63 → 64 playbooks) carries the doctrine for getting it:

- **A six-tier ladder** (none → least privilege → container → microVM/gVisor →
  separate host → ephemeral remote), each row stating what it stops and — the
  column that matters — what it **does not**. Pick the lowest tier whose
  "does not stop" you can genuinely accept. Tier 5 leaves the machine, so it
  is a §5 escalation before the data moves.
- **Five control dimensions named separately**, because most real "sandboxes"
  control one and are assumed to control all five: writable filesystem,
  network egress, credentials that cross in, lifetime, and what results carry
  back out.
- **A boundary proof** — runnable commands that must *fail* inside the sandbox
  (write to a protected path, curl an unlisted host, read a credential file,
  find the docker socket), with the output pasted. **A config file is a claim;
  a pasted `Read-only file system` is a boundary.** Re-prove after every config
  change: one added `-v` flag silently returns tier 2 to tier 0 while the docs
  still say tier 2.
- **Sandbox theater**, enumerated: root in the container, the mounted docker
  socket (a host root shell with extra steps), the rw host bind-mount,
  `--net=host`, and the jail holding the same credentials as the host.
- **Honest limits kept, not traded away.** Containers share a kernel and an
  escape is one kernel bug away. No tier protects what you deliberately mounted.
  And isolation is a blast-radius control, **not** a correctness control — "it
  ran sandboxed" never substitutes for review, tests, or evidence.

Wired in: a `§6` routing row; `§7` now routes from the tripwire to the boundary
in the same breath that admits the tripwire's limit; the `05-packaging.md`
strength table gains the isolation layer as a fourth row and a section on where
containment actually comes from; and `/sandbox` (byte-identical plugin twin)
sizes the tier and runs the proof.

**No new role card.** Evidence first: "sandbox" appeared nowhere in
`platform-engineering.md`, `security.md`, `platform-engineer.md`,
`devops-engineer.md`, or `05-packaging.md` — the gap was a *skill*, not a hat.
The three hats already exist, so the skill was added to their **Loads**:
platform-engineer builds the tier as a paved road, devops-engineer runs it,
security-reviewer holds the veto on a tier that is unproved or mismatched to
the blast radius. The dispatched subagent cards indirect through the role
card's Loads, so they picked it up with no `.claude/agents/` change; the count
stays at 14.

**No isolation-detecting hook.** Reliable container/VM detection across
platforms is real work with real false-negative risk, and a detector that is
wrong is worse than none — an agent that believes it is contained and is not is
worse off than one that knows it is on the host. The detection *procedure* is
in the skill as a verification recipe instead. Doctrine ships no sandbox and
provisions none: a container requirement would end its ability to install into
any repo on any OS with zero dependencies.

### Added — security operations: Doctrine carries the SOC playbooks

Doctrine had `skills/security.md` (build-time: secrets, input boundaries,
dependencies), `skills/ai-security.md` (reviewing an AI deployment), and
`skills/incident-response.md` (reliability incidents). It had nothing for
*running* security operations — the standing capability that assumes an
adversary is already inside and works a queue, a hunt, and an investigation.
Doctrine now carries those playbooks so an agent operating under it can
execute them; Doctrine itself does not run a SOC.

**5 skills** (58 → 63 playbooks):

- `skills/security-operations.md` — the SOC backbone: detect → triage →
  respond, the triage four questions, severity matrix, incident command,
  MTTD/MTTR/dwell time. States plainly how it differs from
  `skills/incident-response.md`: an adversary is *adaptive* and evidence is
  *perishable*, so containment is partly a timing decision and capture
  precedes mitigation.
- `skills/detection-engineering.md` — detection-as-code. The repo is the
  source of truth and the SIEM console is a deploy target; rule metadata
  (hypothesis / ATT&CK / data sources / known FP causes / response guidance /
  test evidence); tuning by **specificity, never blanket exclusion**; and
  three-colour coverage where **untested rules never count as green** —
  an all-green map built from untested rules is §7 #1 fabrication with a chart
  on it.
- `skills/threat-hunting.md` — hypothesis-first, time-boxed, and productive
  when it finds nothing *only if* it records what was searched. Stack-don't-scan
  at estate scale; every manual find becomes a detection or an explanation of
  why it cannot.
- `skills/digital-forensics.md` — order of volatility, chain of custody, never
  analyse the original, UTC normalisation, and observed-vs-inferred marked
  throughout. Cloud/container control-plane logs called out as the richest
  and fastest-expiring evidence.
- `skills/threat-intelligence.md` — the pyramid of pain, source scoring,
  indicator expiry, and attribution treated as a §5 decision with legal weight
  rather than a technical conclusion.

**3 roles** (39 → 42 cards):

- `roles/soc-analyst.md` — works the queue; every alert ends in a recorded
  disposition with a reason. Benign true positives are not false positives.
- `roles/detection-engineer.md` — owns detections as code through G3/G4/G5,
  and owns the honest red cells on the coverage map.
- `roles/incident-responder.md` — adversary-shaped incident command,
  explicitly distinguished from `roles/sre.md`'s reliability-shaped command;
  notification, law enforcement, disclosure, and extortion decisions are
  always the human's (§5).

**2 commands + 1 template:** `/soc-triage` and `/soc-hunt` (byte-identical
twins in `.claude/commands/` and `plugin/commands/`), and
`templates/security-incident-report.md` — a confidence table, an
observed-vs-inferred timeline, a chain-of-custody block, an enumerated
persistence checklist, and a §5 human-decision record.

**No new subagents and no new hooks.** The SOC roles work a live queue rather
than review a diff, so they need no fresh-context isolation; `.claude/agents/`
stays at 14. No SOC hook was added because none would do real work — the
action-level control at the tool boundary already exists as the `PreToolUse`
guard, and a hook that merely announced "security" would be theater.

Also corrected while touching them: stale corpus counts in `README.md`
(39 → 42 roles, 58 → 63 skills, 7 → 8 standards) and `.Doctrine/README.md`
(templates claimed 10; the filesystem had 14 before this change, 15 after).

### Fixed — round 5 (final, bounded): the anchor was weaker than it read

A single scoped security round audited only `doctrine_gold gate` and
`doctrine_verify`'s gold-gate wiring — days-old code that had never been
independently attacked. It maintained the veto: an ordinary forward commit (no
force-push, no amend) that forges a record and commits the forgery in one step
passed, because the gate compared the record against *itself*'s prior
committed state, which for a same-commit forgery does not exist to differ
from. Deletion detection also depended entirely on a committed manifest, so a
`git mv`/`git rm` followed by a commit removed the evidence from git's current
tree in the same step that should have been caught, and printed "nothing
promoted yet."

Fixed: deletion/relocation is now checked against git's **history** on the
gold directory (`git log`), not only its current tree, so a committed move or
removal is caught even with no manifest involved. `committed_bytes` and the
manifest comparison are EOL-normalized, so an honest Windows clone under
`core.autocrlf=true` (the Git for Windows installer default) is no longer
accused of forging its own security sign-off — that false accusation would
have gotten the gate disabled within a day of real use. Git being entirely
unreachable now fails the gate closed instead of reading as "nothing to
check." `doctrine_verify`'s decision to invoke the gate now reads git
**history** (`git log`) instead of the **index** (`git ls-files`), so a
`git rm` staged but not yet committed can no longer make the one-command
suite skip the gate while the gate itself, run directly, still fails. The
gate's own success message now states how many artifacts were actually
verified rather than claiming a full match after silently skipping one absent
from a fresh checkout.

**Corrected, not fixed — this round's residual is architectural, not a bug:**
a record forged and committed in the *same* commit is undetectable by any
HEAD-relative check, because there is no prior state to diff against.
`.Doctrine/05-packaging.md` states this precisely now and names the control
that actually catches it — a human reading `git log -p --
docs/releases/gold/` before a release-bound merge lands, backed by branch
protection. "CI running this gate on the pushed commit" is retracted as a
second anchor for that case: CI checks out the identical HEAD and reaches the
identical (wrong) answer. The two-line pre-commit hook this file recommended
earlier is retracted outright: the gate compares against HEAD, and a record
has no HEAD copy to compare against until *after* its own promoting commit
exists, so the hook refused the commit that files the very first record.

Evidence: ruff clean, 324 tests OK (1 skipped), full suite green. Five
independent rounds total; this is where the arc stops — the remaining gap is
now a documented, structural property of comparing against HEAD, not a
defect a sixth round would find and a seventh would need to fix again.

### Changed — the Bash guard is reclassified, and the real gate is elsewhere

Three independent security passes each found new shell spellings that reached
a protected file: round 1 redirects, round 2 non-redirect write primitives and
bare directories, round 3 wrapper verbs (`env rm -rf …`), newline segmentation
(a leading `ls` made a whole multi-line script "read-only"), nested shell
strings, `awk` program text, `sort --output=`, and process substitution. All
are fixed and carry regression tests — **and the pattern is the finding.**
Shell is Turing-complete; no static analysis of it is complete, so a guarantee
built on enumerating spellings will be wrong again.

- The **Write/Edit** rules stay a sound boundary: one field names one file.
- The **Bash** rule is now documented as a **tripwire, not a boundary** —
  excellent at catching the accident and the careless early, not a containment
  boundary against a determined adversary inside the repo.
- **`doctrine_gold gate`** is the guarantee that holds. It re-hashes every gold
  record, so tampering fails whether it came from a tool call, a redirect,
  `awk`, an editor, or an unreviewed script. `doctrine_verify` runs it whenever
  `docs/releases/gold/` exists; all three CI templates run it on every push;
  a two-line pre-commit hook keeps tampering out of history entirely.

### Fixed — round 3

- **Wrapper verbs no longer lend their verdict.** `env` and `time` were on the
  read-only list and *execute their arguments*: `env rm -rf <gold dir>` deleted
  every immutable record in silence. Wrappers are stepped through to the real
  verb; `bash -c`/`sh -c` payloads and interpreter program text are judged as
  writers.
- **`\n` is a command separator.** Its absence let a leading `ls` make an
  entire multi-line script inherit a read-only verdict — and multi-line Bash
  calls are the common case.
- **The control surface now covers the enforcement itself**: `tools/doctrine_*`,
  all of `.claude/` (including `settings.local.json`, which merges *over*
  settings.json, and `agents/*`, which carries the verifier tool grants
  ADR-010 names), `.mcp.json`, the ssh allowed-signers store and `*.pub`, plus
  the `git config` **verb** — which rewrites `core.hooksPath`, the signing
  trust store and aliases without ever naming the file it writes. A verifier
  had deleted `doctrine_guard.py` itself with no decision emitted.
- **Blanket policy entries are refused by behaviour, not by spelling.** The old
  four-string list missed `?*`, `*.*`, `**/**` and `[a-z.]*`, each a total
  off-switch. Entries are now tested against canary paths.
- **Every hook in both wirings resolves and runs from the project root.** Only
  `PreToolUse` had been repaired; the rest still used bare relative paths, so
  for any user whose cwd was not the project root, hydration and the engagement
  block silently never ran.
- **The test that was supposed to catch that was test theater** — it asserted
  `returncode == 0`, the one condition a silently-off hook also satisfies, in a
  test whose own docstring named that failure mode. It now asserts each hook
  produced output.

### Fixed — independent verification of v0.7.0 overturned its own sign-off

Three fresh-context verifiers were dispatched on `v0.6.46..HEAD`. The author's
self-review had **approved** the release; the independent pass returned
REQUEST-CHANGES, a security **VETO** on five findings each proven with an
executed payload, and a QA **FAIL**. Every finding below was reachable in one
or two tool calls. All are fixed, each with a regression test that reproduces
the verifier's own payload.

- **The guard could be switched off by the party it governs.** Neither
  `.doctrine-state/guard.json` nor `pyproject.toml` was protected, and `allow`
  accepted `"**"`. Two tool calls disabled all four rules; one more flipped
  consumer-corpus protection off. The enforcement surface (policy, hook
  wiring, `CLAUDE.md`, `AGENTS.md`, `.github/workflows/`, the fleet target
  list) now requires an explicit human **ask**, and blanket patterns are
  dropped even from a well-formed policy file.
- **The command path rule matched raw substrings**, which failed in both
  directions at once: `python -c "open(p,'w')"`, `touch`, `install`,
  `git checkout --`, `perl -pi`, backslash paths, quote elision and trailing
  comments all walked past it, while `.git` matched `.gitignore`/`.github`
  and `.env` matched `os.environ` — verifiers measured **11 of 13 ordinary
  commands denied**. Commands are now tokenized, path candidates resolved
  against the repo root, and matched by the same matcher the Write rule uses.
- **The guard failed open on a `RecursionError`.** A payload nested 3000 deep
  escaped `except ValueError`; the gate exited 1 with no decision, which the
  hook contract reads as *proceed*. One decoy field carried a denied secret
  write straight through. Parse failures of every kind now deny, payload size
  is bounded, and wrong-typed `tool_name`/`tool_input` deny instead of being
  coerced to an empty dict.
- **The hook resolved its own script relatively**, so from a subdirectory
  python exited 2 — the code reserved for *block* — and the gate became a
  total lockout that prevented its own repair. It did exactly that to the
  session that built it. Both wirings now resolve from `CLAUDE_PROJECT_DIR`,
  with a relative fallback, and a test executes each hook command from a
  subdirectory.
- **`gold check --require-signature` passed a substituted signer.** Deleting
  the tag and re-cutting it at the same commit with a different key returned
  exit 0 and printed GOLD, while the record still credited the first signer;
  only the `signed` boolean was compared. Identity is now compared, a record
  with no attestation cannot satisfy `--require-signature`, and the console
  prints the record's own claim rather than whatever the tag verifies as now.
- **`doctrine_fleet` was neither read-only nor safe.** `git status` rewrote
  the index whenever the stat cache was stale (any fresh clone), and git
  honoured `core.fsmonitor` **from the repo being inspected** — a "read-only"
  scan executing code chosen by untrusted repos. Now `--no-optional-locks`
  with `core.fsmonitor`/`core.hooksPath` neutralized. It also no longer
  crashes on an unreadable directory or a non-cp1252 repo name.
- **The bridge leaked its repository snapshot to a rebound `Host`** (browsers
  omit `Origin` on same-origin GET, so the origin check waved it through);
  `Host` is now validated against loopback names. The oversized-request branch
  lost its 413 the same way the 415 path used to — a bounded lingering discard
  fixes it up to 1 MiB, beyond which the abort is deliberate and documented.
- **Rule coverage gaps closed**: force-push via `+refspec`, `update-ref -d`,
  `uv/poetry publish`, `Remove-Item -Recurse`, `rm -rf ..`, download-then-run;
  and for §7 #4, `pytestmark`, `skipTest`, `raise SkipTest`, plus deleting or
  `sed -i`-ing a test file through the shell.
- Guard path handling: Windows extended-length (`\\?\`) prefixes no longer
  skip every rule, matching is case-insensitive (macOS treats `.ENV` and
  `.env` as one file), nested `services/*/.env` is protected by both tools,
  and a write *into* a governed repo is judged even when the session started
  in a parent directory.

### Changed

- `attestation` now records which backend signed (`ssh` / `openpgp` /
  `x509`), read from the signature's own armor header rather than local
  config. **Compatibility:** the field is optional, so records written by
  0.7.0 stay valid — but a repo whose corpus is still at 0.7.0 will reject a
  record produced by a newer tool, because the 0.7.0 schema sets
  `additionalProperties: false`. Update the corpus before promoting across a
  version-skewed fleet; `doctrine_fleet status` is how you find the skew.
- Verifier roles are **dispatched, not worn**: `.Doctrine.md` §2,
  `02-role-protocol.md`, `/review`, `/qa` and the per-turn engage reminder now
  require fresh-context subagents at G4/G5, and an in-session fallback must
  open its artifact with that disclosure.
- ADR-010, the brief, `README.md` and `05-packaging.md` corrected: they
  described a verifier-write-isolation rule that was never implemented and
  could not be from a payload that carries no role. What actually isolates a
  verifier is its subagent tool grant — which still includes `Bash`, so the
  gap is now stated rather than claimed shut.

## [0.7.0] - 2026-08-03

> Release **prepared**, not cut: the version carriers are bumped and the gates
> are green, but the annotated tag and any publication remain the human's
> call (§5). Everything below is on disk and tested.

### Added

- **`tools/doctrine_guard.py` — mechanical enforcement at the tool boundary.**
  The L3 `PreToolUse` gate ADR-004 left on the roadmap. Until now every
  Non-Negotiable was prose the agent chose to obey; the guard *denies* at the
  point of action: secret-shaped content (#2), writes to immutable evidence
  (gold records, the state checkpoint, the installed corpus in a consumer
  repo), and *escalates* §5 actions (force-push, history rewrite, publish,
  `terraform destroy`, `curl | sh`) and test-weakening edits (#4) to the human.
  Outside a Doctrine repo it is silent; inside one, an unparseable request is
  denied — a governed repo must not gain a bypass by malforming a request.
  Local policy at `.doctrine-state/guard.json` (`protected_paths`, `allow`).
- **Gold-build attestation.** `doctrine_gold record` now reads git's own
  verification of the annotated tag and stores `{signed, signer, key}` in the
  record; `--require-signature` (on `record` and `check`) refuses a promotion
  whose authorship is unproven. The hash chain proved *what* was promoted;
  a signed tag proves *who*. No new dependency, no key custody, no network —
  it reads keys the org already manages. Records written before 0.7.0 stay
  valid (`attestation` is optional; records are immutable).
- **`tools/doctrine_fleet.py` — the cross-repo view.** `status` reports
  doctrine version, drift from a source tree (`current` / `behind vX` /
  `ahead` / `modified` / `incomplete`), state-plane posture, worktree
  cleanliness, release distance, and gold-record count for N repos, as a table
  or `--json`. Strictly read-only (a test hashes the whole tree before and
  after); exits 1 on drift so a scheduled job can watch a portfolio.
- **CI parity beyond GitHub.** `.Doctrine/templates/ci/gitlab-ci.yml` and
  `.Doctrine/templates/ci/azure-pipelines.yml` run the same gate sequence as
  the Actions workflow; `doctrine_install --ci --ci-provider github|gitlab|azure`
  lands each at its provider's canonical path.

### Fixed

- **The bridge suite's intermittent failure** (~1 full-suite run in 6 under
  load). Early-rejection paths in the control-room bridge answered and closed
  while the request body was still in flight; the late body landed on a closed
  socket, the OS replied RST, and the client lost the response it had not read
  (`ConnectionAbortedError` / WinError 10053). The body is now drained at the
  single `_send_json` choke point — the oversized branch deliberately opts out
  — and every connection read is bounded by `REQUEST_TIMEOUT_SECONDS`, closing
  a slowloris hold-open at the same time. A deterministic reproduction
  (headers, pause, late body) ships as a regression test: it fails 10/10
  against the pre-fix module and passes 10/10 after.
- **`.env.example` is no longer treated as a secrets file** by the guard's
  protected-path rule — the repo-devops skill *requires* it. The secret rules
  still apply to it: names yes, values no.

- **Reinstall preservation hardening** — force updates now explicitly preserve
  repository-owned Doctrine state, memory/session roots, and planning artifacts.
  Existing profile markers embedded in richer Markdown brief lines are detected,
  preventing duplicate append blocks. Regression coverage force-reinstalls over
  seeded state, session, memory, brief, plan, and ADR data and requires
  byte-for-byte identity.

- **Personal/solo delivery profile + universal MAPLE selection** — installer
  flags `--personal` and `--solo` now select one canonical
  `Delivery profile: personal`, routing ordinary work through the new Solo
  Builder role and a DevOps evidence gate without mandatory organizational,
  governance, privacy, compliance, or legal ceremony. Real risk surfaces still
  activate their matching controls, and the permanent safety/§5 floor is
  unchanged. Personal installs default to `Agent latitude: creative`: agents
  may explore reversible local solutions freely before deterministic
  tests/evidence, while governance fences only the effect that activated it.
  Existing explicit latitude is preserved; the marker is a portable work
  policy, not a provider temperature claim. Every install now records
  `Workforce runtime: maple`; legacy
  `--maple` remains an idempotent compatibility flag, no MAPLE package is
  installed or linked, and unavailable runtimes degrade to native/serial
  execution. Personal and enterprise profiles fail closed as mutually
  exclusive; startup remains composable.

- **Consumer dashboard contract packaging fix** — the repository installer now
  copies `docs/contracts/doctrine-control-room.openapi.json` with the dashboard
  tool and its tests. Consumer installs can run the advertised optional
  `test_doctrine_*.py` suite without the source-only contract test failing on a
  missing file; a packaging regression test verifies byte-for-byte delivery.

- **Control Room Windows production loading repair** - the repository-owned
  production launcher now normalizes vinext's Windows static-cache keys so
  rendered CSS and JavaScript assets no longer return `404`. The layout uses
  network-free native font stacks instead of emitting host filesystem font
  URLs, and an HTTP regression starts the built server and verifies every
  rendered asset and content type.

- **Doctrine Control Room + local runtime bridge** — adds an isolated
  `dashboard/` React module and the stdlib-only `doctrine-dashboard` bridge. The
  UI now reads real project/Git identity, activation wiring, state-chain status,
  governance-artifact counts, recent commits, package/tag distance, and
  verification results. **Run verification** creates one bounded asynchronous
  job and reports all four Doctrine gates plus the observed test count.
  Loading, partial, unavailable, empty, and live states now arise from the
  contract instead of a state picker; prototype metrics and fake action buttons
  are removed. The bridge binds to loopback, exact-allows local origins,
  rejects dirty-tree/non-JSON/oversized/concurrent mutations, runs no shell,
  bounds verifier time/output, invalidates mid-run repository changes, and
  fails closed on contradictory gate output. The pinned dashboard toolchain was
  refreshed after a new advisory sweep and now audits with zero known
  vulnerabilities. A source-only CI workflow now repeats lockfile install,
  lint, TypeScript, build/tests, and audit on Ubuntu and Windows without
  changing Doctrine's consumer workflow. Local only — no external publication,
  remote auth, portfolio aggregation, or MAPLE/Shield/Trust connector is
  claimed.

- **Repository-audit remediation** — source/consumer detection now parses
  `[project].name` with stdlib `tomllib`; source verification fails closed when
  its required Ruff gate is unavailable; the source checkout carries the
  universal `AGENTS.md` boot and treats it as activation-critical; CI covers
  Python 3.11 and 3.12 with Ruff pinned; and the MCP protocol test closes all
  subprocess pipes.
- **Dogfood: opt-in wiki publishing for this repo** — `.github/workflows/wiki.yml`
  + `scripts/build_wiki.py` apply `skills/web-publishing.md` to the Doctrine repo
  itself. On push to `main` — once the human sets repo variable
  `DOCTRINE_WIKI_PUBLISH=on` (the recorded §5 external-publish opt-in) — the wiki is
  one-way-synced from the designated source (`.Doctrine/` roles + skills = 78 pages
  + Home + `_Sidebar`) through a fail-closed gate (credential-pattern scan,
  broken-link + empty-page checks). Repo tooling only — **not** a framework/version
  change (no `.Doctrine/` corpus or manifest change).
- **Dogfood: opt-in GitHub Pages for this repo** — `.github/workflows/pages.yml` +
  `scripts/build_site.py` render the designated source (`.Doctrine/` playbooks +
  roles + skills + README = 86 pages) to a **self-contained** static site (embedded
  CSS, no CDN, works offline) via Python-Markdown, through the same fail-closed gate
  (credential-pattern scan, thin/empty-page check), deploying via
  `actions/deploy-pages`. Dormant until `DOCTRINE_PAGES_PUBLISH=on` **and**
  Settings→Pages→Source=GitHub Actions (the recorded §5 opt-in). Repo tooling only.

## [0.6.46] - 2026-07-23

### Added
- **`--local` install + a managed `.gitignore` block — Doctrine is now
  trivially easy to keep out of (or move off) a repo.** The framework footprint
  is scattered by design (root dot-files, `tools/`, `tests/`, `.claude/`, and
  per-tool adapter files at *variable* paths like `.cursor/rules/`, `GEMINI.md`,
  `.github/copilot-instructions.md`), which made "gitignore all of Doctrine" a
  manual, error-prone chore. The installer now writes a single marker-delimited
  managed block:

  ```
  # >>> doctrine (managed by doctrine_install; delete this block to un-ignore) >>>
  ...
  # <<< doctrine <<<
  ```

  - **`--local`** fills that block with the WHOLE installed framework, computed
    for the selected `--tool`s so the variable adapter paths are covered
    automatically. Default (no flag) keeps today's behavior — only
    machine-local state is ignored, the corpus stays committable — so this is
    fully backward-compatible.
  - **`docs/` gate artifacts (briefs, ADRs, reviews) are never ignored** — they
    are the repo's own work product, authored via Doctrine but about the repo
    (the lesson from ignoring a real repository-review by accident). `Makefile`
    is offered commented (generic name the repo may own), not silently hidden.
  - The block writer replaces (never duplicates) its block and preserves all
    content outside the markers byte-exactly, CRLF included (raw bytes, no
    universal-newline translation — the recurring Windows lesson).
  - New `tests/test_doctrine_install_gitignore.py` (13 cases: block contents,
    variable adapter paths, docs-never-ignored, replace-not-duplicate,
    CRLF/outside-content preservation, idempotence, `--local` integration).
  - Docs: `QUICKSTART.md` + `.Doctrine/05-packaging.md` document `--local`.

## [0.6.45] - 2026-07-23

### Changed
- **Portfolio-private references scrubbed from the corpus — Doctrine is
  publish-clean.** The distributable framework named several first-party,
  unpublished products by name; a public Doctrine (installed into other repos,
  or the repo itself) would have leaked them. This release genericizes every such
  reference to the *mechanism* it serves, so the method stays intact and the
  product names live only in a private, gitignored plan.
  - **Removed** the three proposed internal-integration shims
    (`integrations/stix.md`, `openguide.md`, `contegrity.md`) and their §6 routing
    rows. Runtime **action** / **behavior** / **provenance** enforcement is now
    documented as *bring-your-own extension points* (pick a fit, vet via
    `dependency-policy`, wire as a new `integrations/*.md` shim) — the same
    architecture without the product names.
  - **Genericized** inline mentions across `skills/tooling.md` (portfolio catalog →
    wired-integrations + extension points), `skills/ai-security.md`,
    `domains/agentic-ai.md`, `domains/auditing.md`, `integrations/README.md`,
    `integrations/fde.md`, `integrations/graphify.md`, `roles/fde.md`, the
    state-plane docs, several ADRs/briefs/retros, and tool comments.
  - **Public integrations kept:** CodeMonk, MAPLE, floci, ponytail, graphify (all
    have live upstreams / wired shims). Competitor references (public) left as-is.
  - Verification: corpus grep-clean for the internal product/pack names; lint +
    signatures + tests green. No mechanism removed — only names.

## [0.6.44] - 2026-07-23

### Added
- **AI deployment-pattern security-review archetypes (Security Review Process
  Standardization, pillar 1).** A shared control backbone + five archetype packs:
  - **`skills/ai-security.md`** (57 -> 58 skills) — the shared AI-security-review
    discipline: OWASP LLM Top 10 · MITRE ATLAS · NIST AI RMF · ISO/IEC 42001 · EU AI
    Act; the threat taxonomy (prompt injection incl. indirect, insecure output
    handling, excessive agency, supply-chain, model DoS/theft, overreliance) and the
    deterministic G1+G5 review method. Loaded by `security-reviewer` + `ml-engineer`.
  - **`domains/agentic-ai.md`** — excessive agency, tool least-privilege, HITL/action
    gating (maps to §5 + a wired action-enforcement layer), memory poisoning, cost/loop bounds (budget gate + loop caps).
  - **`domains/conversational-ai.md`** — prompt injection/jailbreak, system-prompt
    leak, transcript PII, moderation, transparency, overreliance.
  - **`domains/iot-ai.md`** — device attestation, signed edge-model + OTA, adversarial
    sensor inputs, on-device extraction (composes manufacturing/transportation).
  - **`domains/contact-center-ai.md`** — voice consent/PII, deepfake-voice, PCI-in-voice
    (DTMF mask), agent-assist human override (composes finance/healthcare).
  - **`domains/saas-ai.md`** — tenant isolation (no cross-tenant RAG/embedding leakage),
    no-train-on-customer-data, subprocessor/DPA, RBAC, per-tenant limits.
  - **Zero new roles** — all five overlay `skills/ai-security.md` and reuse
    security-reviewer/compliance/risk/ml-engineer. 15 domain packs total (10 industry
    verticals + 5 AI archetypes).
- `.Doctrine.md` §6 routing row for AI-deployment security review; `domains/README`
  gains the archetype category; counts -> 58 skills.

## [0.6.43] - 2026-07-22

### Changed
- **`argument-hint` frontmatter on all five slash commands** (`/doctrine`, `/role`,
  `/review`, `/qa`, `/checkpoint`) — self-documenting arg placeholders so the
  autocomplete shows what to type. Both `.claude/commands/` + `plugin/commands/`
  (byte-parity). Note: the *root* cause of "selecting `/doctrine` auto-sends an empty
  task" is the keystroke — **Enter** both selects *and* submits; **Tab** accepts the
  suggestion WITHOUT submitting (then type the task, then Enter). The hint improves
  discoverability; Tab-to-select is the definitive fix.

## [0.6.42] - 2026-07-22

### Added
- **Local-first MCP: the installer now auto-registers `doctrineos`.** A `.mcp.json`
  is written into every install (never overwriting an existing one), registering the
  `doctrineos` server (`python tools/doctrine_mcp.py`) so any `.mcp.json`-aware agent
  (Claude Code, Cursor, …) offers the doctrine tools — corpus lint, state plane,
  gold-build gates — on approval. **No marketplace, no publish** required; the
  `/plugin` path was never the only way. The source repo now self-registers via a
  root `.mcp.json` too (dogfooding).
- README quick-start clarified: the plugin path needs the marketplace (public); the
  installer is the local/private path and now wires the MCP; `claude mcp add
  doctrineos -- python tools/doctrine_mcp.py` documented for manual Claude Code use.
- Tests: `.mcp.json` in the install round-trip + registers-doctrineos +
  never-overwrites-existing.

### Verified (local, this machine)
- Live stdio probe of `tools/doctrine_mcp.py`: `initialize` → `serverInfo doctrineos`,
  `tools/list` → 7 tools, `state_status` call → real checkpoint data (`isError:false`).
- Local install (`--tool all`) into a throwaway target: 230 files, consumer
  lint-clean, and (post-fix) `.mcp.json` present.

## [0.6.41] - 2026-07-22

### Added
- **`/review` and `/qa` role-shortcut commands** — high-frequency gate roles on top
  of the parametric `/role`: `/review` adopts the Code Reviewer at G4 (fresh-context,
  severity-ranked, runs the AI-slop pass); `/qa` adopts the QA Engineer at G5
  (adversarial, execute-don't-inspect, five UI states). Both ship in `.claude/commands/`
  + `plugin/commands/` (byte-parity, auto-enforced by the generalized check).
- **`skills/ai-slop.md` now also loaded by `roles/ux-designer.md`** — design slop
  (UI variant) is covered by ux + web-designer + code-reviewer. Signatures updated.

## [0.6.40] - 2026-07-22

### Added
- **`skills/ai-slop.md` — the AI-slop detection reviewer discipline** (56 -> 57
  skills; gstack's "designer who catches AI slop", generalized). A fresh-context
  G4/G5 detector for the failure modes specific to AI-generated code/content:
  invented APIs, plausible-but-wrong, over-engineering, placeholder-as-done, comment
  slop, test theater, fabricated evidence, ignores-the-codebase, security theater,
  confident-wrong prose. Composes with Non-Negotiables #1/#9 and `ponytail` (they
  forbid the acts; this detects them). Loaded by `roles/code-reviewer.md` and, for
  design slop, `roles/web-designer.md`; routed in §6.
- **Browser E2E at G5 (Playwright)** — `roles/qa-engineer.md` + `skills/testing.md`
  now require a **real-browser** end-to-end check for user-facing surfaces at G5,
  exercising the **five UI states** (empty/loading/error/partial/ideal). Playwright
  is the vetted external anchor (native or the Playwright MCP server) — *recommended,
  not bundled*: Doctrine stays vendor-neutral (`skills/tooling.md` portfolio-first).

## [0.6.39] - 2026-07-22

### Added
- **`/role` slash command — role ergonomics** (idea harvested from gstack, built
  doctrine-native). `/role <name> [task]` adopts a specific hat: reads the role card
  + its Loads, announces `[ROLE: …]`, runs that role's checklist, and keeps
  reviewer roles fresh-context. Ships in `.claude/commands/` **and** `plugin/commands/`
  (byte-parity), beside `/doctrine` and `/checkpoint`.
- **Frictionless onboarding** — the README quick-start now shows the drive-it path
  (`/doctrine`, `/role`, `/checkpoint`) so a new user engages in one line.

### Changed
- `doctrine_lint` `check_plugin_parity` **generalized**: every `.claude/commands/*.md`
  now auto-requires a byte-identical `plugin/commands/` twin (one-directional — the
  plugin may still ship consumer-only commands like `doctrine-init`). New commands
  are covered automatically; also fixes a hard-coded checkpoint-only drift message.

## [0.6.38] - 2026-07-21

### Changed
- **`skills/loop-engineering.md` — right-sized upgrade.** Adopts the expanded
  draft's substance while keeping the skill lean (progressive disclosure): adds
  **loop profiles — Ratchet (budget 2-3) / Shutter (budget 1) / Farm (orchestrator
  fan-out)** and the **token-jam stop rule**, with Farm-Loop cross-referencing
  `03-parallel-execution.md`. The five-beat anatomy, caps, DCCV spine, journal, and
  failure modes are retained/tightened.
- **`skills/metrics.md` — owns the token numbers.** The deep per-loop token
  accounting (**TPI / TTG / TPD / ETS**, per-profile expectations, farm rollup CPM +
  orchestrator-overhead) moved here from the loop skill — measurement lives with the
  measurement discipline; loop-engineering keeps the *behavior*. All from harness
  usage fields, never self-estimated; computed by CodeMonk. Ties into the v0.6.35
  budget gate.

## [0.6.37] - 2026-07-21

### Added
- **`skills/tooling.md` — the tool/project selection discipline (55 -> 56 skills).**
  Answers "what's the best tool for this role/skill/gate/plugin/MCP/subagent" as a
  *procedure*, not a rotting matrix: **portfolio-first**, then vetted external
  (`standards/dependency-policy.md`), MCP via `skills/mcp-tooling.md`, adoption/
  provisioning = §5. Carries the grounded **portfolio catalog** mapping our own
  integrations to the Doctrine mechanism each serves, with honest status
  (the wired integrations CodeMonk/MAPLE/floci/ponytail/graphify, plus bring-your-own
  extension points for action/behavior/provenance/retrieval), plus a best-fit-by-mechanism table. Anti-staleness by
  design: encodes the rule + the stable portfolio map, defers volatile external
  specifics to the routed discipline skill + a currency check.
- `.Doctrine.md` §6 routing row for tool selection; counts updated to 56 skills.

## [0.6.36] - 2026-07-20

### Added
- **Runtime enforcement extension points (proposed).** §6 routing rows + notes for
  three thin, opt-in, non-vendored planes, each orthogonal to the process gates:
  - runtime **action** enforcement — makes §5 ("escalate before irreversible/external
    actions") physical: an action-enforcement layer ALLOW/DENY/QUARANTINE gates the
    concrete action with a crypto proof + HITL. Doctrine decides, the layer enforces,
    the human is root.
  - runtime **behavior** enforcement — role personas + `engagement-engineering` +
    `ponytail` compile to behavioral contracts held by a behavior-control runtime;
    sits beside ponytail in Behavior Engineering.
  - **integrity/provenance** — a provenance layer captures agent comms as
    tamper-evident evidence beneath the state plane, gold-build, and
    `domains/auditing.md`.
  - Three orthogonal planes: process (Doctrine gates) · behavior · action · with
    provenance as the evidence record beneath all.

### Notes
- **Honesty:** these are **proposed** shims — the *fit, routing, and boundary* are
  grounded, but each frontmatter marks `upstream` / `license` / `pinned_version` /
  API as `<confirm>` because they are not yet verified against a running product.
  No fabricated pins. The human confirms the real interfaces before they wire live
  (unlike codemonk/maple, which are verified).

## [0.6.35] - 2026-07-20

### Added
- **`doctrine_metrics budget` — a real budget gate (measurement -> enforcement).**
  CodeMonk *trends* token spend but by design never gates work; this adds a live
  ceiling: `budget --cap <tokens>` (or `--spent <n>` from `codemonk tokens`, or a
  summed `--log`) compares spend to the cap and, on breach, exits non-zero with a
  **Section 5 escalation** (the human decides to continue — never a silent block,
  consistent with the codemonk boundary). No telemetry yet exits 0 with a
  launch-wrapped hint (not a breach). Defensive JSONL token sum tolerates unknown
  lines. 7 tests (under/warn/over/no-telemetry/parse/cap-guard).

### Changed
- `integrations/codemonk.md`: **wrapped launch (`codemonk wrap --otel -- claude`)
  is now the documented standard** for token capture, with the honest caveat that
  capture cannot be enabled retroactively — a session started bare has no token
  data (which is why the recent history is blank). Documents the budget gate.

### Notes
- Honest state of token monitoring: the metric *design* is comprehensive (TCR,
  cost-per-landed-change, ROI), but capture is a session-launch choice and has been
  off — `codemonk_tokens.jsonl` is absent and `docs/metrics/` is stale at 7/13.
  Turning it on requires launching wrapped; this release makes that the standard and
  adds the enforcement gate that was missing.

## [0.6.34] - 2026-07-20

### Added
- **Four domain packs close the initial vertical set (ten domains total):**
  - **`domains/ecommerce.md`** — PCI · consumer-protection · tax nexus · WCAG;
    idempotent checkout, inventory-reservation (no oversell), server-authoritative
    pricing, no dark patterns.
  - **`domains/travel.md`** — IATA/GDS/NDC · PCI · passport (special-category) PII ·
    ATOL; live-availability booking idempotency, fare-rule correctness, APIS handling.
  - **`domains/transportation.md`** — FMCSA HOS/ELD · ISO 26262 (ASIL) · telematics
    privacy · GTFS; tamper-evident duty logs, functional-safety fallback, no silent
    surveillance. Composes `domains/aerospace.md` rigor for ASIL-D autonomy.
  - **`domains/auditing.md`** — SOC 2 · GAAS/SOX · evidence integrity · independence;
    immutable/tamper-evident evidence, chain-of-custody, separation-of-duties (the
    doctrine's own fresh-context-verifier rule as a legal requirement), reproducible
    findings. (Evidence-integrity substrate maps onto a wired provenance layer.)
  - **All four add 0 new roles.**

### Changed
- `domains/README.md` ledger: **ten domains, three new roles total** (healthcare +2,
  quant +1; the other eight reuse the core) — the overlay thesis proven at scale.

## [0.6.33] - 2026-07-20

### Added
- **`domains/manufacturing.md`** — Manufacturing pack: ISO 9001 / IATF 16949 /
  ISO 13485 · IEC 62443 (OT/ICS security) · IEC 61508/61511 (functional safety, SIL)
  · ISA-95 MES model; OPC-UA/MTConnect/MQTT entities. Non-negotiables: app software
  is never the sole guard against physical harm (independent SIL safety system),
  OT/IT segmentation (Purdue), no untested change to a live line, unbroken lot
  genealogy. **0 new roles** (security-reviewer=OT/62443, risk-officer=functional
  safety, qa-engineer=quality/traceability).
- **`domains/logistics.md`** — Logistics/Supply-Chain pack: customs/export control ·
  OFAC sanctions · C-TPAT · DSCSA serialization · GDP/FSMA cold-chain · dangerous
  goods; GS1 (GTIN/SSCC/GLN) + EPCIS + EDI (X12/EDIFACT) entities. Non-negotiables:
  hold-not-release for controlled/sanctioned shipments (§5), substantiated customs
  data, unbroken chain-of-custody, no silent cold-chain excursion. **0 new roles**
  (compliance-officer=customs/sanctions, regulatory-affairs=export/DSCSA).

### Changed
- `domains/README.md` packs index: **six domains, three new roles total** — the
  overlay cost ledger now reads healthcare +2, finance 0, quant +1, aerospace 0,
  manufacturing 0, logistics 0.

## [0.6.32] - 2026-07-20

### Added
- **`domains/quant.md`** — Quant/Trading pack: MiFID II · MAR (market abuse) ·
  model-risk (SR 11-7) · SEC 15c3-5 market access; FIX/ITCH entities, point-in-time
  market data, versioned models. Non-negotiables: no look-ahead/out-of-sample-only
  backtests, pre-trade risk controls + tested kill switch before any live order,
  no market-abuse order patterns, governed model risk, reproducible research.
- **`domains/aerospace.md`** — Aerospace/Space pack: DO-178C (DAL A–E) · DO-254 ·
  ECSS · NASA-STD-8739 · **ITAR/EAR export control**; CCSDS/MIL-STD-1553/ARINC 653
  entities, bidirectional requirements traceability. Non-negotiables: MC/DC +
  traceability for DAL-A/B, defined safe modes, bounded WCET / no post-init dynamic
  allocation in flight-critical paths, ITAR data segregation (§5), config management.
- **`roles/quant-researcher.md`** (38th role, `⁽ᵈ⁾` domain specialist) — owns signal/
  model research and the **backtest-integrity sign-off** (no look-ahead, out-of-sample,
  reproducible); distinct from the ML Engineer. Aerospace adds **zero** roles (reuses
  qa-engineer for DO-178C verification, risk-officer for the safety case, compliance/
  regulatory-affairs for ITAR + certification).

### Changed
- `domains/README.md` packs index now carries a **roles-added column** as the honesty
  ledger of overlay cost (healthcare +2, finance 0, quant +1, aerospace 0).
- Counts updated to 38 roles / three domain specialists (`.Doctrine.md` index +
  legend, both READMEs, plugin); also corrected a stale "35 roles" bullet in the root
  README (unbumped since v0.6.30 — the badge had moved but the prose had not).

## [0.6.31] - 2026-07-20

### Added
- **`domains/finance.md`** — the Finance/Fintech domain pack, second overlay off
  the v0.6.30 template. Regimes: PCI-DSS · AML/KYC · SOX · PSD2 · Basel III ·
  MiFID II. Canonical entities: ISO 20022 / ISO 8583 / FIX, double-entry
  `LedgerEntry`, money as integer minor units. Non-negotiables: idempotent
  money movement, unbreakable double-entry, no PAN outside PCI scope, no skipped
  AML/KYC, mandatory reconciliation.
- **Demonstrates the overlay payoff: zero new roles.** Finance composes onto the
  existing governance core (security-reviewer for PCI, compliance-officer for
  AML/KYC, risk-officer for model/market risk, regulatory-affairs for licensing).
  A vertical is a pack, not a new headcount — most domains add no roles.

## [0.6.30] - 2026-07-20

### Added
- **Domain-overlay layer (`domains/`)** — verticals (healthcare, finance, aerospace,
  logistics…) are covered by thin **overlay packs** that compose WITH the horizontal
  engineering core, not by parallel role-sets. Coverage is `role × domain`: one
  `backend-engineer` loads `domains/<x>.md` when the work serves that domain, gaining
  its regulatory regime, canonical entities, domain acceptance criteria, harm model,
  and a G5 domain sign-off. Keeps the always-loaded core lean (progressive disclosure)
  while scaling to any number of verticals. Rationale: parallel per-domain companies
  would be an N×M file explosion with ~90% duplicated engineering content and
  regulations that go stale.
- **`templates/domain-pack.md`** — the fixed eight-section shape every pack follows
  (regime · entities/interop · acceptance · harm model · gate overlay · specialist
  roles · glossary · non-negotiables); `domains/README.md` documents the layer.
- **`domains/healthcare.md`** — the pilot/reference pack: HIPAA/HITECH + GDPR-health
  + IEC 62304 + DCB0129/0160 + FDA Part 11; FHIR/HL7/SNOMED/LOINC canonical entities;
  PHI-never-to-an-unBAA'd-LLM and clinical-safety non-negotiables.
- **Two domain-specialist roles** (35 → **37 roles**): `roles/clinical-safety-officer.md`
  (patient-safety veto at G5; owns the hazard log) and `roles/regulatory-affairs.md`
  (classification, submissions, audit liaison; reused across regulated domains). Both
  signed by `doctrine_signature`.

### Changed
- `.Doctrine.md` §6 gains a domain-overlay routing row and §10 gains a `⁽ᵈ⁾`
  domain-specialist class (with legend); README/plugin counts updated (37 roles,
  10 templates, the `domains/` tree entry).
- `doctrine_lint` `check_references` now validates `domains/` paths (REF_RE), so
  broken pack references fail the corpus gate like any other.
- Adding the two roles auto-updated the `privacy-compliance` and `testing` skill
  Signatures (their generated used-by-roles lists) — the generated-signature system
  staying true by construction.

## [0.6.29] - 2026-07-19

### Added
- **`tools/doctrine_signature.py`** — the Signature convention (introduced in
  0.6.28 as a hand-written exemplar) becomes a **generated, lint-enforced
  artifact**. The tool derives each role/skill's block across the eight mechanism
  dimensions from the corpus's own primary sources — a role's `Loads` line (→
  skills), its `.claude/agents` card (→ subagent + declared tool grant), the
  inverse used-by map (→ a skill's roles), a small stable gate-ownership map —
  and writes it into a marker-managed block (`<!-- SIGNATURE:BEGIN … END -->`)
  that leaves all hand-written prose untouched. `--write` regenerates; the
  default mode diffs and reports drift. Two small in-code maps (`ROLE_GATE`,
  `SKILL_EXTRA`) are the only hand-kept config; the 90 blocks are fully derived.
- **`doctrine_lint` check_signatures** — a missing or drifted Signature block now
  **fails the corpus gate** (fix: `make sign`). Gated like `check_version`: a
  source-repo authoring invariant, skipped in consumer repos whose installed
  `.Doctrine/` corpus is a read-only snapshot (§12).
- **Signatures materialized on all 90 disciplines** — 35 role cards + 55 skill
  playbooks now each carry a generated Signature block, replacing the single
  hand-written exemplar. Honest by construction: a reviewer role that loads only
  standards shows `Skills: —`; a role with no `.claude/agents` card shows
  `Subagents: —`.
- Tests: `tests/test_doctrine_signature.py` — determinism, marker-scoped splicing
  (prose outside the markers is never touched), drift detection (hand-edit → stale),
  used-by inversion, and the source-only lint gating (12 tests).

### Changed
- `make sign` target; `doctrine-signature` console script + `py-modules` entry;
  `doctrine_signature.py` joins the installer `TOOL_FILES` (ships to consumers so
  they can re-sign their own corpus extensions).
- `plugin.json` description count corrected: 52 → 55 skills.

### Rationale
- The hand-written Signature (0.6.28) was a drift liability: nothing stopped a
  role's declared skills from diverging from its actual `Loads` line. Deriving the
  block from primary sources and failing the build on drift makes the honesty
  ledger *true by construction* rather than by discipline. More work once; correct
  forever.

## [0.6.28] - 2026-07-19

### Added
- **`skills/engagement-engineering.md`** — the engagement-craft discipline: *how the
  agent engages* a task and a human across the lifecycle (open → clarify-or-proceed →
  right-resolution execution → honest status → clean handoff). Unifies pieces that
  were scattered across §2 (the Engagement Protocol), `requirements`, `ponytail`,
  `loop-engineering`, the state plane, and the autonomy-resolution / trust-ratchet
  model into one named, **cross-cutting** discipline (applied by every role, like
  `ponytail`). Realized on existing machinery — the doctrine-engage `UserPromptSubmit`
  hook = *open*; escalation-park + §5 = *checkpoint*; the state-plane checkpoint =
  *handoff*. Deliberately a **skill, not a role** (engagement is cross-cutting craft,
  not a gate-owning function).
- **Discipline "Signature" convention** — a discipline declares its composition across
  the eight mechanism dimensions (**roles · skills · tools · plugins · workflows ·
  hooks · MCP servers · subagents**; multiples where they exist, `—` where none, `◻`
  planned). `engagement-engineering` carries the first Signature as the pattern.

### Changed
- Routing table + counts: 54 → 55 discipline playbooks; `engagement-engineering`
  added to the always-on craft set ("Any code at all") + a dedicated routing row.

## [0.6.27] - 2026-07-18

### Added
- **`skills/accounting.md`** — the bookkeeping/accounting discipline (double-entry,
  the three tying statements, journal entries, reconciliation, month-end close,
  variance analysis, audit support) under Finance Ops, with the draft-only /
  CPA-reviewed / never-moves-money guardrail (§5). Distinct from `finance.md`
  (forward-looking runway/budgets/unit-economics); this is *the books*. Harvested as
  the one genuine gap from a 42-agent task-catalog — the rest was already covered by
  existing roles, or is task-level work those roles perform (not new roles: turning
  micro-agents into 42 roles would break the separation-of-duties role model).

### Changed
- **`skills/marketing.md`** — added a Search & answer-engine optimization (SEO/GEO)
  section: earn citations from AI answer engines through genuine structured
  authority (never tricks), and tie rankings to the funnel metric.
- **`skills/legal-basics.md`** — added a Vendor assessment section (terms/liability,
  data handling, security posture, red flags) — the non-code-vendor equivalent of
  what `dependency-policy` does for code deps; the decision stays the human's (§5).
- Routing table + counts: 53 → 54 discipline playbooks.

## [0.6.26] - 2026-07-17

### Added
- **`skills/debugging.md`** — a systematic debugging / root-cause discipline:
  reproduce-first, a hypothesis-driven loop (refute, don't confirm), the
  vendor-neutral techniques (git bisect, minimal reproduction, differential
  debugging, trace-to-origin), cause-not-symptom, and a regression test that
  proves the fix. Fills a real gap — "debug" was scattered across
  observability/incident-response but had no dedicated dev-time bug-hunting
  playbook. **Distilled (not copied), vendor-neutral, agent-agnostic** from the
  open coding disciplines in the awesome-claude-skills survey
  (`root-cause-tracing`, `test-fixing`); no third-party package, script, or
  service was adopted — the vendor-locked and already-covered entries were
  deliberately excluded.

### Changed
- **`skills/repo-devops.md`** — added a *git worktrees* section for parallel-safe
  local work (isolated working trees over one shared `.git`), reinforcing that
  the version line stays single-writer (worktrees isolate editing, not landing).
- Routing table + counts: 52 → 53 discipline playbooks.

## [0.6.25] - 2026-07-17

### Added
- **Data Architect role (`roles/data-architect.md`) + `skills/data-architecture.md`**
  — data modeling (conceptual/logical/physical) and storage topology
  (OLTP/warehouse/lakehouse/mesh, system-of-record, expand-contract evolution,
  one-definition-per-entity). Bounded against Chief Architect (whole system),
  Head of Data (governance), Data Engineer (pipelines), Database Engineer (schema).
- **Database Administrator role (`roles/database-administrator.md`) +
  `skills/database-operations.md`** — DB *operations*: tested restores, RPO/RTO,
  HA/DR, prod-safe migrations (lock scope, online/expand-contract), performance
  ops, least-privilege access. Bounded against Database Engineer (designs schema)
  and SRE (whole-system reliability). Destructive ops are §5-gated.
- **`skills/platform-integrations.md` ("Spaces")** — governed integration with
  external enterprise platforms (Hugging Face, Snowflake, ServiceNow, Salesforce,
  Jira, …): intake checklist (auth / data-direction / SDK / limits / failure),
  §5 on outbound writes to a system of record, secrets-in-manager, sandbox-first,
  and an extensible platform catalog.
- **Four language profiles (6 → 10):** C/C++, Ruby, PHP, Swift — toolchain,
  format/lint, idioms, the no-swallow error rule, testing, dependency audit.
- **Observability stacks catalog** in `skills/observability.md` — three pillars
  + OpenTelemetry (instrument once, export anywhere); Prometheus/Grafana,
  ELK/Loki, Jaeger/Tempo, Datadog, Sentry, each with cost/PII/§5 watch-items.

### Changed
- Routing table + role index wired for the 2 roles and 3 skills; counts
  33 → 35 role cards (24 engineering) and 49 → 52 discipline playbooks.

## [0.6.24] - 2026-07-17

### Added
- **Data Analytics discipline (`roles/data-analyst.md` + `skills/data-analytics.md`
  + `templates/analysis-report.md`)** — the catalog had Data *Engineering* (Data
  Engineer + `data-engineering` + Head of Data) but no Data *Analytics*: no analyst
  role, no analytics skill. They are distinct disciplines — engineering *moves and
  stores* data, analytics *derives decisions from* it. New **Data Analyst** role +
  **data-analytics** skill cover analysis, BI/dashboards, experimentation, and metric
  definition on a decision-first, honest-statistics discipline:
  one-metric-one-definition, uncertainty + confounders reported, no
  correlation-as-causation, reproducible query, PII aggregated
  (`privacy-compliance`), and **p-hacking treated as a §1 honesty violation, not a
  technique**. `templates/analysis-report.md` (the decision-serving readout) ships
  with it. **Data Engineering rounded out** with the template it lacked:
  `templates/data-contract.md` (schema-as-promise, change policy, lineage/retention;
  Head of Data co-signs). Wired into the §6 routing table + §10 role index (33 roles
  / 49 skills); filed with a G0 brief.

## [0.6.23] - 2026-07-16

### Added
- **Web Design discipline — a designer, recruited (`roles/web-designer.md` +
  `skills/web-design.md`)** — Doctrine could *publish* a site (`web-publishing`)
  but had no one who made it *look* designed: UX Designer owns flows, Frontend
  Engineer implements, `ui` covers components — zero visual/web/brand coverage, so
  generated sites looked dev-built. New **Web Designer** role + **web-design** skill
  fill it, on one strategy: **borrow a proven open-source template and map the
  repo's own content into it**, rather than invent design from scratch. The skill
  encodes the corporate-site structure (hero → features → docs → about → CTA →
  footer), a **template catalog** of free/open-source options (Material for MkDocs,
  Docusaurus, Nextra, Start Bootstrap, HTML5 UP…) with **license discipline**
  (check + attribute + comply; CC-BY keeps its credit), real-content-not-lorem
  mapping, self-contained-not-CDN, and accessibility. Wired into the §6 routing
  table + §10 role index; filed with a G0 brief. Honest constraint recorded:
  external template repos can't be fetched from a sandbox, so the skill carries the
  catalog for per-project borrowing and a strong self-contained default ships in
  the generator. Proven by upgrading the repo's own site generator
  (`scripts/build_site.py`) to a corporate-quality template.

## [0.6.22] - 2026-07-16

### Added
- **Web publishing — GitHub Pages, project website, and GitHub wiki
  (`skills/web-publishing.md`)** — the doctrine had no coverage for publishing a
  repo to a web surface (grep: 0 hits), and no support for auto-publish-on-push.
  New skill governs all three surfaces plus **opt-in auto-publish on commit/push**,
  on one load-bearing rule: *auto-publish to a public surface is auto-EXPOSE on
  every push.* So (1) **opt-in is a §5 decision made once** and recorded
  (`Web publish: pages | site | wiki | off` in the brief), **never default-on** —
  the choice is the escalation, not each push; (2) publish a **designated source
  only** (`/docs`/`site/`/an artifact), never secrets/drafts/whole-repo; (3) the
  publish workflow **fails closed** — build + link-check + secret-scan before
  deploy, so a broken/leaky build never goes live. Includes a hardened,
  SHA-pinned reference Actions workflow (path-scoped, `deploy-pages`), the
  Pages/website/wiki specifics (one-way docs→wiki, custom-domain = §5), and
  wiring into the §6 routing table + the Tech Writer role's Loads. Filed with a
  G0 brief; enforcement of the publish gate is the workflow's (fail-closed), the
  opt-in is the human's.

## [0.6.21] - 2026-07-16

### Fixed
- **Installer atomic-update guard — no more partial-update framework drift** — a
  non-force install into a repo that already has Doctrine copied *new* framework
  files while *skipping* changed ones (`copy_file` preserves different-content
  files without `--force`). When the skipped set included a **consistency
  carrier** — `.Doctrine/README.md` (the role/skill counts),
  `tools/doctrine_install.py` (the file manifest), or `.Doctrine.md` (the law) —
  the consumer's framework went internally inconsistent (new files present, counts/
  manifest stale), so its *own* `doctrine_lint`/`doctrine_packaging` failed. Found
  live in a consumer repo after a non-force "hook-merge" update. `install()` now
  refuses **before touching the target** when updating an existing Doctrine and any
  consistency carrier would differ, pointing to `--force` (which updates the whole
  framework atomically). A generic differing file still skips-with-a-warning —
  idempotent re-install and local-edit preservation are unchanged. Regression:
  `tests/test_doctrine_install_atomic.py`; the packaging suite (idempotent,
  differing-file-skip) stays green. Same consumer-vs-source hazard class as the
  v0.6.10→v0.6.18 retro, one layer down: a partial *update* is its own drift source.

## [0.6.20] - 2026-07-16

### Added
- **Governed use of external MCP servers (ADR-005 + `skills/mcp-tooling.md`)** —
  the doctrine had no discipline for *consuming* external MCP servers (it only
  *ships* the `doctrineos` server); grep for `Sentry` returned zero hits. New
  `skills/mcp-tooling.md` governs MCP tool-use for **any** feature development
  (not DevOps-only), on four invariants: **open-source-first** (an MCP server is a
  dependency — same `dependency-policy` bar; a closed/hosted data-touching MCP is a
  §5 decision); **intended, available, else fall back** (match the MCP to intent,
  use only if wired, otherwise fall back to the CLI — never block a task on an absent
  MCP); **MCP actions are governed actions** (read-only/least-privilege by default;
  every write/deploy/spend/delete/send = §5 escalation; secrets in the server's auth
  config never the repo; attributable + tested); **no skill-per-server** (one
  principle-first skill + an illustrative catalog — GitHub/Docker/cloud/Sentry —
  that grows by registry entry, not by rotting per-provider files). Wired into the §6
  routing table and the DevOps Engineer role's Loads; ADR-005 records the decision.
  Enforcement is advisory until a mechanical MCP-action gate lands (PreToolUse /
  external pre-execution authorization — the L3 successor to ADR-004).

## [0.6.19] - 2026-07-16

### Added
- **Activation layer — repos reliably wake Doctrine up (ADR-004)** — Doctrine
  was advisory: loaded into context and reliant on the agent *choosing* to
  engage, so installed repos often never triggered the Engagement Protocol
  (loaded-but-not-obeyed, or never fully wired). Two mechanisms close the gap.
  **L0 `doctrine_awaken`** — an activation doctor that audits a repo's wake-up
  wiring (presence · CLAUDE.md/AGENTS.md load · SessionStart+UserPromptSubmit
  hooks · state plane) and reports each gap with a remediation; exit non-zero on
  a critical gap, so "installed but not triggering" is diagnosable in one
  command. **L1 `doctrine_engage` + a `UserPromptSubmit` hook** — re-arms the
  Engagement Protocol on *every* user message (an injected compact reminder),
  turning "loaded once at session start, forgotten mid-session" into "prompted
  every turn." Both **consumer-safe by construction** (engage no-ops outside a
  doctrine repo; the plugin hook keeps its `os.path.exists` guard; awaken
  inspects wiring only) — the v0.6.10→v0.6.18 retro's dominant bug class
  designed out up front — and ASCII-only (Windows cp1252). Wired into
  `.claude/settings.json` + `plugin/hooks/hooks.json`; both tools shipped by the
  installer (`TOOL_FILES`). L2 (`.claude/rules/` path-routing pack) and L3
  (`PreToolUse` hard gates) are ADR-004 roadmap. Filed with the full G0→G2 trail
  (brief/ADR-004/plan) + `tests/test_doctrine_awaken.py` — dogfooding the retro's
  self-application amendment.

## [0.6.18] - 2026-07-16

### Added
- **Platform Engineering discipline** — a new role
  (`roles/platform-engineer.md`) and skill (`skills/platform-engineering.md`)
  fill the gap between DevOps (a repo's tooling/CI) and SRE (reliability/SLOs):
  the internal platform *as a product* — paved roads, shared substrate,
  self-service infra, developer experience; owns the cross-repo substrate both
  build on. Principles: platform-the-second-use, golden-path-not-golden-cage
  (every road has a documented escape hatch), contracts+versions on shared
  substrate, self-service over tickets. New `templates/paved-road.md` is the
  per-road artifact. Wired into the §6 routing table and §10 role index.
- **PaaS deploy-target skills** — `skills/cloud-vercel.md`, `cloud-railway.md`,
  `cloud-render.md`, `cloud-fly.md` extend cloud coverage below the major
  providers. Honest local-first story: unlike aws/azure/gcp (floci-emulated),
  PaaS targets are **not** emulated, so the parity path is Docker/CLI
  (`vercel dev`, `railway run`, …) + preview deploys, with a local → preview →
  prod promotion ladder and elevation to prod as a §5 escalation. The §6
  Cloud-stage row now records `Cloud target: …|vercel|railway|render|fly`.

## [0.6.17] - 2026-07-14

### Fixed
- **`doctrine_lint` version check — whole bug class swept (CHANGELOG too)** —
  0.6.16 fixed the consumer `pyproject` false-desync but missed the sibling
  **CHANGELOG** check in the same function; a consumer repo with its own
  product CHANGELOG (found live: a consumer repo at 0.2.0) failed lint with a false
  "version desync: .Doctrine.md v0.6.16 != CHANGELOG 0.2.0". `check_version`
  now computes `is_source` once (pyproject declares `doctrineos`) and gates
  ALL Doctrine-owned carriers — CHANGELOG, pyproject, plugin.json, README
  badge — on it; only `doctrine_mcp.py` (Doctrine's own file even inside a
  consumer) is always checked. Source behavior unchanged. Regression tests:
  consumer CHANGELOG not flagged; source CHANGELOG desync still caught.
  Lesson applied: fix the whole bug class, not the one instance.

## [0.6.16] - 2026-07-14

### Fixed
- **`doctrine_lint` version check is now consumer-safe** — it treated *any*
  `pyproject.toml` `version = "X.Y.Z"` as a Doctrine version carrier, so a
  consumer repo with its own product version (found live: a consumer repo at 0.1.0)
  failed lint with a false "version desync: pyproject.toml 0.1.0 !=
  .Doctrine.md v0.6.15". `pyproject.toml` is now a carrier only when it
  declares the `doctrineos` package (which the installer never copies); a
  consumer's own pyproject is left alone. Same consumer-vs-source lesson as
  ADR-002. Regression tests: consumer pyproject not flagged; a real
  `doctrineos` desync still caught. Surfaced by installing Doctrine into a
  new consumer product repo.

## [0.6.15] - 2026-07-14

### Added
- **Product-family topology, formalized (ADR-003 + a template)** — the
  three-repo shape is now a written decision, not a recommendation:
  `doctrine` (governance + tooling) + `maple-oss` (runtime) + the product
  (`product-app`), with a **one-way dependency graph** (product → {doctrine,
  maple}; doctrine ⟂ maple, no cycles). `docs/adr/003-product-family-topology.md`
  fixes the boundaries and the rationale (separate repos for
  license/cadence/visibility; a monorepo would spread MAPLE's AGPL to all).
  New `templates/compatibility-manifest.md` (G6 artifact) is the per-release
  **stack BOM**: the certified doctrine+maple versions for each product
  release, the family-gate evidence checklist (Doctrine↔MAPLE smoke, product
  gates, AGPL ack), and rollback. Routing-table row added. **Deferred, on
  purpose:** the *running* family gate (CI pinning + testing three repos)
  waits until the `product-app` repo exists — a gate over a missing repo is
  unenforceable; the contract is written first so it guides creation.

## [0.6.14] - 2026-07-14

### Changed
- **MAPLE integration updated to maple-oss 1.1.2** — all five enhancement
  asks shipped upstream and are now reflected in `integrations/maple.md`,
  verified here against the 1.1.2 source tree (real smoke output, all
  pass): (1) `register_handler` case-trap fixed; (2) `send(...,
  require_routable=True)` → `Err UNROUTABLE`; (3) broker-enforced
  fresh-context verifier preset (`maple.security.separation`) that blocks
  a verifier→builder route — **separation of duties is now a runtime
  guarantee, not a convention, closing the v0.6.11 caveat**; (4) the
  doctrine profile (`maple.adapters.doctrine_adapter`:
  `build_work_package`/`build_gate_result` + validators, `GATE_VERDICTS`);
  (5) `tokens` as a first-class `ResourceRequest` type. The "sharp edges"
  section becomes "Resolved in 1.1.2"; the "enhancement asks" become
  "shipped"; `pinned_version` 1.1.1 → 1.1.2. License disposition unchanged
  (AGPL, never vendored/imported — the profile ships inside maple-oss).

## [0.6.13] - 2026-07-14

### Fixed
- **`doctrine_verify` is now consumer-safe (ADR-002)** — in a consumer repo
  it ran `ruff check tools tests` and `unittest discover -s tests` against
  the HOST's own code: linting the host's files under Doctrine's ruff config
  and running the host's whole suite plus Doctrine's heavyweight self-tests
  (git-spawning, minutes-long). Reported live from the MAPLE repo (ruff
  flooded with the host's findings; the test gate hung). Now scope-aware:
  `is_source_repo()` (true only when `pyproject.toml` declares `doctrineos`,
  which the installer never copies) runs the full dev suite in the source
  repo, while a consumer verifies only Doctrine's own surface — corpus
  **lint** + **state** — and skips ruff/tests with a note pointing to
  `unittest discover -s tests -p "test_doctrine_*.py"` for the tool tests.
  New `tests/test_doctrine_verify.py`; QUICKSTART re-verify note corrected.
  Resolves the consumer-vs-source verify-surface debt parked in ADR-001.

## [0.6.12] - 2026-07-13

### Added
- **Turnkey install (productization v0.1)** — the installer becomes one
  command that ends verified. `doctrine_install --verify` initializes the
  state plane and runs the gate suite in the target after copying, so a
  single `python tools/doctrine_install.py --target <repo> --verify` goes
  from a doctrine clone to a proven-green install (no separate init/verify
  steps). `--maple` seeds `Workforce runtime: maple` in the target brief
  (opt-in MAPLE runtime), mirroring `--enterprise`/`--startup`. New
  top-level `QUICKSTART.md` documents zero-to-verified. First slice of the
  DoctrineOS productization program (strategy brief kept private;
  `docs/adr/001-turnkey-distribution.md`, `docs/plans/productization-v0.1.md`).
  Verification is honest: nothing is weakened to go green, the real gate
  exit code is surfaced, and a failing suite makes the install exit
  non-zero. Regression tests assert the plumbing (state-init→verify, cwd,
  exit-code propagation, opt-in seeding) without re-running the full suite.

## [0.6.11] - 2026-07-13

### Added
- **MAPLE runtime integration (opt-in)** — `integrations/maple.md` wires
  MAPLE (`maple-oss` 1.1.1, mapleagent.org — first-party, same author)
  as the doctrine's optional multi-agent workforce runtime: roles become
  persistent addressable agents, work packages and gate verdicts become
  typed messages (`WORK.PACKAGE` / `GATE.RESULT` carrying artifact
  hashedrefs, never prose), `Result<T,E>` carries honest failure,
  link-identified channels enforce separation of duties (verifiers hold
  links only to the orchestrator), and `execute_consensus` maps to the
  verifier panel. Two hard boundaries in law: MAPLE routes, gates
  decide; the state plane stays the durable truth (broker state is
  ephemeral). Verified live on Windows/Py3.12 with an in-process-broker
  smoke test. Ships with a reproduced sharp-edges list (handler-key
  case trap; `send()` Ok = enqueue, not delivery) and a five-item
  upstream enhancement wishlist for `maple-oss`. AGPL-3.0 disposition
  recorded per dependency policy: never vendored, never imported by
  doctrineos — document + protocol contract only; consumers opting in
  flag `Workforce runtime: maple` in their brief. Routing table row
  added.

## [0.6.10] - 2026-07-13

### Added
- **The Engagement Protocol** — the observable cue that Doctrine kicked
  in. On EVERY user command in a doctrine repo, the agent's response
  OPENS with the Engagement Block before any work: `[DOCTRINE ENGAGED]`
  + Class / Role / Loads / Gates / Governance / Profiles (one-line form
  for Class S — right-sized ceremony applies to the ritual itself).
  Explicit cues: `doctrine: <task>` forces engagement; only the human
  can bypass, and a bypass is announced (`[DOCTRINE BYPASSED — human
  instruction]`), never silent. Autonomy contract stated in law: after
  the block, the agent executes the gates without waiting — pausing
  only at §5 escalations. Shipped as: `.Doctrine.md` §2 (the law),
  AGENTS.md compression (all agents), `/doctrine` command for Claude
  Code (.claude + plugin, byte-parity lint-enforced).

## [0.6.9] - 2026-07-13

### Added
- **Governance layer (GRC)** — four heads above the gates, policy
  separated from enforcement (`standards/governance.md`): **Head of
  AI** (model/vendor policy, eval standard, responsible-AI boundary,
  model inventory), **Head of Data** (data contracts, lineage,
  retention map, one-definition-per-entity), **CISO** (security
  posture, threat-model registry, exception register — every accepted
  risk carries the human's signature AND an expiry; the
  security-reviewer keeps the G5 ship veto), **Risk Officer**
  (enterprise risk register, `templates/risk-register.md` →
  `docs/risk/register.md`, deltas reviewed at every G7; "a risk nobody
  re-reviews is a surprise on a schedule"). G1 gains the governance
  co-sign (mandatory on enterprise-profile repos). Deliberate
  non-role, recorded in the standard: hands-on "cybersecurity" stays
  with engineers + the security-reviewer — three hats, no fourth.
- **Core delivery craft completed** (user-spotted gap): new
  `skills/architecture.md` (the G1 craft: boundaries where change
  happens together; an ADR with one option is a memo; failure modes
  before happy path) and `skills/requirements.md` (the G0 craft:
  problems not solutions; ACs are executable sentences; QA's
  adversarial classes start at intake). Wired into chief-architect and
  product-owner Loads.
- Counts: 30 roles, 40 skills, 8 standards, 9 templates.

## [0.6.8] - 2026-07-13

### Added
- **Startup craft skills** — the discipline layer under the v0.6.7
  founder-ops roles, house format, seven playbooks: `marketing`
  (positioning is one sentence; a launch is a release, apology draft
  pre-written), `content` (write from the CHANGELOG outward; every
  claim carries a claims-table row for pre-send review), `sales`
  (FDE-scripted demos rehearsed to hash-stable; verbatim CRM notes;
  lost-deal truth feeds G0), `customer-support` (severity = user
  impact; reproduce before routing), `finance` (runway from measured
  burn, never hope-math; measured|estimated|projected labels survive
  quotation), `legal-basics` (obligations register; policy must match
  the actual data map; never practices law), `fundraising` (KPIs
  defined once and stable; lowlights as prominent as highlights).
  Role Loads wired; skill count 31 → 38.

## [0.6.7] - 2026-07-13

### Added
- **Startup profile** (OPT-IN via `Company profile: startup` in the
  brief; installer `--startup` seeds it): seven founder-ops roles —
  Growth Marketer, Content Marketer (claims trace to shipped tags),
  Sales/GTM (demos via the FDE; pricing is a human decision), Support
  Engineer (the user→gates bridge: a reproduced bug becomes a G0 brief
  or HOTFIX), Finance Ops (models, never moves money), Legal Ops
  (drafts, never practices law), Investor Relations (real metrics with
  fidelity labels; "good news and bad in the same font size"). Two iron
  laws on every card: **draft-never-send** (all external actions are
  the human's, §5) and the **honesty law beyond code** (no invented
  testimonials/figures; estimates labeled). All main-thread roles.
  Role count 19 → 26; routing table +7 rows; tests 110 → 111.

## [0.6.6] - 2026-07-13

### Added
- `tools/doctrine_verify.py` — the one-command gate suite,
  cross-platform (stock Windows has no `make`; a Windows-first consumer
  hit exactly that). Runs lint → ruff (skipped with a note when not
  installed) → tests → state-chain verify (skipped before `state
  init`); `make verify` now delegates to it. Verified live: 4 gates
  green through the single command. Plugin /doctrine-verify and
  installer next-steps updated.

### Fixed
- **Escaped packaging defect**: `doctrine_metrics.py` (added v0.6.1)
  was never in the installer's `TOOL_FILES`, so consumer repos lacked
  it while their copied SessionStart hook referenced it unguarded —
  every session in an installed repo opened with a hook error. Now
  shipped, with a regression test asserting every `tools/doctrine_*.py`
  is in `TOOL_FILES` (the class, not the instance). Existing installs:
  re-run the installer. Tests 109 → 110.

## [0.6.5] - 2026-07-13

### Changed
- **History rewritten** (operator decision): `Co-Authored-By` trailers
  stripped from all 44 commits via git-filter-repo; all 17 tags
  rewritten in place. Requires `git push --force --all && git push
  --force --tags`; stale clones must be re-cloned. Pre-rewrite history
  preserved in a local bundle.
- **Provenance migrated from trailers to the enrichment overlay**:
  `doctrine_metrics enrich --mark-authorship agent_assisted` asserts
  authorship for every HEAD-reachable commit (a blanket operator claim,
  documented as such). Verified live: CodeMonk again reports
  44 agent / 0 human without any trailer. Commit shas quoted in the
  audit trail (reviews/QA/retro) re-mapped to the rewritten history via
  the filter-repo commit-map (strict 40-hex parsing, word-boundary
  replacement); state-plane `at_commit` anchors are content-hash-chained
  and stay untouched — pre-rewrite anchors are historical.
- Post-rewrite metrics snapshot filed; enrichment message now reports
  entries vs reviewed separately. Tests 107 → 109.

## [0.6.4] - 2026-07-13

### Added
- **Token-capture wiring documented exactly** (closes the last unfed
  metric family, TCR / cost-per-landed-change): capture is a
  session-launch choice — OTel env must exist before the agent starts,
  no hook can enable it retroactively. Two wirings in
  `integrations/codemonk.md`: `codemonk wrap --otel -- claude`
  (endpoint spawned, env pre-wired) or a standing `codemonk collect`
  on 127.0.0.1:4318 with the four env exports (extracted from CodeMonk
  0.10.0 source, verified live). Events land in `codemonk_tokens.jsonl`
  (gitignored); report via `codemonk tokens --log`.
- `doctrine_metrics capture-hint` — a SessionStart hint (never a gate,
  always exit 0) fires only when a metrics-adopted repo runs
  uncaptured; wired into `.claude/settings.json` and the plugin hooks.
  3 new tests (107 total).

## [0.6.3] - 2026-07-13

### Added
- **Gate instrumentation** — `doctrine_metrics.py gates` mines the
  process's own story from what the pipeline already files: per-release
  cycle time, commit/fix volume, and review-verdict events (counted only
  on added artifact lines that NAME a verdict, so prose "veto" and
  pasted `CHECK FAILED` output cannot inflate the numbers; adverse =
  REQUEST-CHANGES/VETO/FAIL). First real report committed at
  `docs/metrics/gates-2026-07-13.md`: 14 release windows, 36 commits,
  7 fix commits, 4 adverse verdicts — the five review rounds are now
  visible as data. A zero-adverse release with material change is
  flagged for retro scrutiny, mirroring the HITL/CESR erosion gate.

### Fixed
- **Escaped defect from v0.6.2** (found by flaky-test triage, fixed
  fail-closed): after a shared-distillate merge, the loser's orphaned
  original distillate stayed at the forked seq, leaving
  `_distillate_files[-1]` ambiguous by hash order — verify desynced on
  roughly half of hash draws. Merge now archives every same-seq
  distillate no survivor references. Suite deterministic across three
  consecutive full runs (104 tests).

## [0.6.2] - 2026-07-12

### Added
- **State-plane concurrency** (spec 0.3.0) — closes audit gap #1, the
  linear-chain assumption. Same worktree: an advisory session lease
  (`local/lease.json`, TTL 1h, gitignored) guards chain append;
  `checkpoint --steal` takes over loudly. Across clones: `verify`
  reports `CHAIN FORKED` naming both heads (hydrate refuses — a fork is
  a loud full stop); `merge --loser` archives the losing head +
  distillate under `forks/` (history never deleted), repoints to the
  winning head, salvages the loser's dead_ends into the next
  checkpoint's pending file (scanned at merge time — a poisoned loser
  cannot soft-lock the plane), prints learned/open_threads for honest
  re-proposal, and runs a MANDATORY post-merge verify. Leaf-only;
  descendants refuse with iterate-from-the-leaf guidance.

### Fixed (review round #5: APPROVE-WITH-NITS + security SIGN-OFF)
- All findings landed: merge StateErrors cleanly on malformed losers
  (SC-1), lease parse hardened via load_json (LE-1), post-merge verify
  mandatory (MG-1), shared distillates never archived (MG-2), salvage
  scanned at merge (SV-1), plan wording corrected (SC-2), empty salvage
  and stray-directory messages honest (SC-3/SC-5), prune comment
  accurate (SC-4). Tests 92 → 96 incl. a genuine two-clone fork
  simulation and three-way-fork coverage by the reviewer's probes.

## [0.6.1] - 2026-07-12

### Added
- `tools/doctrine_metrics.py enrich` — bridges the doctrine's review
  artifacts to CodeMonk: scans `docs/reviews|qa|merges` for commit
  references, verifies each against the repo (hex-validated before git
  argv, ancestor-of-HEAD only), and emits the enrichment overlay.
  **Verified end-to-end on this repo: HITL 0% → 27.3%** — the nine
  review-round commits now count as reviewed, with the fidelity label
  stated in the output (verifier fan-out, human-arbitrated). Enriched
  snapshot filed alongside the baseline; wired into pyproject
  (`doctrine-metrics`); 4 new tests (86 total).

## [0.6.0] - 2026-07-12

### Added
- **The Doctrine measures itself** — closes self-measurement, gap #2 of
  the fully-equipped-EOS audit. New `skills/metrics.md` (measure the
  process; HITL reduction only counts while CESR holds; metrics are G7
  inputs, never weapons; the honesty law applies to numbers) and
  `integrations/codemonk.md` — **CodeMonk 0.10.0** pinned as the
  metrology subsystem (CESR, agent engagement, HITL gated on CESR,
  token churn, cost per landed change; golden-vector metric spec, zero
  runtime deps). Verified by execution on this repo: 31 agent changes
  detected via commit trailers, CESR 100% (zero reverts — accurate);
  baseline filed at `docs/metrics/2026-07-12-baseline.md` with fidelity
  notes (git-only HITL reads 0 until review enrichment is wired).
- Routing row for process measurement; G7 attaches the scorecard where
  metrics are adopted; Project Reviewer conditionally loads the skill.
- `supportfolder/` gitignored (drop zone; upstream is pinned, never
  vendored — per the integrations rule).

## [0.5.0] - 2026-07-12

### Added
- **Packaged distribution** (`.Doctrine/05-packaging.md`):
  `tools/doctrine_install.py` installs the law + enforcement suite into
  any repo (idempotent, append-never-replace, never clobbers without
  `--force`, per-tool adapters, `--enterprise`/`--ci`);
  `tools/doctrine_mcp.py` — stdlib stdio MCP server exposing
  lint/state/gold tools to Claude Code, Codex, Cursor, Windsurf,
  Copilot, Gemini and any MCP-capable agent; **Claude Code plugin**
  (`/plugin marketplace add` → `/plugin install doctrine`) with
  /doctrine-init, /doctrine-verify, /gold-check, /checkpoint, 14
  subagents, guarded SessionStart hook, bundled MCP config — plugin
  wiring is byte-parity with `.claude/`, enforced by new lint checks;
  `pyproject.toml` builds the `doctrineos` wheel (publish human-gated).
- LICENSE (MIT). Version-sync lint: plugin manifest, pyproject, and MCP
  serverInfo must match the `.Doctrine.md` header.

### Fixed (review round #4: security SIGN-OFF; code REQUEST-CHANGES → fixed)
- Consumer repos now verify clean out of the box: lint skips
  source-repo-only checks (plugin parity, CHANGELOG sync) where those
  files don't exist, survives missing files as findings not crashes.
- MCP server no longer dies on malformed input: non-object lines/params/
  arguments and unknown/missing tool args are JSON-RPC errors; raw-line
  RecursionError caught; 5 MB line bound; serve-loop catch-all.
- Installer: refuses nested source/target (self-ingestion), preserves
  CRLF in appended files, never writes through symlinks without --force.

## [0.4.0] - 2026-07-12

### Added
- **Enterprise merge & promotion profile** (OPT-IN via
  `Merge profile: enterprise` in the brief; defaults unchanged
  otherwise): `standards/merge-and-promotion.md` — Merge Council with
  unanimity quorum for release-bound merges, a permission matrix
  (role → merge/tag/promote/deploy rights → enforcement mechanism), and
  the Gold Build ladder (candidate → soak → GOLD; deploy only from a
  gold record; **the hash chain is the rollback ladder**).
- `templates/merge-verdict.md` (council verdict record, filed at
  `docs/merges/`), `schemas/gold-build.schema.json` (content-pinned
  `hashedref`s, `prev_gold_sha256` chain), and `tools/doctrine_gold.py`
  (`record`: refuses without verdict + sign-offs + human approval, all
  content-pinned; `check`: the deploy gate — schema, re-hash, chain
  topology, tag→commit binding).
- Doctrine amendment (this round's lesson): `skills/backend.md` —
  content-hash references; existence is not evidence, mtime is not an
  authority signal.

### Security
- Delta review round-trip #3: security VETO reproduced chain forking
  via mtime forgery and "no verdict, no gold" satisfied by zero-byte
  files. Closed: chain order derives ONLY from prev-hash links (single
  genesis, no forks, full reachability — a broken ladder blocks ALL
  deploys); verdict and sign-offs content-pinned and re-hashed at the
  deploy gate; annotated-tags-only; tag format validated before git
  argv; hardened relpath schema. Re-verified by original exploits:
  APPROVE + SIGN-OFF. Suite: 70 tests.

## [0.3.0] - 2026-07-12

### Added
- **Sessions are now stateful by default.** `hydrate --if-present` (quiet
  no-op on an empty plane, for hooks) and `hydrate --emit-agents`
  (deterministic marker-managed state block in root AGENTS.md — any
  AGENTS.md-reading tool becomes stateful with zero integration).
  Claude Code wiring shipped: `.claude/settings.json` SessionStart hook,
  `CLAUDE.md` bundle import, `/checkpoint` slash command wrapping the
  propose→dispose protocol. A Stop-hook auto-checkpoint is deliberately
  absent: distillates are model-authored; a mechanical hook cannot write
  an honest one.
- `04-agent-adapters.md` State-plane wiring section; HYDRATION.md CLI
  section marked implemented.
- New standing-audit item 7 in `skills/security.md`: agent-context
  emission is an injection surface (second finding of that class this
  release cycle — the closed loop promoted it to law).

### Security
- Delta review round-trip on the emit path: the security VETO reproduced
  a managed-block breakout (marker tokens in model-authored state text
  escaping into committed AGENTS.md on re-emit, self-propagating).
  Closed with defense in depth: MARKER_RES rejection at checkpoint
  time, HTML-comment-token refusal at emit time (covers intent files
  written by other tools), strict one-ordered-pair marker integrity,
  byte-exact preservation outside the markers. Both verifiers re-ran the
  original probes: APPROVE + SIGN-OFF. Suite: 49 tests.

## [0.2.1] - 2026-07-12

### Added
- **G7 retrospective filed** (`docs/retro/2026-07-12-state-tooling.md`)
  by the Project Reviewer: 5-whys on the two deepest escaped defects,
  honest-negatives section, eight doctrine amendments — all applied:
  transactional append-only artifacts (backend), failure-path tests
  assert absence of side effects + valid×invalid cross-products
  (testing), own-state identifiers are a path trust boundary (security),
  required Threat sketch for Class L plans (template), ASCII-safe
  terminal output (python profile), OS-constraint ⇒ CI matrix leg
  (cicd), case-insensitively unique top-level dirs (repo-devops),
  "fixed" requires the re-executed original probe (dos-and-donts §7).
- `integrations/floci.md` — **floci verified real** (floci.io,
  github.com/floci-io, MIT): the cloud skills' emulator dependency
  resolves; documented fallbacks (LocalStack — auth-gated since 2026-03,
  Azurite, gcloud emulators).

### Changed
- CI: actions pinned to full commit SHAs (H-2 condition closed);
  `windows-latest` matrix leg added — the cp1252 output class is now
  covered by environment, not only by unit test.

## [0.2.0] - 2026-07-12

### Added
- **The doctrine is now mechanically enforced.** `tools/doctrine_state.py`:
  stdlib-only reference implementation of the state plane — init /
  checkpoint (propose→dispose, hash-chained, secret-scanned) / verify
  (chain + state_index re-hash incl. graph) / hydrate (budgeted bundle
  with per-section degrade-to forms, refuses unverified chains) / prune
  (dead_ends merge forward) / status. `tools/doctrine_lint.py`: 8-check
  corpus CI gate (references, formats, counts, version sync, canonical
  examples) — on its first run it caught real drift in the corpus.
  38 unit tests; Makefile (`make verify`) + GitHub Actions
  (least-privilege, ruff + corpus lint + suite).
- **First full dogfood of the doctrine's own process**: brief (G0), plan
  (G2), build (G3), then the G4/G5 verifier fan-out with its own
  subagents. Round 1: code review REQUEST-CHANGES (1 blocker, 7 major),
  security VETO (reproduced path traversal), QA FAIL (state-corrupting
  ordering bug). All findings remediated with regression tests; round 2:
  APPROVE-WITH-NITS + security SIGN-OFF + QA PASS. Artifacts under
  `docs/reviews/` and `docs/qa/`.

### Changed
- **State-plane spec 0.2.0**: state root renamed `.doctrine/state/` →
  `.doctrine-state/` (case-insensitive filesystems merge `.doctrine/`
  into `.Doctrine/`, landing runtime state inside the corpus — found by
  QA); checkpoint schema gains `$defs/intent_id` (path-traversal defense
  on `active_intents` and `state_index.intents` keys); examples
  re-serialized to canonical bytes (they violated their own no-trailing-
  whitespace rule).

### Security
- Round-1 veto findings all closed and re-verified by the original
  exploits: intent-id traversal (3 layers), CI token scope, unverified-
  chain hydration, unbounded JSON, stray-file crash, secret-like state
  content (fail-closed scan), git subprocess hardening. Actions
  SHA-pinning deferred with recorded rationale.

## [0.1.6] - 2026-07-12

### Added
- **Language profiles** (`standards/languages/`): Rust, Python, TypeScript
  (extracted from the old coding-standards sections and expanded with
  Testing/Dependencies), plus first-class Go, JVM (Java 21+/Kotlin), and
  .NET (C# 12+) profiles — the doctrine is no longer a Rust/Python/TS-only
  shop.
- **Five new adapters**: Cline (`.clinerules/`), Roo Code (`.roo/rules/`),
  Amazon Q (`.amazonq/rules/`), Continue (`.continue/rules/`), JetBrains
  Junie (`.junie/guidelines.md`); install map updated in
  `04-agent-adapters.md`.
- **Monorepo section** in `skills/repo-devops.md`: native workspaces,
  path-filtered CI, CODEOWNERS, nested AGENTS.md pointers.

### Changed
- `standards/coding-standards.md` rewritten as a language-neutral core +
  profile routing table; unprofiled languages get General rules + the
  ecosystem's canonical toolchain, with new profiles proposed via G7.

## [0.1.5] - 2026-07-12

### Added
- **Ten new skill playbooks** closing the enterprise-coverage gaps:
  `privacy-compliance`, `incident-response`, `resilience`, `concurrency`,
  `ml-engineering`, `data-engineering`, `iac`, `mobile`, `i18n`,
  `accessibility` — all in the house format (Principles/Defaults/Do/
  Don't/checklist/failure modes), 45–70 lines each.
- **Four new roles**: SRE (SLOs/error budgets; wears Incident Commander on
  HOTFIX, may freeze releases on budget burn), Data Engineer, ML Engineer
  (no prompt/model change without eval evidence), Compliance Officer
  (fresh-context verifier; can block ship pending human legal review).
- **Four new subagents** in `.claude/agents/` (sre, data-engineer,
  ml-engineer workers; compliance-officer verifier) — now 14 total:
  8 workers + 6 verifiers.

### Changed
- Routing table: eleven new rows (privacy, incidents, resilience,
  concurrency, ML, data, IaC, mobile, i18n, a11y).
- G5 gains conditional Compliance participation; HOTFIX names the SRE as
  Incident Commander; role counts updated everywhere (19 roles, 30 skills).

## [0.1.4] - 2026-07-12

### Changed
- The five previously orphaned skills (no role Loaded them) now have
  owners: `backend-engineer` loads `observability.md` and `performance.md`
  conditionally; `devops-engineer` loads `cloud-<provider>.md` per the
  brief's recorded `Cloud target` and its Activates-when now names cloud
  deploy/IaC work.

## [0.1.3] - 2026-07-12

### Added
- **FDE integrated as a first-class role**: `roles/fde.md` (frontmatter
  normalized to the role-card convention), skills
  `floci-{provision,seed,parity,promote}.md` under `skills/`, plus
  `rubrics/discovery.rubric.md`, `schemas/parity-ledger.schema.json`,
  `examples/floci.manifest.yaml`. Role index and routing table now route
  customer prototype/demo/PoC asks to it.
- **ponytail + graphify shims integrated**: `skills/ponytail.md` (brevity
  ladder, added to the "Any code at all" routing row) and
  `skills/graphify.md` (graph-before-grep, new structure-questions routing
  row); human-facing setup docs under `integrations/`.
- **State plane wired in**: routing row for session start/end/handoff;
  `01-workflow.md` session discipline references checkpoint + hydration.
- `integrations/` index with per-pack overview docs (fde, ponytail,
  graphify); AGENTS.md compression regenerated per the `04` sync rule.

### Changed
- Role count 14 → 15, skill count 14 → 20 (README layout and
  `02-role-protocol.md` updated); FDE added to the roles that stay in the
  main thread (`03-parallel-execution.md §5`) — its P1/P6 gates are
  human-interactive.
- Former pack folders `.Doctrine/FDE/` and `.Doctrine/graphify_PonyTail/`
  dissolved into the standard tree (all moves history-preserving renames).

## [0.1.2] - 2026-07-12

### Added
- `.Doctrine/state-plane/` — the doctrine-state-plane pack (checkpoint
  protocol, distillate schema, hydration compiler spec) extracted into the
  tree; it previously existed only as two redundant zips at the repo root.

### Removed
- All packaging debris from the raw pack drops, every removed copy verified
  byte-identical to the kept canonical first (originals reachable at
  `v0.1.0`): four root-level export zips, inner pack zips, flattened
  top-level duplicates in `FDE/` and `graphify_PonyTail/`, partial
  `mnt/user-data/outputs/` export copies, and the literal
  `{brace-expansion}` scaffold directories.
- Canonical single copies now: `.Doctrine/FDE/fde-floci-pack/`,
  `.Doctrine/graphify_PonyTail/doctrine-integrations/`,
  `.Doctrine/state-plane/`.

## [0.1.1] - 2026-07-12

### Fixed
- `.Doctrine/README.md` skill-playbook count corrected (ten → fourteen).
- G4/G5 gate-labeling conflict resolved: `code-reviewer` subagent description
  now names the G4/G5 review fan-out (per `03-parallel-execution.md §4`)
  instead of implying security-reviewer and qa-engineer run at G4.
- `.Doctrine.md §8` artifact tree: retrospective filename aligned with the
  template (`retro/<date>-<slug>.md`); release-checklist filing path added
  (`docs/releases/vX.Y.Z.md`) and mirrored in the template header.
- `01-workflow.md` G1 exit clarified: the ADR set *is* the design document
  (no separate design-doc template exists by design).
- Severity labels in `templates/code-review-report.md` aligned to the
  bracketed form used by the role card and workflow (`[BLOCKER]` …).

### Removed
- Duplicate `.Doctrine/agents/` folder (byte-identical copy of
  `.claude/agents/`). Canonical location is `.claude/agents/`, as stated in
  `.Doctrine.md §11` and the README layout.

### Added
- `CLAUDE.md` bootstrap shipping the `@.Doctrine.md` import that `§11` and
  `adapters/AGENTS.md` instruct users to create.
- `CHANGELOG.md` (this file), `.gitignore`, `.gitattributes` (LF-canonical,
  matching the pack-wide canonicalization rules).
- Doctrine version of record now tracked in the `.Doctrine.md` header.

## [0.1.0] - 2026-07-12

### Added
- Baseline import of the Doctrine System as received: root operating system
  (`.Doctrine.md`), 14 role cards, 14 skill playbooks, 6 standards,
  7 templates, gated workflow G0–G7, role protocol, parallel-execution
  protocol, multi-agent adapters (AGENTS.md + overlays), 10 Claude Code
  subagents, and un-integrated add-on packs (FDE/floci, graphify+ponytail,
  doctrine-state-plane zips) preserved for history.

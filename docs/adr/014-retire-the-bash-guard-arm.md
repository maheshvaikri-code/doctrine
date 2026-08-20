# ADR-014: retire the Bash arm of the `PreToolUse` guard

<!-- G1 artifact. File as docs/adr/NNN-slug.md. One decision per ADR. -->

**Date:** 2026-08-19 · **Status:** accepted
**Deciders:** framework owner (explicit, offered options with the tradeoff shown), Chief Architect

## Context

Doctrine's `PreToolUse` guard governed two surfaces. On **Write/Edit** it is sound: the
payload names one file in one field, so a path is data, not a language to interpret. On
**Bash** it analysed the command *text* to decide whether the command would write a
protected path. §7 and `05-packaging.md` have both described that arm as *"a tripwire,
not a boundary"* for several releases, on the strength of three independent security
passes that each found new bypass spellings — wrapper verbs, newline segmentation,
nested shell strings, program text, long-form output flags, process substitution. Every
round was fixed; every next round found more. The corpus already drew the correct
conclusion in writing: **shell is Turing-complete and no static text analysis of it is
complete**, so the containment answer is a layer down (`skills/sandboxing.md`), never a
better parser.

Two new findings closed the argument.

**1. The cost side was larger than recorded.** A live session reproduced the arm denying
ordinary read-only work: a diagnostic command was refused with *"this command would
modify 'docs/releases/gold/v1.json'"* because the path appeared in text the verb
classifier could not read (inside a `python -c`, inside a loop). The narrow
"provably-read-only verb" grant added in an earlier commit only covered commands the
classifier could positively recognise, so everything else — every build, every test run,
every unlisted verb — still fell through. The friction was not incidental; it was the
common case for a working agent.

**2. A load-bearing diagnosis in the corpus was simply wrong.** Prior commits, code
comments and `FEATURES.md` all asserted that *registering* a `PreToolUse` hook removes a
tool from the harness's own auto-approve path — that "silence is not approval". Checked
against the runtime's documentation, that is false: a hook exiting 0 with empty stdout is
ignored and the normal permission flow applies unchanged. The prompts attributed to hook
registration were, in substantial part, the guard genuinely objecting — i.e. finding 1.
The same check established the real precedence, which matters more than the wrong claim
did: `permissions.deny` and `permissions.ask` outrank any hook decision, so a hook
`allow` can never grant more than the operator already allows themselves.

Presented with the choice, the owner selected removal in two steps: first drop the Bash
arm and keep Write/Edit; then, once the matcher mechanism was confirmed documented and
clean, remove `Bash` from the matcher entirely rather than keep an always-allow hook.

## Decision

**`Bash` is removed from the `PreToolUse` matcher** in `.claude/settings.json` and
`plugin/hooks/hooks.json` (now `Write|Edit|MultiEdit|NotebookEdit`). The guard does not
run on shell commands at all: no inspection, no Doctrine-sourced prompt, no per-command
process spawn.

**The shell path-analysis code is deleted, not disabled** — 370 lines removed against
48 added (`git diff --numstat`), taking `tools/doctrine_guard.py` from 1107 to 785 lines,
across 22 symbols:
`check_protected_in_command`, `command_targets`, `command_is_read_only`,
`command_has_write_redirect`, `redirect_paths`, `strip_shell_noise`, `segment_verb`,
`_carries_flag`, `solobuilder_profile`, and the constants they served (`READ_ONLY_VERBS`,
`PREFIX_VERBS`, `NESTED_SHELLS`, `PROGRAM_TEXT_WRITERS`, `PATHISH`, `REDIRECT_TARGET`,
`SEGMENT_SPLIT`, `HEREDOC`, `SOLOBUILDER_MARKERS`). Dead code that looks like security is
worse than an honest gap: a reader would believe path protection still ran.

Both earlier partial holds go with it — the narrow read-only grant and the
`Delivery profile: solobuilder` blanket grant. They were reasonable shapes for a control
worth keeping; the control was not worth keeping, so the distinction they drew is gone.

**Write/Edit is untouched in code**: secrets (§7 #2), protected paths and immutable
evidence, the control surface, and test-weakening (§7 #4) all still decide, verified by
execution. **Its guarantee, however, is now conditional** — see the second-order
consequence under Consequences, which the first draft of this ADR did not name.

**The command branch in `evaluate()` is retained** for a repo that deliberately re-adds
`Bash` to its matcher. It runs `check_secrets`, `check_control_commands`,
`check_irreversible` (§5) and `check_test_weakening_command`, then approves. These are
literal-pattern rules that fire almost never and cost no measurable friction. Nothing
analyses command paths any more, on any profile.

## Alternatives considered

| Option | Pros | Cons | Why not |
|---|---|---|---|
| A (chosen): remove `Bash` from the matcher; delete the path-analysis code | zero friction and zero latency on shell; the corpus's own stated conclusion finally acted on; no dead security-shaped code | Doctrine's hold on shell becomes prose only — no mechanical §5 or secret check on a command | accepted knowingly: the mechanism it replaces was incomplete by construction, and `permissions.deny`/`ask` plus an isolation tier are the controls that actually hold |
| B: keep the hook on `Bash` but always return `allow` after the rare-firing checks | keeps a real §5/secret check on commands at near-zero friction | still spawns a process per Bash call; keeps a partial control whose completeness cannot be argued | offered and rejected by the owner once the matcher mechanism was confirmed documented and safe |
| C: keep the arm, fix only the false positives | smallest change; retains every existing protection | the false positives are a symptom of the undecidability, not a bug list — round five would find round six | rejected: "fix the class, not the instance" (charter), and the class here is unfixable by parsing |
| D: strengthen the parser | in principle closes known bypasses | four rounds of evidence say the next round finds more | rejected on the corpus's own long-standing reasoning |

## Consequences

- **Positive:** shell work in a Doctrine repo is exactly as fast and as quiet as in an
  ungoverned one. The corpus stops claiming a protection it could not deliver, which is
  what §7 #1 demands of it. 263 lines and their tests leave the maintenance surface.
- **Negative / accepted, stated plainly:** nothing mechanical now stops `git push
  --force`, a publish, a `rm -rf` of gold records, or a credential echoed into a command,
  in the default wiring. Evidence integrity for gold records rests entirely on
  `doctrine_gold gate` in CI (tamper-evident, not tamper-proof — and blind to a record
  forged and committed in one step). §5 on shell is now honour-system for the agent plus
  whatever the operator puts in `permissions.deny`/`ask`.
- **Negative, SECOND-ORDER, and not foreseen when this ADR was first written — added
  after a G5 audit demonstrated it end to end.** The Write/Edit arm is self-disabling
  through the newly-unchecked channel. `.doctrine-state/guard.json` is protected against
  a *Write* (`ask`) but no longer against a shell command, and a policy of
  `{"allow": ["tools/*", ".claude/*"]}` is not blanket, so `is_blanket()` correctly does
  not refuse it — while `allow` exempts those paths from the path **and** secret rules.
  Executed chain: shell-write the policy (`allow`, was `ask`) → Write
  `tools/doctrine_guard.py` (`allow`) → Write `.claude/settings.json` (`allow`) → Write
  an AWS key into `tools/x.py` (`allow`). No prompt at any step. So "Write/Edit remains
  enforced" is true of the code and conditional as a guarantee: it holds until one
  unchecked command rewrites the guard's policy, wiring, or source. **Doctrine cannot
  close this from inside a repo the agent can write to** — the same principle already
  recorded as "nothing inside a repository the agent can write is tamper-proof against
  that agent", now reaching the guard's own policy file.

  **The mitigation is weaker than it first appears, and this ADR states that rather than
  bank the reassurance.** Permission rules are matched per tool: `Bash(...)` patterns
  match command TEXT, not paths, so no rule expresses "any command that writes this
  path". `Read(...)`/`Edit(...)` deny rules do reach the file tools and a *recognised*
  subset of file commands in Bash (`cat`, `head`, `tail`, `sed`) — real, partial, and now
  shipped as `permissions.ask` entries in `.claude/settings.json` — but they are silent
  on `echo x > path` and on any subprocess that opens the file itself. The same
  undecidability that retired the guard's arm applies to the permission layer; it does
  not escape it. The only complete control is the isolation tier
  (`skills/sandboxing.md`), where `filesystem.denyWrite` (which `Edit(...)` deny rules
  merge into) is enforced by the kernel — **and sandboxing is unsupported on native
  Windows**, this project's own primary platform. So on Windows the honest statement is
  that the chain is open and closing it means running under WSL2 or a container, not
  writing a config entry. Recorded in `05-packaging.md`, `FEATURES.md` and the guard's
  own module docstring rather than left for someone to rediscover.
- **Competitive note, recorded because it was weighed:** point-of-action enforcement was
  identified in this repo's own teardown work as Doctrine's most defensible advantage over
  comparable frameworks. That advantage now rests on the Write/Edit arm alone — which is
  the sound half, and the half that guards the irreversible mistake (a committed secret).
- **Invalidation triggers:** a runtime appears that offers *structured* shell intent
  (parsed argv and resolved paths, not raw text) — that would be data, not a language, and
  would justify a new, sound command arm; or an operator needs mechanical shell control and
  should reach for `permissions.deny`/`ask` and `skills/sandboxing.md` first, not a revived
  parser.

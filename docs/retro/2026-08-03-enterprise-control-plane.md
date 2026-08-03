# Retro — Enterprise Control Plane (v0.7.0)
<!-- G7 artifact. Author: Project Reviewer. -->

**Task:** close the four gaps an audit found between "well-specified doctrine"
and "enterprise development operating layer", plus the bridge flake it
surfaced. Class L. Brief: `docs/briefs/enterprise-control-plane.md`.

## What actually happened

The plan had five work packages. All five shipped. The interesting part is
what the work taught, not that it landed.

### The first hypothesis was wrong, and proving it wrong was the fastest step

The bridge flake looked like the classic Windows pattern: respond, close, and
the unread request body triggers RST. A probe with a slow-reading client
returned 20/20 clean — the hypothesis was refuted in two minutes. The real
mechanism was the *timing of the body*, not merely its presence: a client that
sends headers and body in separate segments loses the race when the server
answers and closes between them. Reproducing that (headers, pause, late body)
failed 10/10 before the fix and passed 10/10 after.

**Keep:** `skills/debugging.md`'s "test the hypothesis you want to be wrong".
The cheap refutation saved a fix aimed at the wrong mechanism.

### Dogfooding found two defects no test would have

The guard was wired into this repo's own `.claude/settings.json` while it was
being built, so it judged its author's edits. It denied two of them:

1. Writing its own test file — the secret pattern let one quote character open
   and a different one close, matching across unrelated text.
2. Writing the G4 review — prose *about* credential handling matched the
   credential pattern.

Both are false denials, and false denials are how an enforcement gate dies:
people switch it off. Neither would have surfaced from tests written by the
same mind that wrote the patterns; both surfaced within minutes of the tool
being made to live under its own rule.

**Keep:** wire an enforcement tool into the repo that builds it, on day one.
**Doctrine candidate:** `skills/tooling.md` should say plainly that a policy
tool is not done until it has judged its own author for a full session.

### The gate correctly refused a "convenient" fixture

Adding a test fixture that looked like a real credential was denied. The
tempting move was to widen `.doctrine-state/guard.json` to allowlist `tests/*`
— which would have blinded the guard across the whole test tree to make one
test convenient. The file's existing convention (assemble fixtures from
fragments) solved it with no policy change.

**Keep:** when a gate blocks you, the first question is whether the gate is
right. Here it was. Widening policy to pass your own test is how the escape
hatch becomes the norm.

### Honest evidence is slower than it looks

Two full-suite runs had to be discarded because files were edited while the
suite read them from disk — a "failure" that was an artifact of the
measurement, not the code. Reporting either as evidence would have been
fabrication in one direction (a false red) and sloppiness in the other.

**Keep:** freeze the tree during the run that produces the evidence you cite.

## What we could not do, and said so

- **G4 independence.** The doctrine wants a fresh-context reviewer; this
  session could not dispatch subagents, so G4 was an author's self-review,
  disclosed at the top of the review artifact rather than implied to be a
  panel.
- **A real signed tag.** No signing key is configured here, so signature
  *parsing* is tested against git's documented output shapes, and the
  end-to-end signed path is untested. The parser fails closed, so the untested
  direction can only under-report a signature, never invent one.
- **The tag itself.** Version carriers are at 0.7.0 and the CHANGELOG section
  is written, but cutting the annotated tag is §5 — the human's call.

## Doctrine changes proposed

1. `skills/tooling.md`: a policy/enforcement tool is not done until it has
   governed its own authoring session (above).
2. `skills/testing.md`: "freeze the tree during the evidence run" belongs
   beside the existing determinism rules — a suite that reads source from disk
   is non-deterministic under concurrent edits.
3. `standards/dos-and-donts.md`: record that four non-negotiables are now
   mechanically enforceable and six are not, so the doctrine never drifts into
   claiming enforcement it does not have.

## Metrics

- 5 work packages, ~1,200 new lines of tool and test code, 56 new tests.
- 7 defects found and fixed during the pass; 2 of them by dogfooding, 0 by CI.
- 5 accepted limitations, each documented where a reader will meet it.

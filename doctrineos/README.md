# DoctrineOS

A single static binary that governs how an AI coding agent works in a
repository, and proves afterwards what it did.

> **Status: early. A partial, heavily verified port.**
> The state plane and the guard are ported and held byte-identical to the
> Python reference by six differential oracles. Everything else in
> [the Doctrine](https://github.com/maheshvaikri-code/doctrine) is not here
> yet. See [What is and is not ported](#what-is-and-is-not-ported).

## Why a binary

The agent is the user. That changes the requirements:

- **No runtime to install.** A Node shop, a Rust shop, or a scratch container
  should not need Python present to run gates that have nothing to do with
  their stack. For a human that is a tax; for an autonomous agent it is a wall,
  and the wall is where autonomy ends.
- **Every command is non-interactive and parseable.** An agent cannot answer a
  prompt and cannot "just look" at an error.
- **Failure is loud, never a silent degrade.** An agent that half-loads a
  corpus will confidently apply half a law.

## Commands

```
doctrineos init [--target dir] [--prune]  make a repo governed (idempotent)
doctrineos check                decide a PreToolUse payload (stdin JSON -> stdout JSON)
doctrineos context [flags]      resolve which resources this task activates
doctrineos gate --done          Definition-of-Done gate (Stop event)
doctrineos checkpoint --proposal f  write a checkpoint (propose/dispose)
doctrineos hydrate [--check]    build the context bundle for the next session
doctrineos verify               walk the state chain (tamper-evident, not tamper-proof)
doctrineos canon [--hash]       canonical bytes of stdin JSON (chain encoding)
doctrineos gold-chain           order the gold ladder, or refuse a broken one
doctrineos gold-pin <path>      pin a file to its content hash (empty = not a sign-off)
doctrineos status               what is pinned, installed, and materialised
```

## The three mechanisms

**Activation.** `context` computes which resources a task needs instead of
asking the model to consult a table. The kernel ships **29 resources** — skills,
standards and lenses — each declaring what fires it and what that costs. A weak
signal (a keyword in the task) may hand you a document; only a deterministic
one may make you adopt a lens. See [`kernel/README.md`](kernel/README.md).

**Memory.** An agent resets to zero every session, so continuity lives outside
it: hash-chained checkpoints, a distillate of what was learned and what failed,
and a deterministic bundle the next session reads. `checkpoint` writes it,
`hydrate` reads it back.

**Evidence.** `verify` walks the chain. It is **tamper-evident, not
tamper-proof**: it catches a record edited after it was committed, and cannot
catch one forged and committed in a single step — no prior state exists to diff
against. A release-bound merge still needs a human reading the diff.

**Refusal.** `check` answers a `PreToolUse` payload: secrets and writes to
immutable evidence are denied before the tool runs. Scope is exact — the guard
is wired to file writes only. **Its hold on your shell is prose, not
mechanism**; containment there is a sandbox's job, a layer down.

## What is and is not ported

| Ported, oracle-verified | Not ported |
| --- | --- |
| state chain: `checkpoint`, `verify`, `hydrate` | `doctrine_install`, fleet, metrics, lint, dashboard |
| canonical bytes (the chain encoding) | gold `record`/`check` (git + GPG surfaces) |
| gold ladder topology + content pinning | `FEATURES.md` toggles (Python-only today) |
| the `PreToolUse` guard decision | |
| the activation engine (`context`) | roles, domain overlays, templates |
| a 29-resource kernel (skills, standards, lenses) | the other 167 corpus files |

Known divergences are recorded in
[`docs/05-PORT-VERIFICATION.md`](docs/05-PORT-VERIFICATION.md) rather than left
to be rediscovered.

## Verification

A verifier is judged by what it **refuses**, which makes it uniquely easy to
port badly: a port that refuses *less* than its reference still prints
`verify OK` and looks healthy. So the Go implementation is held to the Python
one by running both across the same inputs and diffing:

```text
guard decisions           24/24  agree
canonical bytes           15/15  byte-identical
chain findings            13/13  verdicts AND finding text
gold topology             11/11  + content pinning 5/5
hydration bundles          7/7   BYTE-identical, incl. a real 31-checkpoint plane
interop (write path)      11/11  incl. chains written alternately by Go and Python
Go suite                  35/35
```

Two rules make those numbers mean something, and both were learned the hard
way — the write-up in
[`docs/05-PORT-VERIFICATION.md`](docs/05-PORT-VERIFICATION.md) lists every bug
they caught, including the ones in the harness itself:

1. **Compare findings, not verdicts.** Two implementations can refuse the same
   record while describing it differently, and a wrong explanation sends a
   reader after a defect that is not there.
2. **A mutation must be able to pass.** Cases are run against a control binary
   built with the rule under test removed. A case that fails either way is not
   a test.

Running them needs a [doctrine](https://github.com/maheshvaikri-code/doctrine)
checkout as the reference:

```
cd oracles && DOCTRINE_REF=/path/to/doctrine python hydrate_diff.py
```

## Build

```
go build -o dos .        # no dependencies outside the standard library
go test ./...
```

## Relationship to Doctrine

[Doctrine](https://github.com/maheshvaikri-code/doctrine) is the corpus and the
law — roles, skills, standards, gates — and is the reference implementation
this is verified against. DoctrineOS is the execution layer being rebuilt as a
binary. Doctrine is not going away and nothing here replaces it.

## License

See [LICENSE](LICENSE).

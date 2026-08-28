# Differential oracles

Hold the Go implementation to the Python one by running **both** across the
same inputs and diffing the results. Rationale and findings:
[`../docs/05-PORT-VERIFICATION.md`](../docs/05-PORT-VERIFICATION.md).

```
python differential.py    # guard decisions on 24 tool payloads
python canon_diff.py      # canonical bytes, byte-for-byte, 15 shapes
python tamper_diff.py     # chain findings on 13 mutations of a real chain
python gold_diff.py       # gold ladder topology + content pinning
python interop_diff.py    # chains WRITTEN by one, verified by the other
```

They need `dos` (or `dos.exe`) built first:

```
cd .. && go build -o dos .
```

Paths are derived from each file's own location, so they run from anywhere.

## The control binary

`tamper_diff.py` also looks for `../preschema` — the identical source with
**only** the schema call excised. It is optional, and it is the most important
part of the harness.

Without it, "the schema-only cases fail" proves nothing: a case that fails no
matter what is not a test. With it, those cases must come back **OK** from the
pre-schema binary and **FAIL** from the current one. The first run of this
control immediately rejected one of my own cases as mislabelled.

Rebuild it with:

```
python build_control.py
```

That used to be a list of manual steps here, which is how a control quietly
stops matching the code it is a control for. The script asserts both excisions
rather than attempting them: if either stops matching after a refactor, it
fails loudly instead of producing a binary identical to the real one — which
would make every schema-only case "pass" for the wrong reason and look like
success. Rebuild it whenever `verify.go` changes.

The binary is gitignored; it is a diagnostic, not a deliverable.

## Readers and writers need different oracles

The first four compare what each implementation SAYS. `interop_diff.py` does
not: it compares what each implementation ACCEPTS. Two writers can describe a
checkpoint identically and still emit bytes the other refuses, and for a writer
that matters more — a bad reader returns one wrong verdict, a bad writer
corrupts the evidence every later reader depends on.

Its load-bearing case is `interleaved g/p/g/p`: checkpoints written alternately
by Go and Python, with both verifiers accepting the result. Each link hashes
its predecessor's exact bytes, so a single byte of encoder drift breaks every
link after it — indistinguishably from tampering.

## Reading the output

`tamper_diff.py` reports two numbers, and the second is the strict one:

```
verdicts agree 13/13   findings text identical 13/13
```

Verdict agreement is weak — two functions that always return FAIL would score
perfectly. Finding **text** is what catches a port that reaches the right
answer for the wrong reason, which is how the `seq 0 != expected 30` bug was
found while verdicts read 12/12.

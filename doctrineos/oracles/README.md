# Differential oracles

Hold the Go implementation to the Python one by running **both** across the
same inputs and diffing the results. Rationale and findings:
[`../docs/05-PORT-VERIFICATION.md`](../docs/05-PORT-VERIFICATION.md).

```
python differential.py    # guard decisions on 24 tool payloads
python canon_diff.py      # canonical bytes, byte-for-byte, 15 shapes
python tamper_diff.py     # chain findings on 13 mutations of a real chain
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

To rebuild it, copy the sources to a scratch directory, delete the
`validateSchema` call and its `loadSchema` loader from `verify.go`, drop the
test file, and build to `../preschema`. Assert both excisions succeed — if the
call is not found, the control silently becomes a copy of the real binary and
every case "passes" for the wrong reason.

The binary is gitignored; it is a diagnostic, not a deliverable.

## Reading the output

`tamper_diff.py` reports two numbers, and the second is the strict one:

```
verdicts agree 13/13   findings text identical 13/13
```

Verdict agreement is weak — two functions that always return FAIL would score
perfectly. Finding **text** is what catches a port that reaches the right
answer for the wrong reason, which is how the `seq 0 != expected 30` bug was
found while verdicts read 12/12.

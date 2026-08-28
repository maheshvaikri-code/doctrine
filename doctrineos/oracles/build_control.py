"""Build the pre-schema CONTROL binary used by tamper_diff.py.

The control is what makes the schema-only cases meaningful: they must come back
OK from a binary built WITHOUT the schema rule, and FAIL from the real one. A
case that fails either way is not a test.

This was a set of manual steps in the README, which is how a control quietly
stops matching the code it is supposed to be a control for. It is a script so
that "rebuild the control" cannot drift from "the current sources minus one
rule".

The excisions are ASSERTED, not attempted. If either string stops matching -
because the code was refactored - the build fails loudly rather than producing
a binary identical to the real one, which would make every schema-only case
"pass" for the wrong reason and look like success.
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import _locate

# Needs neither the reference checkout nor a built binary: it compiles one.
SRC = _locate.MODULE

OUT = _locate.CONTROL

SCHEMA_CALL = '''		if err := validateSchema(data, schema, schema, "$"); err != nil {
			findings = append(findings, fmt.Sprintf("%s: schema: %s", base, err.Error()))
		}
'''
SCHEMA_LOAD = '''	schema, schemaErr := loadSchema(pl.root, "checkpoint")
	if schemaErr != nil {
		return nil, schemaErr
	}
'''


def main():
    work = Path(tempfile.mkdtemp())
    try:
        pkg = work / "pkg"
        shutil.copytree(SRC, pkg, ignore=shutil.ignore_patterns(
            "*.exe", "preschema", "dos", "oracles", "docs"))
        verify = pkg / "verify.go"
        text = verify.read_text("utf-8")

        for label, chunk in (("schema call", SCHEMA_CALL), ("schema loader", SCHEMA_LOAD)):
            if chunk not in text:
                print(f"error: {label} not found in verify.go - the control would be "
                      f"a COPY of the real binary and every schema-only case would "
                      f"pass for the wrong reason", file=sys.stderr)
                return 1
            text = text.replace(chunk, "", 1)
        verify.write_text(text, "utf-8", newline="\n")

        for t in pkg.glob("*_test.go"):
            t.unlink()  # the control only needs to run, not to be tested

        r = subprocess.run(["go", "build", "-o", str(OUT), "."], cwd=pkg,
                           capture_output=True, text=True)
        if r.returncode != 0:
            print("error: control build failed:\n" + r.stdout + r.stderr, file=sys.stderr)
            return 1
        print(f"control built: {OUT.name} (current sources, schema rule excised)")
        return 0
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())

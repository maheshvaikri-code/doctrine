# Brief — Repository Audit Remediation
<!-- G0 artifact. Task class: L (cross-cutting verification/release integrity). -->

## Problem

The repository audit found seven gaps across source detection, fail-closed
verification, non-Claude activation, release identity, supported-Python CI
coverage, subprocess cleanup, and README accuracy.

## Scope

1. Parse PEP 621 project identity instead of searching raw TOML text.
2. Fail source verification when its required Ruff gate cannot execute.
3. Install the universal root `AGENTS.md` boot and make it activation-critical.
4. Restore an honest local release identity for the existing v0.6.46 commit
   without pushing or fabricating historical release mappings.
5. Test Python 3.11 and 3.12 in CI with a pinned Ruff version.
6. Close every pipe created by the MCP protocol integration test.
7. Synchronize the README test count with discovery.

## Non-goals

- Publishing or pushing tags.
- Reconstructing tags for versions whose exact shipped commits are not proven.
- Changing Doctrine's public API or adding dependencies.

## Acceptance criteria

- Comments, unrelated TOML tables, and formatting differences cannot
  misclassify source versus consumer repositories.
- A source verification run with Ruff unavailable returns nonzero.
- `doctrine_awaken` reports the source checkout fully awake and treats a missing
  `AGENTS.md` as a critical gap.
- Local annotated tag `v0.6.46` resolves to the existing v0.6.46 release commit;
  no remote refs are changed.
- CI contains Windows/Linux × Python 3.11/3.12 and a pinned Ruff install.
- The MCP protocol test passes with `ResourceWarning` promoted to an error.
- README's test count equals `unittest` discovery.
- Full Doctrine verification passes and the working-tree diff is reviewed.

## Constraints

Python 3.11+, stdlib-first, Windows and POSIX, no external publication.

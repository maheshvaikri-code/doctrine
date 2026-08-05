# Retrospective - WorkHawk application extraction - 2026-07-25

## Facts

Shipped to `main`: WorkHawk as a separate source application under
`workhawk/`, internal identity `openhawk.workbench`, a typed module registry,
the live Doctrine v1 adapter, truthful unavailable states for MAPLE/STIX/Trust,
renamed cross-platform CI, seven hosted browser scenarios, and updated
architecture/operating documentation.

Implementation commits: `8a0d63a`, `43d1a30`, and `4ada7e2`. Gates G0 through
G7 were walked. No site, package, tag, or external release was created.

Defects caught after the initial extraction: an ignored Sites build plug-in, a
short-viewport sidebar overflow risk, incomplete per-module browser assertions,
a locally occupied E2E port, and one ambiguous hosted brand locator.

## What worked

- Moving rather than copying the frontend left one source of truth and made the
  new ownership boundary visible in Git.
- The registry made future integrations explicit without inventing their
  availability, metrics, or actions.
- Contract tests covered repository topology and packaging, catching a file
  that the local build could see but a clean checkout would lose.
- Hosted OS and browser gates validated the exact pushed commit after local
  browser tooling proved unavailable.
- Keeping the bridge API stable avoided widening Doctrine's trusted execution
  boundary during a frontend ownership change.

## What failed or hurt

- The repository's broad `build/` ignore pattern silently matched a required
  application source file after the directory move.
- The first local E2E attempt waited on a port already owned by another process.
- The local interactive browser connector had no browser backend, while the
  local Playwright cache had no Chromium executable.
- The first hosted browser rerun exposed a strict-mode locator ambiguity caused
  by the new brand correctly appearing in several places.
- A user-created WorkHawk logo arrived during verification. The original raster
  was preserved byte-for-byte and integrated only after source, render,
  production HTTP, and browser checks were added.

## Root causes

### Required moved source was ignored

The file lived under `build/` -> the root ignore rule matched directory names
at any depth -> the local file remained on disk -> local compilation therefore
passed -> staged review initially relied on status rather than fresh-checkout
presence. Root cause: repository-topology verification gap. The fix combines an
explicit tracked rename with a permanent access assertion.

### First hosted browser run failed

The brand was added in the shell -> the fixture activity and footer also
contained WorkHawk -> `getByText` used substring matching -> Playwright strict
mode found three valid nodes -> the source contract could not model locator
uniqueness. Root cause: browser assertion precision gap. The fix uses exact
user-visible brand text and was re-run in hosted Chromium.

### Local browser evidence was unavailable

The default port was occupied -> the first web server could not bind -> a port
override enabled a second attempt -> the Playwright package had no installed
browser executable -> the application browser service exposed zero backends.
Root cause: local environment/tooling availability, not product behavior.
Hosted CI already installed fresh Chromium and supplied authoritative evidence.

## Doctrine and tooling amendments

| # | Amendment | Target | Class-S change filed? |
|---|---|---|---|
| 1 | Assert the existence of ignored-name source files after application moves. | WorkHawk source/CI contract test | no; implemented |
| 2 | Keep a validated E2E port override for deterministic local/browser execution. | `workhawk/playwright.config.mjs` | no; implemented |
| 3 | Assert future module status by module name, never by one repeated status label. | hosted browser suite | no; implemented |
| 4 | Treat exact hosted browser reruns as required evidence after any locator failure. | QA report and CI practice | no doctrine-law change |

## Honest negative findings worth remembering

- MAPLE, STIX, and Trust are registry seams, not integrations. Doctrine is the
  only live WorkHawk module in this repository.
- WorkHawk currently has no editor, PTY terminal, capability broker, identity
  service, multi-repository backend, or public deployment.
- Automated Axe and keyboard coverage is strong evidence, but it is not manual
  screen-reader or enterprise accessibility certification.
- The original WorkHawk logo is tracked in `4ada7e2`; the unused derived
  `public/brand/workhawk-mark.png` remains untracked and outside the product.

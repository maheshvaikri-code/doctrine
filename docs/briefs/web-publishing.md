# Brief — Web publishing (GitHub Pages / website / wiki)

<!-- G0 artifact. Author: Product Owner. -->

**Problem.** Doctrine has no coverage for publishing a repo to a web surface — GitHub
Pages, a project website, or the GitHub wiki (grep: 0 hits). The concerns exist
piecemeal (`cicd` = Actions, `tech-writer` = content, `ui`/`frontend` = the site) but
nothing ties them into governed *publishing*, and there is no support for the user's
requirement: **auto-publish on commit/push, opt-in.**

**Goal.** One skill governing web publishing to the three surfaces, including opt-in
auto-publish-on-push, with the discipline that makes auto-publish safe.

**Scope.** `skills/web-publishing.md` (Pages + website + wiki + the opt-in auto-publish
workflow + governance) + routing row + Tech Writer Loads. **Out of scope (future):** an
installer `--pages` flag that seeds the workflow; per-generator tutorials.

**The load-bearing decision.** Auto-publish to a public surface is auto-*expose* on
every push, so: (1) **opt-in is a §5 decision made once** and recorded
(`Web publish:` in the brief), never default-on; (2) publish a **designated source
only** — never secrets/drafts/whole-repo; (3) the workflow **fails closed** (build +
link-check + secret-scan before deploy).

**Acceptance criteria.**
- [ ] Skill covers Pages, project website, and wiki, each with its specifics.
- [ ] The opt-in auto-publish-on-push mechanism is given (a hardened, SHA-pinned Actions workflow) and is off by default.
- [ ] Governance encoded: opt-in = §5, designated-source-only, no secrets/drafts, fail-closed, one-way wiki sync.
- [ ] Wired into the §6 routing table + Tech Writer Loads; skill count updated.
- [ ] `doctrine_lint` + full `doctrine_verify` green.

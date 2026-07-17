# Brief — Web Design discipline (recruit a designer)

<!-- G0 artifact. Author: Product Owner. -->

**Problem.** Doctrine can *publish* a site (`web-publishing`) but has **no one who
makes it look designed.** It has UX Designer (flows) and Frontend Engineer
(implementation) and `ui`, but zero visual/web/brand coverage — so generated
sites look dev-built, not corporate. Grep for web/brand/visual design: ~0 hits.

**Goal.** Recruit a **design discipline** so any repo's public site is
corporate-quality — by adapting proven open-source templates and mapping the
repo's own content, license-clean and self-contained.

**Scope.** `roles/web-designer.md` + `skills/web-design.md` (structure, principles,
content-mapping, a template catalog, licensing) + routing/role-index wiring. Prove
it by upgrading the Doctrine site generator (`scripts/build_site.py`) to a
corporate-quality template.

**The honest constraint (recorded).** "Borrow templates from open-source repos" is
the right strategy, but external template repos can't be cloned from the sandbox.
So: the **skill carries a vetted catalog** (name → license) a designer fetches
per project; and a **strong self-contained default** ships in the generator now.
Design quality comes from *a proven template + content-mapping*, not from an agent
inventing visuals — and every borrowed asset is license-checked + attributed.

**Acceptance criteria.**
- [ ] Web Designer role + web-design skill exist, wired into routing + role index.
- [ ] Skill encodes: borrow-a-proven-template, license-clean, content-mapping (real
      content not lorem), self-contained, accessible; + a template catalog.
- [ ] The Doctrine site generator upgraded to a corporate-quality template (hero,
      features, docs, light+dark, responsive), proving the discipline on the repo.
- [ ] `doctrine_lint` + full `doctrine_verify` green; ruff clean.

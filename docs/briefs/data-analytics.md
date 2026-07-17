# Brief — Data Analytics discipline (+ round out Data Engineering)

<!-- G0 artifact. Author: Product Owner. -->

**Problem.** The catalog has **Data Engineering** (Data Engineer role +
`data-engineering` skill + Head of Data governance) but **no Data Analytics** — no
analyst role, no analytics skill. They are different disciplines: engineering
*moves and stores* data; analytics *derives decisions from* it (analysis, BI,
experiments, metric definitions). And Data Engineering has role + skill but **no
template** (no data artifact), so neither discipline is "Roles + Skills + Playbooks
+ Templates" complete.

**Goal.** Add the Data Analytics discipline fresh; give Data Engineering the
template it lacks. No duplication of the existing DE role/skill.

**Scope.**
- Data Analytics: `roles/data-analyst.md` + `skills/data-analytics.md` +
  `templates/analysis-report.md`.
- Data Engineering round-out: `templates/data-contract.md`.
- Routing row + role index (Data Analyst) + counts + version bump.

**Load-bearing discipline (in the skill).** Decision-first (no dashboard without a
decision); one-metric-one-definition; honest statistics (uncertainty, confounders,
no correlation-as-causation); reproducible query; **p-hacking = a §1 honesty
violation**; PII aggregated per `privacy-compliance`.

**Acceptance criteria.**
- [ ] Data Analyst role + data-analytics skill exist, wired into routing + role index.
- [ ] analysis-report + data-contract templates exist with gate-tag comments.
- [ ] Skill encodes decision-first, metric-definition, honest-stats, experimentation, PII.
- [ ] Counts updated (33 roles / 49 skills); `doctrine_lint` + full `doctrine_verify` green.

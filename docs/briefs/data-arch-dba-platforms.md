<!-- G0 brief — Class L catalog expansion -->
# Brief: Data Architect + DBA roles, platform integrations, more languages (v0.6.25)

## Context
The catalog covered data *engineering* and *analytics* but had gaps the human
named: no dedicated **Data Architect** (data modeling + storage topology) and
no **Database Administrator** (DB operations, distinct from schema *design*).
"Spaces" was clarified to mean **external enterprise platforms** (Hugging Face,
Snowflake, ServiceNow, Salesforce, Jira). Language coverage stopped at six
profiles; observability had the discipline but no **stack** catalog.

## Scope (in)
- **Roles (2):** Data Architect, Database Administrator (DBA) — each with a
  sharp boundary against existing roles (Chief Architect, Head of Data,
  Database Engineer, Data Engineer, SRE) so they are additive, not redundant.
- **Skills (3):** `data-architecture` (modeling), `database-operations`
  (backup/HA-DR/tuning/access), `platform-integrations` ("Spaces").
- **Language profiles (4):** C/C++, Ruby, PHP, Swift (6 -> 10).
- **Observability stacks:** OTel + Prometheus/Grafana + ELK/Loki + Jaeger/Tempo
  + Datadog + Sentry catalog added to `skills/observability.md`.

## Scope (out — mapped to existing, not rebuilt)
- Infrastructures -> `iac` + `cloud-*`; Platforms -> `platform-engineering` +
  `cloud-*`; Technology Stacks -> `templates/compatibility-manifest.md`.

## Acceptance criteria
- [ ] 2 roles + 3 skills + 4 language profiles + observability stacks section.
- [ ] Each new role states what it does NOT own (separation of duties).
- [ ] platform-integrations enforces §5 on outbound writes + secrets-in-manager.
- [ ] Routing table + role index wired; counts -> 35 roles / 52 skills.
- [ ] Version 0.6.25 across all 6 carriers; CHANGELOG entry.
- [ ] `doctrine_verify` green (lint + ruff + tests + state).

## Non-goals / guards
- No new runtime dependency; corpus-only. §12: `.Doctrine/` edits are the
  human's to approve (this brief records intent).

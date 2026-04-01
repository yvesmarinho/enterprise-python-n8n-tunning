<!--
┌─────────────────────────────────────────────────────────────────────────┐
│  SYNC IMPACT REPORT — v2.0.0 → v2.1.0                                  │
│  Version change : MINOR — new infrastructure server (wfdb02) added      │
│                  and Principle III expanded with wfdb02 pg_dump target  │
│  Modified principles:                                                   │
│    III. "Infrastructure Safety First" — added explicit rule that        │
│         pg_dump for F17 MUST target wfdb02 (dedicated DB server),      │
│         not wf001 (application server)                                │
│  Added sections:                                                        │
│    Infrastructure table: wfdb02.vya.digital (82.197.64.145) row —      │
│    PostgreSQL 16 (6432) + Pgbouncer (5432) + MySQL 8.4 (3306) +       │
│    Node Exporter                                                       │
│  Removed sections: none                                                 │
│  Infrastructure intro: "two Debian 12 servers" → "three Debian 12      │
│  servers"; table column "N8N Path" → "Docker Path"                     │
│  Templates:                                                              │
│    plan-template.md     ✅ updated — gate III wfdb02 precision added    │
│    spec-template.md     ✅ compatible (no conflicts)                    │
│    tasks-template.md    ✅ compatible (no conflicts)                    │
│  Downstream artefacts updated (same session):                           │
│    specs/001-p1-tunning-instrumentacao/spec.md    ✅                    │
│    specs/001-p1-tunning-instrumentacao/plan.md    ✅                    │
│    specs/001-p1-tunning-instrumentacao/data-model.md ✅                │
│    specs/001-p1-tunning-instrumentacao/tasks.md   ✅ (T006b, T012,     │
│                                        T022, T030, T031 updated)     │
│    specs/001-p1-tunning-instrumentacao/contracts/  ✅                  │
│    docs/mcp-questions.yaml                        ✅                  │
│  Follow-up TODOs: none — no deferred placeholders                      │
└─────────────────────────────────────────────────────────────────────────┘
-->
<!-- Gerado por scaffold.py 2026-03-05 | Domínio: infrastructure | Linguagem: python -->

# Enterprise Python N8n Tunning Constitution

## Core Principles

### I. Specification-Driven Development (SDD)

`docs/objetivo.yaml` is the **single source of truth** for the entire project.
Every feature (F01–F25), profile (7 roles), and task MUST trace back to a
declared entry in that file. `docs/mcp-questions.yaml` is the technical mirror
and MUST remain in sync with `objetivo.yaml` — any divergence is a blocking
defect. No ad-hoc changes to architecture, features, or profiles are permitted
without first updating `objetivo.yaml`.

**Non-negotiable rules**:
- All Copilot sessions MUST begin by consulting `objetivo.yaml` as context.
- `mcp-questions.yaml` MUST be regenerated (or patched) whenever
  `objetivo.yaml` changes.
- Artefacts (agents, prompts, plans, tasks) MUST reference specific feature IDs
  (e.g., F16, F17, F22).

### II. Performance-Tuning Scope (NON-NEGOTIABLE)

This project **exclusively** covers analysis and performance tuning of resources
used by N8N — instrumentation, PostgreSQL tuning, Prometheus configuration,
workload governance, and complementary observability. **N8N version upgrades
are out of scope** and MUST be handled by a separate project.

The project goal, derived from ANA-001, is to: identify and eliminate resource
bottlenecks (queue saturation, PostgreSQL bloat, dual metric collection,
missing memory/concurrency instrumentation) so that N8N and all other services
sharing the same infrastructure benefit from the performance gain.

**Non-negotiable rules**:
- Any pull request, task, or Copilot output that proposes upgrading the N8N
  container version MUST be rejected with: `OUT-OF-SCOPE: version upgrade
  belongs to enterprise-python-analysis project`.
- Tuning actions are sequenced by ANA-001 priority: P1 (F16, F17, F18) before
  P2 (F19, F20, F21, F23, F24) before P3 (F22, F25).
- Every tuning action MUST be validated first in wfdb01, then promoted to
  wf001 only after the wfdb01 gate passes (see Principle IV).
- The ANA-001 report (`docs/n8n_perf_ANA001_20260101_20260331_*.md`) is the
  **canonical baseline** — all performance claims MUST reference it.

### III. Infrastructure Safety First

Every destructive operation — including DDL (`DROP`, `TRUNCATE`, `ALTER`),
Docker container recreation, execution-entity purge, or volume deletion —
MUST have three prerequisites satisfied before execution:

1. **Validated backup** — `pg_dump` or Docker volume snapshot verified
   (restore test passed in wfdb01).
   - For F17 (PostgreSQL tuning): `pg_dump` MUST be executed directly against
     **wfdb02** (82.197.64.145:6432 or Pgbouncer 5432) — the dedicated database
     server. Running `pg_dump` against wf001 is incorrect; the N8N database
     resides on wfdb02.
2. **Rollback plan** — steps documented in the session artefact.
3. **Maintenance window** — approved by the `project-manager` before any
   action on wf001 (31.220.103.208) or wfdb02 (82.197.64.145).

Traefik labels on running containers are **immutable without explicit user
confirmation**. Any playbook or script that recreates a container MUST
preserve all existing `traefik.*` labels.

### IV. Test-Before-Promote (wfdb01 Gate)

No configuration change, purge operation, or new metric reaches wf001
(production) without a documented gate pass from wfdb01 (test/monitoring).
The gate MUST include:

- Applied configuration verified and stable in wfdb01 for at least one full
  business cycle (13:00–22:00 UTC) — the 121Labs PABX peak window
- All smoke tests returning HTTP 200 (`/healthz`, `/metrics`,
  `/api/v1/workflows`)
- All 🔴 Critical workflows (`121Labs PABX` 429K exec/90d,
  `hub-whatsapp-api-gateway-evolution-api` 84K exec/90d) returning
  `status: success`
- Before/after Prometheus metrics collected and compared vs. ANA-001 baseline
- Gate evidence table documented in `docs/SESSIONS/YYYY-MM-DD/` with
  timestamp, configuration delta, and test-engineer sign-off

Failure of any gate criterion MUST trigger rollback — not a manual override.

### V. Idempotent Automation

All Ansible playbooks and Python automation scripts MUST be **idempotent** —
executing the same playbook/script twice against the same environment MUST
produce no unintended changes on the second run. A task that is not idempotent
is a BLOCKING defect; it MUST be fixed before the artefact is considered done.

**Non-negotiable rules**:
- Ansible: every task MUST have a descriptive `name:`, `tags:` per feature ID,
  and `changed_when:` where appropriate.
- Python: `src/` code follows the Fabric design pattern; no `print()` calls —
  use `logging` stdlib only; docstrings MUST follow reStructuredText format
  with Doctest where applicable.
- `ansible-lint` MUST pass with zero errors before merge.

### VI. Observability & Full Traceability

Every session MUST produce the standard artefact set in
`docs/SESSIONS/YYYY-MM-DD/`:
- `DAILY_ACTIVITIES_YYYY-MM-DD.md` — chronological action log
- `SESSION_REPORT_YYYY-MM-DD.md` — decisions, learnings, next steps

Every tuning action (F16–F25) MUST capture **before** and **after** metrics
from VictoriaMetrics/Prometheus (wfdb01) to quantify impact. The ANA-001 report
(`docs/n8n_perf_ANA001_20260101_20260331_20260331T154646.md`) is the canonical
performance baseline.

**Key instrumentation gaps to close (from ANA-001)**:
- `n8n_queue_depth` not instrumented → F16 closes this
- `n8n_concurrency_*` not instrumented → F24 closes this
- `node_memory_*` for wf001 returning empty → F23 closes this
- Dual metric collection active (Pushgateway + scrape) → F18 closes this
- p95 resolution limited to `le=0.1` bucket → F22 closes this

Session artefacts are **incremental** — existing files (README, INDEX.md,
TODO.md, DAILY_ACTIVITIES, SESSION_REPORT, FINAL_STATUS) MUST be appended to,
never rewritten from scratch.

### VII. Security & Credential Hygiene

Credentials, SSH keys, API tokens, and database passwords are **NEVER**
embedded in versioned artefacts (code, YAML, Markdown, agent/prompt files).

**Non-negotiable rules**:
- SSH configuration: always via `.secrets/ssh.json` (SPA config, git-ignored).
- Database passwords: environment variables or Ansible Vault — never
  in playbooks, scripts, or documentation.
- `mcp.json`: use `${env:VAR_NAME}` syntax — no inline secrets.
- `.secrets/` directory MUST remain in `.gitignore`.
- Any Copilot output that inadvertently includes a credential MUST be
  immediately flagged and the artefact redacted before commit.

---

## Infrastructure & Environment Constraints

This project operates across **three** Debian 12 servers (Docker), all routed
through **Traefik** as reverse proxy:

| Hostname | IP | Role | Docker Path |
|---|---|---|---|
| wf001.vya.digital | 31.220.103.208 | **Production** — N8N + prod-collector-api | `/opt/docker_user/n8n` |
| wfdb01.vya.digital | 86.48.31.149 | **Test + Monitoring** — Prometheus, VictoriaMetrics, Pushgateway | `/opt/docker_user/n8n` |
| wfdb02.vya.digital | 82.197.64.145 | **Database** — PostgreSQL 16 (6432) + Pgbouncer (5432) + MySQL 8.4 (3306) + Node Exporter | `/opt/docker_user` |

**Technology stack**:
- Language: Python 3 (reStructuredText docstrings, Doctest, Fabric pattern)
- Automation: Ansible (idempotent playbooks, Vault for secrets)
- Container runtime: Docker / Docker Compose
- Proxy: Traefik (labels mandatory — never removed without explicit approval)
- Metrics: Prometheus → VictoriaMetrics (wfdb01), scrape target wf001:5001
- Database: PostgreSQL 16 em **wfdb02** (servidor dedicado, porta 6432; Pgbouncer pooler 5432) — N8N backend; `execution_entity` at 429K+ rows (ANA-001)

**Performance baseline (ANA-001, Jan–Mar 2026)**:
- N8N CPU wf001: 1–3% normal, alert threshold > 10%
- Critical workflow p95: < 100 ms (limited to `le=0.1` bucket — real value unknown)
- Probe synthetic latency target (F20): < 200 ms end-to-end
- Peak load: 8.416 exec/hora (121Labs PABX, 2026-03-27) = 2.3 exec/s sustained

**ANA-001 root-cause diagnostics**:
| Hypothesis | ANA-001 Status | Resolving Feature |
|---|---|---|
| N8N queue saturated (primary) | ⚠️ NOT CONFIRMABLE — metric absent | F16 |
| PostgreSQL overloaded by 429K rows | ⚠️ Suspected — needs DBA analysis | F17 |
| Dual Prometheus collection active | ✅ CONFIRMED — both paths live | F18 |
| Webhook response time not measured | ⚠️ NOT INSTRUMENTED | F20 |
| Workers saturated (concurrency) | ⚠️ NOT CONFIRMABLE — metric absent | F24 |
| Memory wf001 not monitored | ✅ CONFIRMED — label misconfigured | F23 |
| Hardware CPU bottleneck | ✅ DISCARDED — CPU 1–3% at peak | — |
| Individual workflow latency | ✅ DISCARDED — 100% under 100ms | — |

**Access**:
- SSH: SPA configuration in `.secrets/ssh.json` (git-ignored, NEVER committed)
- Speckit agent profiles: 7 roles — `system_architect`, `N8N_specialist`,
  `devops_engineer`, `devops_automation`, `project_manager`, `test_engineer`,
  `databases_engineer`

---

## Development Workflow (Speckit Cycle)

The project follows the **Speckit framework** in this mandatory sequence:

```
objetivo.yaml → constitution → clarify → plan → checklist → tasks → analyze → implement
```

1. **`objetivo.yaml`** — Single source of truth; updated first, then mirrored
   to `mcp-questions.yaml`.
2. **`speckit.constitution`** — Governance document; MUST be reviewed at the
   start of any new feature or major change.
3. **`speckit.clarify`** — Up to 5 clarifying questions per feature; answers
   encoded back into `objetivo.yaml` or `spec.md`.
4. **`speckit.plan`** — Implementation plan; Constitution Check gate is
   mandatory before Phase 0 research begins.
5. **`speckit.checklist`** — Custom checklist per feature; generated from
   profile responsibilities and acceptance criteria.
6. **`speckit.tasks`** — Dependency-ordered task list from design artefacts;
   organized by user story.
7. **`speckit.analyze`** — Cross-artefact consistency check post-task
   generation.
8. **`speckit.implement`** — Sequential task execution; each task marked
   in-progress → completed before the next begins.

**Session protocol**:
- Session start: invoke `session-manager` agent; verify `DAILY_ACTIVITIES` and
  `SESSION_REPORT` exist for today.
- Session end: update `TODO.md`, `INDEX.md`; append to `SESSION_REPORT`.
- Git commits: MUST use message-file convention
  (`./scripts/git-commit-with-file.sh /tmp/commit.txt`); `git commit -m` is
  FORBIDDEN.

**File operation rules (P0 — enforced by Copilot)**:
- Create file: `create_file` tool only — never `cat > heredoc` or `echo | tee`
- Edit file: `replace_string_in_file` / `multi_replace_string_in_file` only
- Read/search/list: `read_file`, `grep_search`, `file_search`, `list_dir` only
- Terminal (`run_in_terminal`): only for `git`, `make`, `pytest`, `pip install`,
  `docker`, `systemctl` — never for file operations

---

## Governance

This constitution supersedes all other documented practices in the project. In
case of conflict between this document and any other artefact, this constitution
takes precedence and the conflicting artefact MUST be updated.

**Amendment procedure**:
1. Identify the principle(s) affected and the reason for change.
2. Increment version per semantic rules:
   - **MAJOR** (X.0.0): backward-incompatible principle removal or redefinition
     (e.g., removing the wfdb01 gate requirement).
   - **MINOR** (x.Y.0): new principle or section added, or material expansion
     of existing guidance.
   - **PATCH** (x.y.Z): clarifications, wording fixes, non-semantic refinements.
3. Update `LAST_AMENDED_DATE` to today (ISO 8601: YYYY-MM-DD).
4. Prepend a `SYNC IMPACT REPORT` HTML comment listing changes, templates
   affected, and any deferred TODOs.
5. Propagate changes to dependent templates:
   - `plan-template.md` — update Constitution Check gates if principles changed
   - `spec-template.md` — update mandatory sections if requirements changed
   - `tasks-template.md` — update task categories if principle-driven task
     types changed
   - `copilot-instructions.md` — update agent/prompt tables if profiles changed
6. Create a session artefact entry documenting the amendment rationale.

**Compliance review**: At every Speckit `speckit.plan` Constitution Check gate,
verify that the feature plan complies with Principles I–VII. Non-compliant
plans MUST be blocked until the violation is resolved or a justified exception
is documented with stakeholder approval.

**Runtime guidance**: For GitHub Copilot operational rules, refer to
`.github/copilot-instructions.md`. For domain-specific behaviour, activate the
appropriate agent via the trigger phrase defined in
`.github/prompts/[role].prompt.md`.

**Version**: 2.1.0 | **Ratified**: 2026-04-01 | **Last Amended**: 2026-04-01

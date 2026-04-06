# Implementation Plan: P1 Tunning e Instrumentação N8N (F16 + F17 + F18)

**Branch**: `001-001-tunning-instrumentacao` | **Date**: 2026-04-02 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-001-tunning-instrumentacao/spec.md`

**Note**: This plan covers ANA-001 Phase P1 — three features executed in parallel
on wfdb01 and promoted as a block to wf001.

## Summary

Implementar as três ações de instrumentação e correção crítica da Fase P1 do
ANA-001: (F16) expor métricas de fila do N8N, (F17) ativar purgação da
`execution_entity` e pg_stat_statements, e (F18) eliminar a dupla coleta
Prometheus. As três features são independentes entre si e podem ser desenvolvidas
e testadas em paralelo em wfdb01 antes da promoção em bloco para wf001.

**Technical approach**: Ansible idempotente com Python para verificações e
coleta de evidências. Docker Compose override pattern para variáveis de ambiente.
SSH SPA (fwknop) para acesso seguro. Gate obrigatório em wfdb01 antes de wf001.

## Technical Context

**Language/Version**: Python 3.11 (uv, Fabric pattern, reStructuredText docstrings, Doctest)
**Primary Dependencies**: Ansible 2.15+, ansible-lint, Fabric/Paramiko, psycopg2-binary, prometheus-client
**Storage**: PostgreSQL 16 (wfdb02 — 82.197.64.145:6432; Pgbouncer pooler :5432); N8N Docker volumes em `/opt/docker_user/n8n`
**Testing**: pytest (Python), ansible-lint (playbooks), curl/HTTP checks (smoke tests)
**Target Platform**: Debian 12 — wfdb01 (86.48.31.149, test+monitoring), wf001 (31.220.103.208, prod N8N), wfdb02 (82.197.64.145, prod DB)
**Project Type**: DevOps automation — Ansible playbooks + Python diagnostic scripts
**Performance Goals**: n8n_queue_* instrumented (F16); execution_entity < 50K rows target (F17); zero dupla coleta (F18)
**Constraints**: wfdb01 gate obrigatório antes de wf001; pg_dump antes de ops destrutivas; maintenance window para restart PostgreSQL; rollback em < 5 min (Princípio III/IV)
**Scale/Scope**: 3 features, 3 servers, produção ativa (121Labs PABX 429K exec, WhatsApp 84K exec)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Verify all 7 principles from `.specify/memory/constitution.md`:

- [x] **I. SDD** — F16, F17 e F18 estão declaradas em `objetivo.yaml` com escopo,
  critérios de aceite e status `not-started`. Plano traça de volta a cada entrada.
- [x] **II. Performance-Tuning Scope** — Todas as três features são
  instrumentação/observabilidade/tunning: métricas de fila (F16), PostgreSQL
  tuning (F17), correção de coleta Prometheus (F18). Nenhuma propõe upgrade de
  versão N8N.
- [x] **III. Infrastructure Safety** — `pg_dump` de F17 DEVE ser executado contra
  wfdb02 (82.197.64.145:6432), não wf001. Rollback via reversão do
  `docker-compose.override.yml` documentado. Maintenance window aprovada para
  restart do PostgreSQL em wfdb02 (F17).
- [x] **IV. wfdb01 Gate** — Todas as features serão validadas em wfdb01 durante ao
  menos um ciclo de pico 121Labs PABX (13:00–22:00 UTC) antes de promover para
  wf001. Evidências métricas before/after planejadas.
- [x] **V. Idempotent Automation** — Todos os playbooks Ansible usam módulos
  idempotentes (`lineinfile`, `template`, `docker_compose`); tasks têm `name:` e
  `tags: [f16|f17|f18]`; `ansible-lint` gate incluído no pipeline.
- [x] **VI. Observability** — Coleta de métricas before/after via VictoriaMetrics
  planejada para cada feature. ANA-001 é baseline. Gaps fechados: fila (F16),
  dupla coleta (F18), pg_stat_statements (F17).
- [x] **VII. Credential Hygiene** — SSH via `.secrets/ssh.json` (SPA fwknop). Senha
  PostgreSQL via Ansible Vault. Nenhuma credencial em playbooks, scripts ou docs.

## Project Structure

### Documentation (this feature)

```text
specs/001-001-tunning-instrumentacao/
├── plan.md              # Este arquivo
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── n8n-metrics-endpoint.md
│   ├── ansible-playbook-interface.md
│   └── python-script-cli.md
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
ansible/
├── inventory/
│   ├── hosts.yml            # wfdb01, wf001, wfdb02
│   └── group_vars/
│       ├── all.yml           # vars compartilhadas (sem credenciais)
│       ├── wfdb01.yml
│       ├── wf001.yml
│       └── wfdb02.yml        # overrides DEV/PROD do PostgreSQL
├── playbooks/
│   ├── f16-queue-metrics.yml
│   ├── f17-postgres-tuning.yml
│   └── f18-dual-collection-audit.yml  # audit somente leitura — F18
└── roles/
    ├── n8n_env/              # role: gestão de docker-compose.override.yml
    ├── postgres_tuning/      # role: pg_stat_statements + backup F17
    └── prometheus_config/    # role: scrape config audit + ProvenanceGate validation F18

src/
├── check_n8n_metrics.py      # Verifica endpoint /metrics — F16/F18
├── purge_execution_entity.py # Diagnóstico de execution_entity — F17
├── validate_prometheus.py    # Valida scrape único — F18
└── collect_gate_evidence.py  # Coleta métricas before/after — todos

enterprise-python-n8n-tunning/
├── src/                     # Código existente
└── tests/                   # Testes existentes
```

**Structure Decision**: Estrutura DevOps automation (single project) com separação
clara entre Ansible (infra/idempotência) e Python (diagnóstico/evidências). Roles
Ansible são reutilizáveis entre features P1, P2, P3.

## Complexity Tracking

> Nenhuma violação de constituição identificada — todos os 7 princípios passam.

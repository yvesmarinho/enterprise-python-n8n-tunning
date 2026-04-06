# Tasks: P1 Tunning e Instrumentação N8N (F16 + F17 + F18)

**Input**: Design documents em `specs/001-001-tunning-instrumentacao/`
**Branch**: `001-001-tunning-instrumentacao`
**Data**: 2026-04-02

**Prerequisites**: plan.md ✅ | spec.md ✅ | research.md ✅ | data-model.md ✅ | contracts/ ✅ | quickstart.md ✅

> ⚠️ **REGRA DE DESENVOLVIMENTO**: Toda validação e homologação DEVE ser concluída
> no ambiente de desenvolvimento (`wfdb01` para N8N e `wfdb02:n8n_dev_db` para PostgreSQL) antes de iniciar qualquer
> atualização no ambiente de produção (wf001 / wfdb02). Esta regra é inviolável
> e se aplica a cada fase de cada feature.

---

## Phase 0: Pré-validação — Estado Atual do Ambiente wfdb01

**Propósito**: Verificar o estado real do N8N em wfdb01 *antes* de aplicar qualquer
playbook F16/F17/F18, e identificar todas as variáveis de monitoramento disponíveis
na versão instalada. Resultados alimentam o baseline de evidências.

- [X] PT001 Validar se `N8N_METRICS_INCLUDE_QUEUE_METRICS` está gerando dados de fila em wfdb01: (1) `curl -sf http://86.48.31.149:5001/metrics | grep -E "^n8n_queue"` — confirmar presença de séries `n8n_queue_*`; (2) registrar lista das métricas encontradas e seus valores atuais; (3) se nenhuma métrica encontrada, inspecionar variáveis de ambiente do container: `docker inspect n8n --format '{{range .Config.Env}}{{.}}\n{{end}}' | grep -i metric`; (4) registrar status: ATIVO/AUSENTE/PARCIAL no session report
- [X] PT002 [P] Pesquisar documentação oficial do N8N para identificar todas as variáveis de ambiente de monitoramento disponíveis além de `N8N_METRICS_INCLUDE_QUEUE_METRICS` e `QUEUE_HEALTH_CHECK_ACTIVE`: consultar docs.n8n.io + changelog da versão instalada; catalogar variáveis por categoria (métricas, queue, diagnóstico, histograma); comparar com as variáveis atualmente em uso; propor ajustes ao `docker-compose.override.j2` se variáveis adicionais forem relevantes para F16

**Checkpoint PT**: Baseline real de métricas wfdb01 documentado; inventário completo de vars de monitoramento disponíveis → alimenta refinamento de T012 (template override.j2) se necessário.

---

## Formato: `[ID] [P?] [Story?] Descrição com caminho de arquivo`

- **[P]**: Pode rodar em paralelo (arquivos distintos, sem dependências incompletas)
- **[Story]**: User story à qual a task pertence (US1=F16, US2=F17, US3=F18)
- **Setup / Foundational / Polish**: sem label de story

---

## Phase 1: Setup — Infraestrutura Ansible e Python

**Propósito**: Criar estrutura de inventário, variáveis de grupo e
dependências Python necessárias para todos os playbooks e scripts.

- [X] T001 Criar `ansible/inventory/hosts.yml` com grupos wfdb01, wf001 e wfdb02 conforme contrato `contracts/ansible-playbook-interface.md` (ansible_host, ansible_port, ansible_user por host)
- [X] T002 [P] Criar `ansible/inventory/group_vars/all.yml` com variáveis compartilhadas: `n8n_compose_dir`, `n8n_queue_alert_threshold`, `n8n_prune_max_age_hours`, `n8n_prune_timeout_ms`, `db_host`, `db_port`, `db_pgbouncer_port`, `db_name: n8n_db`
- [X] T003 [P] Criar `ansible/inventory/group_vars/wfdb01.yml` com overrides de wfdb01 (vm_url, environment=wfdb01)
- [X] T004 [P] Criar `ansible/inventory/group_vars/wf001.yml` com overrides de wf001 (environment=wf001)
- [X] T005 [P] Consolidar o ambiente DEV PostgreSQL em `ansible/inventory/group_vars/wfdb02.yml`, com `db_name: n8n_dev_db` para o gate do Vetor B
- [X] T006 [P] Atualizar `pyproject.toml` na raiz do projeto adicionando dependências: `psycopg2-binary>=2.9`, `prometheus-client>=0.20`, `paramiko>=3.4`, `fabric>=3.2` com `[tool.uv.sources]` ou grupo `[project.optional-dependencies]`
- [X] T007 [P] Adicionar targets no `Makefile`: `make f16` (run f16-queue-metrics.yml -l wfdb01), `make f17` (run f17-postgres-tuning.yml -l wfdb01), `make f18` (run f18-dual-collection-audit.yml -l wfdb01), `make lint-playbooks` (ansible-lint ansible/playbooks/)

**Checkpoint**: Inventário válido, group_vars completos, deps Python declaradas — build de infraestrutura pode começar.

---

## Phase 2: Fundacional — Role Skeletons e Script de Gate Compartilhado

**Propósito**: Criar os esqueletos de roles Ansible reutilizáveis e o script
de coleta de evidências used por US1, US2 e US3.

**⚠️ CRÍTICO**: Nenhuma fase de User Story pode começar enquanto esta fase não estiver completa.

- [X] T008 Criar estrutura completa do role `ansible/roles/n8n_env/` com: `defaults/main.yml` (n8n_compose_dir, override vars), `tasks/main.yml` (include_tasks por feature com tags), `meta/main.yml` (galaxy_info com min_ansible_version: "2.15")
- [X] T009 [P] Criar estrutura completa do role `ansible/roles/postgres_tuning/` com: `defaults/main.yml` (db_host, db_port, db_name, backup_dir: /tmp, prune_max_age_hours: 720), `tasks/main.yml` (include_tasks por subtag), `meta/main.yml`
- [X] T010 [P] Criar estrutura completa do role `ansible/roles/prometheus_config/` com: `defaults/main.yml` (vm_url, feature_id, environment), `tasks/main.yml` (include_tasks), `meta/main.yml`
- [X] T011 Criar `src/collect_gate_evidence.py` conforme contrato `contracts/python-script-cli.md` — args: `--feature F16|F17|F18`, `--environment wfdb01|wf001`, `--vm-url URL`, `--output-dir DIR`; consulta PromQL no VictoriaMetrics, gera JSON com `metrics`, `status (pass|fail|inconclusive)`, `collected_at`; docstrings reStructuredText; logging via stderr; saída JSON via stdout

**Checkpoint**: Roles e script de gate prontos — stories US1, US2, US3 podem ser implementadas em paralelo.

---

## Phase 3: User Story 1 — F16: Habilitação de Métricas de Fila N8N (Priority: P1) 🎯

**Goal**: Playbook Ansible idempotente ativa métricas `n8n_queue_*` no N8N de
wfdb01 via `docker-compose.override.yml`; alert rule Prometheus criada; script
Python valida presença das séries em `/metrics`.

**Teste Independente**: `curl -sf http://86.48.31.149:5001/metrics | grep n8n_queue_depth && echo PASS` após execução do playbook em wfdb01.

### Implementação US1

- [X] T012 [US1] Criar `ansible/roles/n8n_env/templates/docker-compose.override.j2` com bloco `services.n8n.environment` contendo variáveis F16 (`N8N_METRICS_INCLUDE_QUEUE_METRICS`, `QUEUE_HEALTH_CHECK_ACTIVE`, `N8N_METRICS_ENABLED`) e F17 (`EXECUTIONS_DATA_PRUNE`, `EXECUTIONS_DATA_PRUNE_MAX_AGE`, `EXECUTIONS_DATA_PRUNE_TIMEOUT`) controladas por vars Jinja2 booleanas (`n8n_f16_enabled`, `n8n_f17_enabled`)
- [X] T013 [P] [US1] Criar `ansible/roles/n8n_env/tasks/f16_queue_metrics.yml` com tasks: (1) `stat` + `assert` do docker-compose.yml em `n8n_compose_dir`, (2) `template` do override.j2, (3) `command: docker compose up -d n8n args: {chdir: n8n_compose_dir}`, (4) `wait_for: {port: 5001, timeout: 120}` — todas com `tags: [f16, n8n_env]`
- [X] T014 [P] [US1] Criar `ansible/roles/n8n_env/files/alert_rules/n8n_queue_alert.yml` com alert rule Prometheus: `alert: N8NQueueDepthHigh`, `expr: n8n_queue_depth > {{ n8n_queue_alert_threshold }}`, `for: 2m`, labels e anotações completas
- [X] T015 [US1] Criar `ansible/playbooks/f16-queue-metrics.yml` com estrutura obrigatória: Play 1 (SPA knock: fwknop + pause: 3s + wait_for port 5010) + Play 2 (hosts: wfdb01, include_role: n8n_env, vars: n8n_f16_enabled: true, tags: f16) conforme padrão `contracts/ansible-playbook-interface.md`
- [X] T016 [P] [US1] Criar `src/check_n8n_metrics.py` conforme contrato `contracts/python-script-cli.md` — args: `--host`, `--port`, `--timeout`; HTTP GET `/metrics`; retorna JSON com `metrics_found`, `metrics_missing`, `raw_count`; exit code 0=pass, 1=missing, 2=timeout; docstrings reStructuredText com doctest
- [X] T017 [US1] Validar F16 em wfdb01 (DEV/TEST GATE — OBRIGATÓRIO antes de wf001): (1) BEFORE: `python src/check_n8n_metrics.py --metrics-url https://testn8n.vya.digital` → status:pass, 4 métricas encontradas; (2) `ansible-playbook ansible/playbooks/f16-queue-metrics.yml --skip-tags always` → ok=7 changed=2 failed=0; (3) override criado em `/opt/docker_user/n8n/docker-compose.override.yml`; (4) AFTER: `python src/check_n8n_metrics.py --metrics-url https://testn8n.vya.digital` → status:pass; evidências em `docs/SESSIONS/2026-04-02/T017_GATE_F16_EVIDENCE.md` | NOTA: VictoriaMetrics (wfdb01) não exposta ao host — evidência via endpoint direto HTTPS

**Checkpoint**: US1 completo — `n8n_queue_depth` visível em wfdb01, SC-001 validado em ambiente de desenvolvimento.

---

## Phase 4: User Story 2 — F17: Purgação e Tunning PostgreSQL N8N (Priority: P1)

**Goal**: Playbook Ansible idempotente ativa purgação automática da
`execution_entity` (Vetor A, sem restart) e provisiona `pg_stat_statements`
(Vetor B, com restart), validando Vetor B primeiro no banco DEV `n8n_dev_db`
em `wfdb02` antes de operar o `n8n_db`.

**Teste Independente**: `python src/purge_execution_entity.py --db-host 82.197.64.145 --db-port 6432 --db-name n8n_dev_db --check-only` retorna resultado consistente; `SELECT extname FROM pg_extension WHERE extname = 'pg_stat_statements'` retorna resultado no `n8n_dev_db` em `wfdb02`.

### Implementação US2

- [X] T018 [US2] Criar `ansible/roles/postgres_tuning/tasks/f17_backup.yml`: (1) `command: pg_dump -h db_host -p db_port -U n8n -Fc n8n_db | gzip > /tmp/n8n_backup_{{ ansible_date_time.iso8601_basic_short }}.sql.gz` em wfdb02, (2) `stat` + `assert: {that: dump_stat.stat.size > 0}`, (3) `command: sha256sum /tmp/n8n_backup_*.sql.gz | tee /tmp/n8n_backup_latest.sha256`, (4) `fetch` do sha256 para controlador local — `tags: [f17, f17-backup]`
- [X] T018b [US2] Executar restore-test do backup em wfdb01 (SC-005 / FR-006 gate): restaurar dump mais recente em banco temp `n8n_db_restoretest` no wfdb01, via `gunzip -c $(ls -t /tmp/n8n_backup_*.sql.gz | head -1) | psql -h 86.48.31.149 -p 6432 -U n8n n8n_db_restoretest`; afirmar que `SELECT count(*) FROM execution_entity` na DB de restore ≥ valor registrado no backup; registrar `restore_tested: true` no session report; dropar DB de teste após validação
- [X] T019 [P] [US2] Criar `ansible/roles/postgres_tuning/tasks/f17_prune.yml`: incluir role `n8n_env` com vars `n8n_f17_enabled: true` (ativa `EXECUTIONS_DATA_PRUNE=true`, `EXECUTIONS_DATA_PRUNE_MAX_AGE=720`, `EXECUTIONS_DATA_PRUNE_TIMEOUT=3600000` via template override.j2) — `tags: [f17, f17-prune]`
- [X] T021 [P] [US2] Criar `ansible/roles/postgres_tuning/tasks/f17_pgstat.yml`: (1) `postgresql_set: {name: shared_preload_libraries, value: pg_stat_statements}` via `ALTER SYSTEM`, (2) restart controlado do PostgreSQL (`service: {name: postgresql, state: restarted}`), (3) `postgresql_ext: {name: pg_stat_statements, db: "{{ db_name }}", state: present}`, (4) `postgresql_query` para verificar `pg_stat_statements` ativo — `tags: [f17, f17-pgstat]`
- [X] T022 [P] [US2] Criar `ansible/roles/postgres_tuning/templates/postgresql_override.conf.j2` com `shared_preload_libraries = 'pg_stat_statements'`, `pg_stat_statements.track = 'all'`, `pg_stat_statements.max = 10000`
- [X] T023 [US2] Criar `src/purge_execution_entity.py` conforme contrato `contracts/python-script-cli.md` — args: `--db-host`, `--db-port`, `--db-name`, `--check-only`, `--prune-older-than-days`; credenciais via `PG_USER`/`PG_PASSWORD` env vars (NUNCA args); retorna JSON com `row_count_before`, `rows_deleted`, `table_size_before_mb`; psycopg2; docstrings reStructuredText
- [X] T024 [US2] Criar `ansible/playbooks/f17-postgres-tuning.yml` com estrutura: Play 1 (SPA knock VPS), Play 2 (backup: hosts wfdb02, role postgres_tuning, tags f17-backup), Play 3 (prune: hosts wfdb01, role postgres_tuning, tags f17-prune), Play 4 (pgstat: hosts wfdb02 com `when: f17_pgstat_approved | default(false)`, tags f17-pgstat)
- [X] T025 [US2] Validar F17 Vetor A em wfdb01 (DEV/TEST GATE): (1) coletar evidência BEFORE `collect_gate_evidence.py --feature F17`, (2) `ansible-playbook f17-postgres-tuning.yml --tags f17-backup,f17-prune -l wfdb01 --check --diff`, (3) aplicar sem --check, (4) `python src/purge_execution_entity.py --db-host 82.197.64.145 --db-port 6432 --db-name n8n_dev_db --check-only`, (5) coletar evidência AFTER
- [X] T026 [US2] Validar F17 Vetor B DEV GATE em `wfdb02:n8n_dev_db` (OBRIGATÓRIO antes do `n8n_db`): (1) `ansible-playbook f17-postgres-tuning.yml --tags f17-pgstat -l wfdb02 -e f17_pgstat_approved=true` executado com sucesso, (2) extensão `pg_stat_statements` confirmada em `n8n_dev_db`, (3) role ajustado para usar `psql` como `postgres` no próprio host por requisito de privilégio

**Checkpoint**: US2 completo — EXECUTIONS_DATA_PRUNE ativo em wfdb01, pg_stat_statements validado em `n8n_dev_db`, backup de wfdb02 presente com SHA-256.

---

## Phase 5: User Story 3 — F18: Auditoria de Dupla Coleta e Change Request (Priority: P1)

**Goal**: Script Python + playbook de diagnóstico somente leitura geram relatório
JSON com dupla coleta confirmada, nome da variável de controle, e o template
`contracts/prod-collector-api-issue.md` é preenchido com dados reais para
submissão ao projeto responsável. `prod-collector-api` NÃO é modificado.

**Teste Independente**: Arquivo `docs/SESSIONS/$(date +%Y-%m-%d)/f18-dual-collection-report.json` gerado com `verdict: DUAL_COLLECTION`, `pushgateway_series_found` não vazio, `n8n_metric_jobs_found` com jobs reais (`collector_api_wf001_usa`, `collector_api_wf001_usa_ping_data`, `n8n`) e `contracts/prod-collector-api-issue.md` com variável de controle confirmada.

### Implementação US3

- [X] T027 [US3] Criar `src/validate_prometheus.py` conforme contrato `contracts/python-script-cli.md` — args: `--vm-url`, `--lookback`, `--report`, `--output`, `--mode [dual-collection|provenance-gate]`; no modo `dual-collection`: PromQL `{instance=~".*0\\.0\\.0\\.0.*"}` para detectar série Pushgateway; no modo `provenance-gate`: `absent_over_time({instance=~".*0\\.0\\.0\\.0.*", job="pushgateway"}[1h])` + cross-check SQL `COUNT(*) FROM execution_entity` via psycopg2 (tolerância ≤ 1%); saída JSON com `verdict`, `pushgateway_series_found`, `provenance_gate.pushgateway_absent_1h`, `provenance_gate.execution_count_coherent`, `provenance_gate.count_delta_pct`
- [X] T028 [P] [US3] Criar `ansible/playbooks/f18-dual-collection-audit.yml` com: Play 1 (SPA knock), Play 2 (hosts: wfdb01, tasks: `command: docker inspect prod-collector-api` com `register: inspect_result`, `set_fact` para extrair env vars Pushgateway-related, `copy` do JSON de inspeção para controller local) — **SOMENTE LEITURA, nenhuma modificação ao prod-collector-api** — `tags: [f18, f18-audit]`
- [X] T029 [US3] Executar F18 em wfdb01 (DEV/TEST GATE): (1) `validate_prometheus.py` executado remotamente em `wfdb01` contra `http://172.20.0.13:8428` com `verdict: DUAL_COLLECTION`, (2) `ansible-playbook ansible/playbooks/f18-dual-collection-audit.yml -i ansible/inventory/ -l wfdb01` executado sem falhas, (3) jobs reais registrados no relatório (`collector_api_wf001_usa`, `collector_api_wf001_usa_ping_data`, `n8n`, `pushgateway_wfdb01`)
- [X] T030 [US3] Preencher `contracts/prod-collector-api-issue.md` com dados reais do T029: flag confirmada em `wf001` como `PROMETHEUS_PUSHGATEWAY_ENABLED=true`, serviço `adminvyadigital/n8n-collector-api:latest`, exposição direta `0.0.0.0:5001 -> 5000/tcp`, data de inspeção e evidência PromQL consolidadas

**Checkpoint**: US3 completo — relatório JSON de dupla coleta gerado, `prod-collector-api-issue.md` preenchido com dados reais prontos para submissão, SC-006/SC-007 documentados como critérios de aceite.

---

## Phase 6: Polish — Gate de Evidências, Lint e Promoção em Bloco

**Propósito**: Validação cruzada de qualidade, lint de playbooks e promoção
em bloco F16+F17+F18 para wf001 após aprovação do test_engineer.

> ⚠️ **PROMOÇÃO EM BLOCO (FR-010)**: F16, F17 **e** F18 DEVEM ser promovidos
> juntos para wf001. Nenhuma feature pode ser promovida individualmente.
> F18 só entra no bloco após ProvenanceGate aprovado pelo projeto responsável.

- [X] T031 [P] Executar `ansible-lint ansible/playbooks/f16-queue-metrics.yml ansible/playbooks/f17-postgres-tuning.yml ansible/playbooks/f18-dual-collection-audit.yml` — corrigir todos os erros antes de prosseguir (`make lint-playbooks`); además: executar cada playbook uma segunda vez contra wfdb01 sem alterações e afirmar que o PLAY RECAP mostra `changed=0` para todos os plays (FR-008 / Princípio V — idempotência obrigatória)
- [ ] T032 [P] Executar verificações de gate AFTER em wfdb01 para SC-001–SC-007: (1) `python src/check_n8n_metrics.py --metrics-url https://testn8n.vya.digital` confirma as 4 séries `n8n_scaling_mode_queue_jobs_*` esperadas (SC-001), (2) `python src/purge_execution_entity.py --db-host 82.197.64.145 --db-port 6432 --db-name n8n_dev_db --check-only` confirma tendência de queda vs baseline 429K+ (SC-003), (3) `python src/validate_prometheus.py --vm-url http://127.0.0.1:8428 --mode dual-collection` com SSH tunnel ativo confirma DUAL_COLLECTION ainda ativa (SC-006 pendente de F18 externo), (4) smoke tests HTTP: healthz, /metrics, /api/v1/workflows retornam 200
- [ ] T033 Executar ProvenanceGate pós-correção pelo projeto responsável (F18 externo): `python src/validate_prometheus.py --vm-url http://86.48.31.149:8428 --mode provenance-gate --report --output docs/SESSIONS/$(date +%Y-%m-%d)/f18-provenance-gate-report.json` — confirmar `verdict: PROVENANCE_OK`, `pushgateway_absent_1h: true`, `execution_count_coherent: true` (SC-006 + SC-007)
- [ ] T034 Executar promoção em bloco F16+F17+F18 para wf001 (PRODUÇÃO — apenas após aprovação de test_engineer para todos os gates): `ansible-playbook f16-queue-metrics.yml -l wf001`, `ansible-playbook f17-postgres-tuning.yml --tags f17-prune -l wf001`, executar F18 audit em wf001 + submeter issue atualizado; monitorar wf001 ≥ 1 ciclo de pico (13:00–22:00 UTC); coletar evidências AFTER em wf001

---

## Grafo de Dependências (por conclusão de User Story)

```
Phase 1 (Setup)
  └─→ Phase 2 (Foundational: T008–T011)
        ├─→ Phase 3 (US1 — F16): T012→T017   │
        ├─→ Phase 4 (US2 — F17): T018→T026   │ independentes entre si
        └─→ Phase 5 (US3 — F18): T027→T030   │
                          │
                          └─→ Phase 6 (Gate + Promoção): T031→T034
```

**Dependências críticas**:
- T017 (validar F16 wfdb01) → bloqueia inclusão de F16 no gate de promoção
- T025 (validar F17 Vetor A wfdb01) + T026 (`wfdb02:n8n_dev_db` Vetor B gate) → bloqueiam F17 no gate
- T029 (F18 audit) + T033 (ProvenanceGate externo) → bloqueiam F18 no gate
- T031 (ansible-lint) → DEVE passar antes de T034
- T032 (smoke tests wfdb01) → precede T034
- **T034 (promoção wf001) depende de T017 + T025 + T026 + T029 + T031 + T032 + T033 todos aprovados**

---

## Exemplos de Execução em Paralelo por Story

```bash
# Phase 2 → após concluída, iniciar US1+US2+US3 em paralelo:

# Terminal 1 — US1 (F16)
cd specs/001-001-tunning-instrumentacao/
# Implementar T012→T016, validar T017

# Terminal 2 — US2 (F17)
# Implementar T018→T023, validar T025→T026

# Terminal 3 — US3 (F18)
# Implementar T027→T028, executar T029→T030

# Após todos concluídos:
# Phase 6: lint → gate evidence → provenance → promoção em bloco
```

---

## Estratégia de Implementação (MVP First)

**MVP Mínimo (US1 apenas)**:
- Phases 1 + 2 + Phase 3 (T001–T017)
- Entrega: `n8n_queue_*` visível em wfdb01 — hipótese ANA-001 testável
- Tempo estimado: 1 sessão de trabalho

**P1 Completo (US1+US2+US3)**:
- Todas as phases
- Entrega: F16 + F17 Vetor A validados em wfdb01; F18 issue submetido ao projeto responsável; Vetor B em `wfdb02:n8n_dev_db` aprovado
- Promoção em bloco para wf001 após ProvenanceGate externo

---

## Contagem de Tasks

| Fase | Tasks | Paralelizáveis | Story |
|------|-------|---------------|-------|
| Phase 1: Setup | T001–T007 | 6/7 | — |
| Phase 2: Foundational | T008–T011 | 2/4 | — |
| Phase 3: US1 (F16) | T012–T017 | 3/6 | US1 |
| Phase 4: US2 (F17) | T018–T026 | 4/9 | US2 |
| Phase 5: US3 (F18) | T027–T030 | 1/4 | US3 |
| Phase 6: Polish | T031–T034 | 2/4 | — |
| **Total** | **36 tasks** | **18 paralelizáveis** | |

**MVP (US1)**: 11 tasks (T001–T017 relevantes) — entrega independente e testável.

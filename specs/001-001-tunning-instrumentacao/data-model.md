# Data Model: P1 Tunning e Instrumentação N8N (F16 + F17 + F18)

**Feature**: `001-001-tunning-instrumentacao` | **Date**: 2026-04-02

---

## Entidades

### NativeEnvConfig

Representa as variáveis de ambiente do container N8N que controlam coleta de
métricas de fila (F16) e purgação de execuções (F17).

**Campos**:

| Variável | Tipo | Valor Padrão | Valor Target | Feature |
|----------|------|-------------|-------------|---------|
| `N8N_METRICS_INCLUDE_QUEUE_METRICS` | bool string | `false` / ausente | `true` | F16 |
| `QUEUE_HEALTH_CHECK_ACTIVE` | bool string | `false` / ausente | `true` | F16 |
| `N8N_METRICS_ENABLED` | bool string | depende da versão | `true` | F16 |
| `EXECUTIONS_DATA_PRUNE` | bool string | `false` | `true` | F17 |
| `EXECUTIONS_DATA_PRUNE_MAX_AGE` | int (horas) | ausente | `720` (30 dias) | F17 |
| `EXECUTIONS_DATA_PRUNE_TIMEOUT` | int (ms) | ausente | `3600000` (1h) | F17 |

**Estado**:
- `baseline` → variáveis ausentes ou desabilitadas
- `configured` → variáveis presentes com valores target em `docker-compose.override.yml`
- `validated` → endpoint `/metrics` retorna séries esperadas OU purgação ativa

**Gerenciado via**: `docker-compose.override.yml` em `/opt/docker_user/n8n/`

**Rollback**: Remover `docker-compose.override.yml` + `docker compose up -d n8n`

---

### PostgresConfig

Representa os ajustes de configuração do PostgreSQL 16 em wfdb02 para
diagnóstico de performance e purgação controlada (F17).

**Campos**:

| Parâmetro | Tipo | Valor Padrão | Valor Target | Restart? |
|-----------|------|-------------|-------------|---------|
| `shared_preload_libraries` | string | `''` | `'pg_stat_statements'` | **SIM** |
| `pg_stat_statements.track` | string | ausente | `'all'` | Não (reload) |
| `pg_stat_statements.max` | int | 5000 | `10000` | Não (reload) |

**Extensão** (post-restart): `CREATE EXTENSION IF NOT EXISTS pg_stat_statements;`
executada na database do N8N (banco: **`n8n_db`** — confirmado).

**BackupSnapshot**:

| Campo | Descrição |
|-------|-----------|
| `dump_file` | Path local do `pg_dump` — ex: `/tmp/n8n_backup_YYYYMMDD_HHMMSS.sql.gz` |
| `dump_size_bytes` | Tamanho do dump (validação: > 0) |
| `dump_sha256` | Hash SHA-256 para verificação de integridade |
| `dump_timestamp` | Timestamp ISO 8601 |
| `restore_tested` | `true/false` — restore bem-sucedido em wfdb01 |

---

### PrometheusCollectionConfig

Representa o estado de coleta de métricas do prod-collector-api (F18).

**Campos do prod-collector-api**:

| Variável | Valor Atual (dupla coleta) | Valor Target | Feature |
|----------|--------------------------|-------------|---------|
| `PROMETHEUS_PUSHGATEWAY_ENABLED` | `true` | `false` | F18 (via change request — projeto responsável) |
| `PROMETHEUS_PUSHGATEWAY_URL` | `http://pushgateway:9091` | inalterado | F18 |

**Estado da coleta**:
- `dual` (baseline ANA-001): scrape direto wf001:5001 **E** pushgateway ativo
  → séries duplicadas com labels distintos
- `issuing` (scope F18 neste projeto): change request formal emitido para o
  projeto responsável pelo `prod-collector-api`; variável de controle documentada
- `single-scrape` (target, pós-change-request): apenas scrape direto; pushgateway
  não recebe dados do prod-collector-api; ProvenanceGate validado

**Critério de validação** (via PromQL):
```promql
# ANTES: retorna séries → confirma dupla coleta
{instance=~".*0\\.0\\.0\\.0.*"}[5m]

# DEPOIS: retorna vazio ou sem novos pontos > 1h
absent_over_time({instance=~".*0\\.0\\.0\\.0.*", job="pushgateway"}[1h])
```

---

### WfdbGateEvidence

Registro estruturado das evidências do gate wfdb01 → wf001. Uma instância por
feature por promoção.

**Campos**:

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `feature_id` | string | `F16`, `F17`, ou `F18` |
| `environment` | string | `wfdb01` (gate) ou `wf001` (produção) |
| `applied_at` | datetime ISO 8601 | Timestamp da aplicação |
| `configuration_delta` | dict | Variáveis alteradas: `{var: {before, after}}` |
| `metrics_before` | dict | Snapshot PromQL antes — campos específicos por feature |
| `metrics_after` | dict | Snapshot PromQL após — mesmos campos |
| `smoke_tests` | list[SmokTest] | Resultados dos smoke tests |
| `peak_cycle_covered` | bool | `true` se monitorado durante 13:00–22:00 UTC |
| `test_engineer_signoff` | string | Assinatura/nome do test_engineer |
| `status` | enum | `passed`, `failed`, `rollback` |

**SmokTest sub-entity**:

| Campo | Tipo | Valor Esperado |
|-------|------|---------------|
| `endpoint` | string | `/healthz`, `/metrics`, `/api/v1/workflows` |
| `http_status` | int | `200` |
| `response_time_ms` | int | < 500 ms |

---

## Relacionamentos

```
NativeEnvConfig ──(configura)──► N8N Container (wfdb01 / wf001)
PostgresConfig  ──(configura)──► PostgreSQL 16 (wfdb02)
PrometheusCollectionConfig ──(configura)──► prod-collector-api
WfdbGateEvidence ──(registra)──► NativeEnvConfig | PostgresConfig | PrometheusCollectionConfig
BackupSnapshot ──(precede)──► PostgresConfig (F17 — obrigatório antes de purge)
```

---

## Transições de Estado por Feature

### F16: Métricas de Fila

```
baseline (sem n8n_queue_*)
  → [playbook f16] → configured (vars adicionadas)
  → [docker restart] → active (métricas no endpoint)
  → [PromQL check] → validated (séries no VictoriaMetrics)
  → [gate wfdb01] → promoted (replicado em wf001)
```

### F17: PostgreSQL Tuning

```
EXECUTIONS_DATA_PRUNE:
  baseline (off) → [env var] → configured → [N8N restart] → pruning_active

pg_stat_statements:
  baseline (off) → [ALTER SYSTEM] → pending_restart
  → [maint window + restart] → extension_ready
  → [CREATE EXTENSION] → monitoring_active

BackupSnapshot:
  pending → [pg_dump wfdb02] → dumped → [restore test wfdb01] → validated
```

### F18: Correção Dupla Coleta

```
dual_collection (broken)
  → [disable pushgateway env] → pushgateway_disabled
  → [docker restart prod-collector-api] → single_scrape
  → [PromQL absent check ≥ 1h] → validated
  → [gate wfdb01] → promoted (replicado em wf001)
```

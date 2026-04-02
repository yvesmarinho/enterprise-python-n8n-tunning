# Contract: Python Script CLI Interface

**Interface**: Python scripts executados localmente para diagnóstico e coleta de evidências
**Consumers**: Operador DevOps, playbooks Ansible (via `command` module)
**Relevante para**: F16, F17, F18

---

## src/check_n8n_metrics.py

```
Usage: python src/check_n8n_metrics.py --metrics-url URL [--timeout SECS]

Arguments:
  --metrics-url  URL base do servidor N8N (ex: https://testn8n.vya.digital)
                 O endpoint /metrics será acessado em URL/metrics
  --timeout      Timeout HTTP em segundos (default: 10)

Nota: acesso via HTTPS/Traefik — não requer mapeamento de porta direto ao host.

Output (stdout): JSON
{
  "url": "https://testn8n.vya.digital",
  "status": "pass|fail",
  "metrics_found": ["n8n_scaling_mode_queue_jobs_active", ...],
  "metrics_missing": [],
  "raw_count": 142,
  "checked_at": "2026-04-02T11:00:00Z",
  "error": null
}

Métricas de fila esperadas (N8N 2.x queue mode):
  n8n_scaling_mode_queue_jobs_active
  n8n_scaling_mode_queue_jobs_waiting
  n8n_scaling_mode_queue_jobs_completed
  n8n_scaling_mode_queue_jobs_failed

Exit codes:
  0 = todas as métricas esperadas presentes
  1 = métricas ausentes ou endpoint inacessível
  2 = timeout
```

---

## src/purge_execution_entity.py

```
Usage: python src/purge_execution_entity.py \
         --db-host HOST --db-port PORT --db-name NAME \
         [--check-only] [--prune-older-than-days N]

Arguments:
  --db-host           IP do PostgreSQL (wfdb02: 82.197.64.145)
  --db-port           Porta PostgreSQL ou Pgbouncer (default: 6432)
  --db-name           Nome da database N8N
  --check-only        Apenas relata contagem e tamanho; não purga
  --prune-older-than-days  Purgar execuções mais antigas que N dias (default: 30)

Credenciais: via variáveis de ambiente (NUNCA args):
  PG_USER, PG_PASSWORD (ou PGPASSFILE)

Output (stdout): JSON
{
  "table": "execution_entity",
  "row_count_before": 429000,
  "row_count_after": null,   # null se --check-only
  "rows_deleted": null,
  "table_size_before_mb": 312.4,
  "table_size_after_mb": null,
  "checked_at": "2026-04-02T11:00:00Z",
  "check_only": true
}

Exit codes:
  0 = sucesso
  1 = erro de conexão
  2 = erro de query
```

---

## src/validate_prometheus.py

```
Usage: python src/validate_prometheus.py \
         --vm-url URL [--lookback DURATION] [--report] [--output FILE]
         [--mode dual-collection|provenance-gate]

Arguments:
  --vm-url      URL do VictoriaMetrics (ex: http://86.48.31.149:8428)
  --lookback    Janela de tempo PromQL (default: 1h)
  --report      Gerar relatório JSON completo (default: apenas verdict)
  --output      Arquivo de saída para o relatório JSON (default: stdout)
  --mode        Modo de validação:
                  dual-collection  : detectar dupla coleta (default)
                  provenance-gate  : validar proveniência única pós-correção

Output (stdout): JSON
{
  "dual_collection_active": true|false,
  "pushgateway_series_found": ["...label pairs..."],
  "direct_scrape_series_count": 142,
  "checked_at": "2026-04-02T11:00:00Z",
  "verdict": "DUAL_COLLECTION|SINGLE_SCRAPE|NO_DATA|PROVENANCE_OK|PROVENANCE_FAIL",
  "provenance_gate": {
    "pushgateway_absent_1h": true|false,
    "execution_count_coherent": true|false,
    "count_delta_pct": 0.0
  }
}

Exit codes:
  0 = single scrape confirmado (mode=dual-collection) ou ProvenanceGate PASS
  1 = dupla coleta ainda ativa ou ProvenanceGate FAIL
  2 = VictoriaMetrics inacessível
```

---

## src/collect_gate_evidence.py

```
Usage: python src/collect_gate_evidence.py \
         --feature F16|F17|F18 \
         --environment wfdb01|wf001 \
         --vm-url URL \
         [--output-dir DIR]

Arguments:
  --feature       Feature ID a coletar evidências
  --environment   Ambiente onde foi aplicado
  --vm-url        URL do VictoriaMetrics
  --output-dir    Destino do JSON de evidências
                  (default: docs/SESSIONS/YYYY-MM-DD/)

Output: arquivo JSON + log stdout
{
  "feature_id": "F16",
  "environment": "wfdb01",
  "collected_at": "2026-04-02T11:00:00Z",
  "metrics": {
    "n8n_queue_depth": {"value": 0.0, "labels": {"instance": "wfdb01"}},
    ...
  },
  "status": "pass|fail|inconclusive"
}

Exit codes:
  0 = evidências coletadas com sucesso
  1 = VictoriaMetrics inacessível
  2 = feature_id desconhecido
```

---

## Convenções Gerais dos Scripts Python

- Saída principal: JSON via `stdout`
- Logs de progresso: `logging` stdlib → `stderr` (NUNCA `print()`)
- Credenciais: variáveis de ambiente (`os.environ.get`) — NUNCA args de linha de comando
- Docstrings: formato reStructuredText com Doctest onde aplicável
- Design pattern: Fabric (funções puras compostas, sem estado global mutável)
- Código de erro explícito em cada saída JSON: campo `"error": null|"message"`

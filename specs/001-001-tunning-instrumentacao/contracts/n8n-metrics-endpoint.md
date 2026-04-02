# Contract: N8N Metrics Endpoint

**Interface**: HTTP GET `/metrics` no container N8N (via prod-collector-api)
**Consumers**: Prometheus scrape, script `src/check_n8n_metrics.py`
**Relevante para**: F16 (queue metrics), F18 (validação pós-correção)

---

## Endpoint

```
GET http://{host}:{port}/metrics
Host (wfdb01): 86.48.31.149:5001
Host (wf001):  31.220.103.208:5001
Content-Type: text/plain; version=0.0.4
```

## Métricas Esperadas Após F16

As seguintes séries DEVEM estar presentes no endpoint após aplicação de F16:

| Métrica | Tipo | Descrição |
|---------|------|-----------|
| `n8n_queue_depth` | gauge | Número de jobs aguardando na fila Bull |
| `n8n_queue_waiting` | gauge | Jobs em estado `waiting` |
| `n8n_queue_active` | gauge | Jobs em execução ativa |
| `n8n_queue_delayed` | gauge | Jobs com execução adiada |
| `n8n_queue_failed` | gauge | Jobs que falharam |
| `n8n_queue_completed` | gauge/counter | Jobs concluídos |
| `n8n_executions_total` | counter | Contagem total de execuções |

## Validação

```bash
# Comando de smoke test
curl -sf http://86.48.31.149:5001/metrics | grep -q "n8n_queue_depth" && echo "PASS" || echo "FAIL"
```

## Estado Esperado Após F18

A série com `instance=~".*0\\.0\\.0\\.0.*"` NÃO DEVE aparecer como fonte ativa.
O scrape deve ter apenas `instance=wf001` (relabeled).

## Contratos de Label

| Label | Valor Esperado |
|-------|---------------|
| `instance` | `wf001` (relabeled pelo scrape config) |
| `job` | `n8n` |
| `__address__` | `31.220.103.208:5001` |

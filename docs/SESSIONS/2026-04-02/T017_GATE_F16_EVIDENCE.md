# T017 — Gate F16: Queue Metrics (wfdb01)

**Data**: 2026-04-02
**Ambiente**: wfdb01.vya.digital (86.48.31.149)
**Feature**: F16 — Habilitar Métricas de Fila N8N
**Resultado**: ✅ PASS

---

## 1. BEFORE Evidence

**Timestamp**: 2026-04-02T18:17:49Z
**Comando**: `python src/check_n8n_metrics.py --metrics-url https://testn8n.vya.digital`

```json
{
  "url": "https://testn8n.vya.digital",
  "status": "pass",
  "metrics_found": [
    "n8n_scaling_mode_queue_jobs_active",
    "n8n_scaling_mode_queue_jobs_waiting",
    "n8n_scaling_mode_queue_jobs_completed",
    "n8n_scaling_mode_queue_jobs_failed"
  ],
  "metrics_missing": [],
  "raw_count": 43,
  "checked_at": "2026-04-02T18:17:49.303690+00:00",
  "error": null
}
```

**Estado**: F16 já ativo via `.env` (`N8N_METRICS=true`, `N8N_METRICS_INCLUDE_QUEUE_METRICS=true`) — 4 métricas de fila presentes.

---

## 2. Ansible Playbook — f16-queue-metrics.yml

**Arquivo**: `ansible/playbooks/f16-queue-metrics.yml`
**Comando**: `ansible-playbook playbooks/f16-queue-metrics.yml --skip-tags always`
**Exit code**: 0

### Resultado

```
TASK [n8n_env : F16 | Assert docker-compose.yaml exists]         ok
TASK [n8n_env : F16 | Fail if docker-compose.yaml not found]     ok: All assertions passed
TASK [n8n_env : F16 | Deploy docker-compose.override.yml]        changed
TASK [n8n_env : F16 | Restart n8n services]                      changed
TASK [n8n_env : F16 | Wait for N8N metrics endpoint to respond]  ok

PLAY RECAP: ok=7, changed=2, failed=0, skipped=1
```

### Override implantado

`/opt/docker_user/n8n/docker-compose.override.yml`:

```yaml
---
services:
  n8n_editor:
    environment:
      - N8N_METRICS=true
      - N8N_METRICS_INCLUDE_QUEUE_METRICS=true
      - N8N_METRICS_ENDPOINT=/metrics
      - QUEUE_HEALTH_CHECK_ACTIVE=true
  n8n_worker:
    environment:
      - N8N_METRICS=true
      - N8N_METRICS_INCLUDE_QUEUE_METRICS=true
      - N8N_METRICS_ENDPOINT=/metrics
      - QUEUE_HEALTH_CHECK_ACTIVE=true
  n8n_webhook:
    environment:
      - N8N_METRICS=true
      - N8N_METRICS_INCLUDE_QUEUE_METRICS=true
      - N8N_METRICS_ENDPOINT=/metrics
      - QUEUE_HEALTH_CHECK_ACTIVE=true
  n8n_mcp:
    environment:
      - N8N_METRICS=true
      - N8N_METRICS_INCLUDE_QUEUE_METRICS=true
      - N8N_METRICS_ENDPOINT=/metrics
      - QUEUE_HEALTH_CHECK_ACTIVE=true
```

---

## 3. Containers N8N (pós-restart)

```
n8n-n8n_mcp-1       Up About an hour
n8n-n8n_worker-1    Up About an hour
n8n-n8n_webhook-1   Up About an hour
n8n-n8n_editor-1    Up About an hour
```

---

## 4. AFTER Evidence

**Timestamp**: 2026-04-02T18:53:28Z
**Comando**: `python src/check_n8n_metrics.py --metrics-url https://testn8n.vya.digital`

```json
{
  "url": "https://testn8n.vya.digital",
  "status": "pass",
  "metrics_found": [
    "n8n_scaling_mode_queue_jobs_active",
    "n8n_scaling_mode_queue_jobs_waiting",
    "n8n_scaling_mode_queue_jobs_completed",
    "n8n_scaling_mode_queue_jobs_failed"
  ],
  "metrics_missing": [],
  "raw_count": 43,
  "checked_at": "2026-04-02T18:53:28.917324+00:00",
  "error": null
}
```

---

## 5. Bugs Corrigidos Nesta Execução (B7–B13)

| Bug | Arquivo | Problema | Correção |
|-----|---------|---------|---------|
| B7  | `docker-compose.override.j2` | Service `n8n` inexistente em wfdb01 | Loop `n8n_services` configurável |
| B8  | `f16_queue_metrics.yml` | `become_user: docker_user` → ACL error | `become_user: root`, `mode: 0644` |
| B9  | `f16_queue_metrics.yml` | Restart de `n8n` (serviço inexistente) | `n8n_services \| join(' ')` |
| B10 | `playbooks/f16-queue-metrics.yml` | SPA stanza `wfdb01.vya.digital` → not found | → `wfdb01` |
| B11 | `playbooks/f17-postgres-tuning.yml` | Mesma stanza errada | → `wfdb02`/`wfdb01` |
| B12 | `playbooks/f18-dual-collection-audit.yml` | Mesma stanza errada | → `wfdb01` |
| B13 | `hosts.yml` | `ansible_user: docker_user` → auth fail | → `archaris` |

## 6. Infraestrutura Descoberta

- **VictoriaMetrics**: porta 8428 NÃO publicada ao host; acesso interno via `http://victoriametrics:8428` (rede Docker). Prometheus scrape de N8N apenas para wf001 (31.220.103.208:5001), NÃO para wfdb01.
- Argumento `vm_url` em `group_vars/wfdb01.yml` corrigido: `http://victoriametrics:8428` (nome DNS Docker)
- **`collect_gate_evidence.py`**: não funciona para wfdb01 pois VM não tem dados de N8N wfdb01

## 7. Critério de Aceite

- [x] BEFORE: todas as 4 métricas de fila presentes (status: pass)
- [x] Playbook F16 aplicado sem erros (changed=2, failed=0)
- [x] docker-compose.override.yml criado em wfdb01
- [x] Containers N8N reiniciados com sucesso
- [x] AFTER: todas as 4 métricas de fila presentes (status: pass)
- [x] Endpoint HTTPS `https://testn8n.vya.digital/metrics` ativo

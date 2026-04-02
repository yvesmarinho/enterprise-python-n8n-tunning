# Contract: Change Request — prod-collector-api / Desabilitação do Pushgateway

**Gerado por**: Feature F18 — Documentação de Dupla Coleta e Change Request
**Projeto destinatário**: projeto responsável pelo `prod-collector-api`
**Gerado em**: _preencher na execução_
**Referência ANA-001**: dupla coleta confirmada ativa em wf001 e wfdb01

---

## Contexto

O diagnóstico ANA-001 confirmou que métricas do N8N são coletadas por dois
mecanismos simultâneos em `wf001` (e replicado no ambiente de teste `wfdb01`):

1. **Scrape direto**: VictoriaMetrics faz scrape de `wf001:5001/metrics`
2. **Pushgateway**: `prod-collector-api` envia métricas via push para o
   Pushgateway, que por sua vez é scrapado pelo VictoriaMetrics

Isso resulta em séries duplicadas com labels distintos, invalidando contagens
de throughput e alertas baseados em execuções.

---

## Diagnóstico — Resultados da Inspeção (`F18-PASSO-1`)

> **Preencher com dados coletados na execução:**

| Campo | Valor |
|-------|-------|
| Servidor inspecionado | `wfdb01` / `wf001` |
| Comando de inspeção | `docker inspect prod-collector-api \| grep -i pushgateway` |
| Variável de controle encontrada | _`PROMETHEUS_PUSHGATEWAY_ENABLED` — confirmar nome exato_ |
| Valor atual | `true` |
| Data da inspeção | _preencher_ |

---

## Evidência PromQL (`F18-PASSO-2`)

```promql
# Query confirmatória — retorna séries do Pushgateway:
{instance=~".*0\\.0\\.0\\.0.*", job="pushgateway"}

# Magnitude da dupla contagem:
# n8n_workflow_executions_total via pushgateway vs scrape direto
```

| Métrica | Origem | Magnitude |
|---------|--------|-----------|
| `n8n_workflow_executions_total` | Pushgateway (`0.0.0.0:5000`) | _preencher_ |
| `n8n_workflow_executions_total` | Scrape direto (`wf001:5001`) | _preencher_ |
| **Delta (%)** | — | _preencher_ |

> Relatório completo em: `docs/SESSIONS/YYYY-MM-DD/f18-dual-collection-report.json`

---

## Mudança Solicitada

**Serviço**: `prod-collector-api`
**Ação**: Desabilitar o envio de métricas para o Pushgateway
**Mecanismo**: Alterar a variável de controle identificada no Passo 1

### Configuração Atual (a modificar pelo projeto responsável)

```yaml
# docker-compose.override.yml do prod-collector-api
# (diretório provável: /opt/docker_user/prod-collector-api/)
services:
  prod-collector-api:
    environment:
      - PROMETHEUS_PUSHGATEWAY_ENABLED=true   # ← ALTERAR para false
      - PROMETHEUS_PUSHGATEWAY_URL=http://pushgateway:9091
```

### Configuração Solicitada

```yaml
services:
  prod-collector-api:
    environment:
      - PROMETHEUS_PUSHGATEWAY_ENABLED=false  # ← DESABILITAR
      - PROMETHEUS_PUSHGATEWAY_URL=http://pushgateway:9091  # manter (sem efeito)
```

> ⚠️ **Nota**: O nome exato da variável (`PROMETHEUS_PUSHGATEWAY_ENABLED`) deve
> ser confirmado com o valor obtido na inspeção remota (Passo 1). Se o nome
> for diferente, usar o nome correto identificado.

---

## Critérios de Aceite (Validação pós-mudança — ProvenanceGate)

Após aplicação pelo projeto responsável, este projeto executará:

```bash
python src/validate_prometheus.py \
  --vm-url http://<victoria_metrics_url>:8428 \
  --mode provenance-gate \
  --lookback 1h
```

**Critério 1 — Ausência de Pushgateway (SC-006)**:
```promql
absent_over_time({instance=~".*0\\.0\\.0\\.0.*", job="pushgateway"}[1h])
# Deve retornar resultado (confirma 1h sem novos pontos)
```
✅ Esperado: `PROVENANCE_OK`

**Critério 2 — Coerência de contagens (SC-007)**:
- `n8n_workflow_executions_total` (VictoriaMetrics) vs `COUNT(*) FROM execution_entity` (banco `n8n_db`)
- Delta ≤ 1% confirmado

---

## Impacto da Mudança

| Aspecto | Impacto |
|---------|---------|
| N8N workflows | Nenhum — apenas coleta de métricas afetada |
| Dashboards | Contagens normalizadas (remover deduplicação manual se existente) |
| Alertas | Revisar thresholds após normalização |
| Pushgateway | Serviço permanece ativo; apenas `prod-collector-api` para de enviar |

---

## Regra de Promoção (P1 Block)

Esta mudança **deve ser aplicada e validada em `wfdb01`** antes de qualquer
promoção para `wf001`. A promoção de F16, F17 e F18 para `wf001` ocorre em
**bloco** — todas as três features devem ter gate aprovado simultaneamente.

Referência: `specs/001-001-tunning-instrumentacao/spec.md` → FR-010, FR-011

---

## Contato / Rastreabilidade

| Campo | Valor |
|-------|-------|
| Feature de origem | F18 — `001-001-tunning-instrumentacao` |
| Branch | `001-001-tunning-instrumentacao` |
| Spec | `specs/001-001-tunning-instrumentacao/spec.md` |
| Research | `specs/001-001-tunning-instrumentacao/research.md` → R-004 |
| Solicitante | _preencher_ |
| Data de submissão | _preencher_ |

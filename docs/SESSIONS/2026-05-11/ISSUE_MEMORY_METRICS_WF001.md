# Issue: Corrigir Métricas de Memória Vazias para wf001

**Projeto**: enterprise-observability
**Repositório**: git@github.com:admin-vya-digital/enterprise-observability.git
**Tipo**: Bug Fix
**Prioridade**: P1 — Alta (gap de observabilidade)
**Labels**: monitoring, node-exporter, prometheus, wf001, memory

---

## 📋 Contexto

O servidor **wf001.vya.digital** (31.220.103.208) hospeda o N8N em produção. Atualmente, **métricas de memória retornam vazias** no VictoriaMetrics, enquanto **métricas de CPU funcionam corretamente**.

**Projeto relacionado**: `enterprise-python-n8n-tunning` — Feature F23 (Correção do monitoramento de memória do servidor wf001)

---

## 🎯 Objetivo

Corrigir coleta de métricas de memória (`node_memory_*`) para wf001 no Prometheus/VictoriaMetrics.

---

## 📊 Justificativa

### Problema Atual

**Evidências do ANA-001** (relatório de performance 2026-01-01 a 2026-03-31):
- ✅ **CPU wf001**: Dados corretos (baseline 1-3%)
- ❌ **Memória wf001**: `node_memory_MemAvailable_bytes{instance='wf001'}` retorna **vazio**
- ❌ **Memória swap**: `node_memory_SwapFree_bytes{instance='wf001'}` retorna **vazio**

**Hipótese identificada no ANA-001**:
> "Label `instance` incorreto no relabeling do scrape config Prometheus para node_exporter de wf001"

### Impacto

- 🔴 **Gap crítico de observabilidade**: Impossível diagnosticar problemas de memória em produção
- 🔴 **Alertas inoperantes**: Alertas de memória alta/swap não funcionam para wf001
- 🔴 **Dashboards incompletos**: Painéis de infra mostram apenas CPU (sem memória)
- ⚠️ **Análise de performance limitada**: Não é possível correlacionar uso de memória com latência N8N

---

## 🛠️ Solução Proposta

### 1. Validar Node Exporter em wf001

**Verificar se node_exporter está ativo**:
```bash
# SSH em wf001
ssh -p 5010 archaris@31.220.103.208

# Verificar container/serviço node_exporter
docker ps | grep node-exporter
# OU
systemctl status node_exporter
```

**Verificar métricas localmente**:
```bash
curl http://localhost:9100/metrics | grep node_memory_MemAvailable_bytes
```

**Resultado esperado**: Métrica deve retornar valor numérico (exemplo: `node_memory_MemAvailable_bytes 8234567890`)

---

### 2. Verificar Scrape Config do Prometheus

**Arquivo**: `prometheus.yml` (ou arquivo de configuração do enterprise-observability)

**Problema provável** — relabeling incorreto:
```yaml
scrape_configs:
  - job_name: 'node-exporter'
    static_configs:
      - targets: ['wf001.vya.digital:9100']
    relabel_configs:
      - source_labels: [__address__]
        target_label: instance
        replacement: 'wf001'  # ← Verificar se está correto
```

**Validações**:
1. Target `wf001.vya.digital:9100` está acessível do Prometheus?
2. Label `instance` está sendo aplicado corretamente?
3. Existe duplicação de scrape jobs para wf001?

---

### 3. Validar Targets no Prometheus

**Query no Prometheus UI** (http://wfdb01:9090):
```
Go to: Status → Targets
Buscar: job="node-exporter", instance="wf001"
Verificar: Estado UP ou DOWN
```

**Queries de diagnóstico**:
```promql
# Verificar se target está sendo raspado
up{instance="wf001",job="node-exporter"}

# Verificar todas as métricas node_* de wf001
{instance="wf001",job="node-exporter"}

# Verificar especificamente memória
node_memory_MemAvailable_bytes{instance="wf001"}
```

---

### 4. Possíveis Causas e Soluções

| Causa | Solução |
|-------|---------|
| Node exporter não instalado em wf001 | Instalar via docker ou systemd |
| Porta 9100 bloqueada (UFW) | `ufw allow from <prometheus_ip> to any port 9100` |
| Relabeling incorreto no scrape_config | Corrigir `target_label: instance` |
| Scrape job duplicado com label diferente | Consolidar em único job |
| Node exporter versão antiga (sem métricas de memória) | Atualizar para versão recente |

---

### 5. Correção Esperada

**Antes**:
```promql
node_memory_MemAvailable_bytes{instance="wf001"}
# Resultado: (empty)
```

**Depois**:
```promql
node_memory_MemAvailable_bytes{instance="wf001"}
# Resultado: node_memory_MemAvailable_bytes{instance="wf001",job="node-exporter"} 8234567890
```

---

## 📦 Artefatos de Referência

**Evidências do problema**:
- Relatório ANA-001: `enterprise-python-n8n-tunning/docs/n8n_perf_ANA001_20260101_20260331_20260331T154646.md`
- Feature F23: `enterprise-python-n8n-tunning/docs/objetivo.yaml` (features_implemented.F23)
- Análise de conformidade: `enterprise-python-n8n-tunning/docs/SESSIONS/2026-05-11/COMPLIANCE_ANALYSIS_REPORT_2026-05-11.md`

**Queries de validação pós-correção**:
```promql
# Memória disponível
node_memory_MemAvailable_bytes{instance="wf001"}

# Memória total
node_memory_MemTotal_bytes{instance="wf001"}

# Uso de memória (%)
100 - (node_memory_MemAvailable_bytes{instance="wf001"} / node_memory_MemTotal_bytes{instance="wf001"} * 100)

# Swap livre
node_memory_SwapFree_bytes{instance="wf001"}
```

---

## ⏱️ Estimativa

- **Diagnóstico**: 15 minutos
- **Correção**: 10 minutos (dependendo da causa)
- **Validação**: 10 minutos
- **Documentação**: 5 minutos
- **Total**: ~40 minutos

---

## 🚨 Impacto e Riscos

### Impacto

- **Baixo**: Correção não afeta funcionamento do servidor
- **Observabilidade**: Restaura visibilidade crítica de memória

### Riscos

- 🟢 **Zero downtime**: Correção no Prometheus não requer restart do wf001
- 🟢 **Rollback**: Reverter mudanças no prometheus.yml (< 2 min)
- 🟡 **Restart Prometheus**: Requer reload do Prometheus (sem perda de dados)

---

## 📅 Dependências

- **Bloqueia**: F23 (Correção do monitoramento de memória do servidor wf001)
- **Relacionado**: T034a (baseline de métricas pré-promoção F16+F17)

---

## 📝 Critérios de Aceite

- [ ] Query `node_memory_MemAvailable_bytes{instance="wf001"}` retorna valor numérico
- [ ] Query `node_memory_SwapFree_bytes{instance="wf001"}` retorna valor numérico
- [ ] Dashboard de memória wf001 funcional no Grafana
- [ ] Alertas de memória alta configurados e testados
- [ ] Target `node-exporter | wf001` em estado UP no Prometheus
- [ ] Documentação atualizada em enterprise-observability

---

## 👥 Stakeholders

- **Solicitante**: enterprise-python-n8n-tunning (performance-analyst)
- **Owner**: enterprise-observability (devops-engineer)
- **Impactado**: Equipe de operações (visibilidade de memória restaurada)

---

## 🔗 Referências

- ANA-001: Análise de Performance N8N (2026-01-01 a 2026-03-31)
- Feature F23: Correção do monitoramento de memória do servidor wf001
- Baseline pré-T034a: `enterprise-python-n8n-tunning/scripts/tmp/baseline_metrics_pre_t034a_20260511_101240.json`

---

## 📊 Contexto Adicional

**CPU funciona, memória não** — indica que:
1. Node exporter está ativo (senão CPU também estaria vazio)
2. Problema é de relabeling ou scrape config específico de métricas
3. Possível filtro/exclusão inadvertido de métricas `node_memory_*`

**Prioridade P1** porque:
- Servidor de produção crítico (N8N com 429K+ execuções/90d)
- Gap de observabilidade pode mascarar problemas de memória
- Baseline de T034a está incompleto sem dados de memória

---

*Issue gerada em 2026-05-11 pelo projeto enterprise-python-n8n-tunning*
*Contato: performance-analyst | devops-engineer*

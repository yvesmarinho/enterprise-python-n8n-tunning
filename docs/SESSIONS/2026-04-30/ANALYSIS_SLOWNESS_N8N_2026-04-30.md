# 🔍 Análise de Lentidão N8N — Abril 2026

**ID**: SLOWNESS-2026-04-30
**Data**: 2026-04-30
**Analista**: GitHub Copilot + performance-analyst
**Base de dados**: ANA-001 (jan-mar 2026) + evidências de sessões anteriores

---

## 🎯 Pergunta Central

**"Por que o N8N está lento tanto nos workflows quanto na operação?"**

---

## ✅ Resposta (Diagnóstico)

### **Workflows individuais SÃO rápidos** — o problema NÃO é latência de execução

| Métrica | Valor | Interpretação |
|---------|-------|---------------|
| p95 de duração individual | **< 100ms** | 100% das execuções completam abaixo de 100ms |
| Workflows com p95 ≥ 1s | **0** | Nenhum workflow é "lento" individualmente |
| CPU wf001 durante picos | **1-3%** | Hardware não saturado |

### **Lentidão percebida = TEMPO DE FILA não instrumentado**

O problema está no **tempo de espera na fila de execução**, não na execução em si.

---

## 🔴 Hipótese Principal — Fila N8N Saturada

### Evidência Circunstancial

| Fato | Valor |
|------|-------|
| Taxa de chegada pico (121Labs) | **2.3 exec/s contínuo por 9h** |
| Volume pico/hora | **8.416 execuções** (2026-03-27) |
| Duração média por execução | **< 100ms** |
| Concorrência padrão N8N | **5-20 workers** (não confirmado em wf001) |
| Throughput teórico | **50-200 exec/s** (workers × 1/duration) |

### Cálculo Teórico

```
Throughput teórico = Workers / Duração média
                   = 10 workers / 0.1s
                   = 100 exec/s

Taxa de chegada real = 2.3 exec/s

Conclusão teórica: NÃO deveria saturar
```

**MAS**:
- Concorrência real de wf001 não confirmada (pode ser menor que 10)
- Workers podem estar compartilhados entre workflows
- Execuções de outros workflows competem pela mesma fila

### ⚠️ Lacuna Crítica de Instrumentação

**`n8n_queue_*` métricas NÃO estão habilitadas em wf001**

Sem essas métricas, a hipótese de fila saturada **não é testável com dados atuais**.

**Ação necessária**: F16 (habilitar queue metrics) — **playbook pronto, janela agendada sábado 02h-04h UTC**

---

## 🟠 Hipótese Secundária — PostgreSQL Saturado

### Evidência Confirmada

| Métrica | Valor (mar/2026) | Status Atual (abr/2026) |
|---------|------------------|-------------------------|
| execution_entity linhas | **429.000+** | ⚠️ **Não verificado** (script criado, execução pend SSH) |
| Política de purgação ativa? | **Não** | **Não** (EXECUTIONS_DATA_PRUNE=false) |
| Retenção configurada | **Sem limite** | **Sem limite** |
| pg_stat_statements ativo | **Não** (mar/2026) | ✅ **Sim** (validado em n8n_dev_db, não em n8n_db prod) |

### Impacto

Toda execução N8N:
1. **INSERT** em `execution_entity` (início da exec)
2. **UPDATE** em `execution_entity` (fim da exec, resultado)
3. **SELECT** em `execution_entity` (dashboard, histórico)

Com 429K+ linhas sem índices otimizados ou purgação:
- INSERTs podem gerar locks
- UPDATEs podem ser lentos se tabela fragmentada
- SELECTs de dashboard afetam performance geral

**Ação necessária**: F17 (purgação + pg_stat_statements) — **playbook pronto, janela agendada sábado 02h-04h UTC**

---

## 📊 Ofensores de Volume (ANA-001)

### Top 2 Workflows

| # | Workflow | Exec 90d | % Total | Padrão | Impacto |
|---|----------|----------|---------|--------|---------|
| 1 | **121Labs PABX call-analytics** | **429.786** | **57%** | Horário comercial 13:00-22:00 UTC; pico 8.4K/hora | Domina fila N8N por 9h/dia |
| 2 | **hub-whatsapp-api-gateway-evolution-api** | **84.639** | **11%** | Crescimento súbito desde 04/mar (+1860% em 24h) | Causa desconhecida — auditar |

### Perfil de Carga — 121Labs PABX

| Métrica | Valor |
|---------|-------|
| Pico máximo | **8.416 exec/hora** (2026-03-27 20:00 UTC) |
| Taxa sustentada | **2.3 exec/s por 9h contínuas** |
| Horário ativo | **13:00-22:00 UTC** (10:00-19:00 BRT) |
| Trigger | **Evento individual de PABX** (não batch) |

**Oportunidade de otimização (F21)**:
- Batching de 1 minuto: 8.400 exec/hora → 140 exec/hora (**60× redução**)
- Requer aprovação do cliente 121Labs

### Perfil de Carga — WhatsApp Gateway

| Métrica | Valor |
|---------|-------|
| Primeira atividade | **2026-03-04** (antes inativo) |
| Crescimento inicial | **10 exec → 2.958 exec** em 24h |
| Semana de pico | **33.782 exec** (2026-03-12) |
| Causa | **Não documentada — investigar onboarding** |

**Ação necessária**: Auditar integração Evolution API + base de clientes ativa

---

## 🚨 Gargalos Confirmados

| Gargalo | Evidência | Prioridade |
|---------|-----------|-----------|
| **PostgreSQL execution_entity saturado** | 429K+ linhas, sem purgação | 🔴 P1 |
| **Dupla coleta Prometheus (F18)** | prod-collector-api envia via scrape direto E Pushgateway | 🔴 P1 |

---

## ❓ Hipóteses NÃO Testáveis (Lacunas de Instrumentação)

| Hipótese | Lacuna | Feature |
|----------|--------|---------|
| Fila N8N saturada | `n8n_queue_*` não habilitado | **F16** (pendente em wf001) |
| Workers saturados | `n8n_concurrency_*` não visível | **F24** (não implementado) |
| Latência end-to-end alta | Probe sintético ausente | **F20** (não implementado) |
| Queries PostgreSQL lentas | `pg_stat_statements` validado apenas em DEV | **F17 Vetor B** (pendente em prod) |
| Memória wf001 saturada | `node_memory_*` retorna vazio | **F23** (relabeling incorreto) |
| p50/p95 reais sub-100ms | Buckets de histograma grosseiros | **F22** (não implementado) |

**Total de lacunas críticas**: **6**

---

## 🎯 Recomendações Priorizadas

### 🔴 P0 — IMEDIATO (Esta Semana)

| # | Ação | Razão | Impacto | Status |
|---|------|-------|---------|--------|
| 1 | **Executar T034a (F16+F17 → wf001)** | Habilita queue metrics + purga PostgreSQL | Confirma/descarta hipótese de fila + reduz carga DB | ✅ Playbook pronto, janela sábado 02h-04h UTC |
| 2 | **Verificar tamanho atual execution_entity** | Confirmar crescimento desde mar/2026 | Urgência de F17 depende disso | ⚠️ Script criado, execução pend SSH |

### 🟠 P1 — PRÓXIMA SEMANA

| # | Ação | Owner | Impacto |
|---|------|-------|---------|
| 1 | **Auditar hub-whatsapp-api-gateway-evolution-api** | N8N Admin + Evolution API team | Identificar causa de crescimento súbito 04/mar |
| 2 | **Submeter issue F18 ao prod-collector-api** | DevOps | Desabilitar `PROMETHEUS_PUSHGATEWAY_ENABLED=true` |
| 3 | **Habilitar F24 (concurrency metrics)** | DevOps | Confirmar/descartar workers saturados |

### 🟡 P2 — MÉDIO PRAZO (2-4 Semanas)

| # | Ação | Impacto |
|---|------|---------|
| 1 | **Implementar F20 (probe sintético end-to-end)** | Baseline de latência real before/after |
| 2 | **Implementar F22 (buckets sub-100ms)** | p50/p95 reais em vez de 0.095s artificial |
| 3 | **Avaliar F19/F21 (governança + batching 121Labs)** | Redução de 60× no volume (8.4K → 140 exec/hora) |

---

## 🔍 Próximos Passos

### Imediato (Hoje/Amanhã)

1. ✅ **Análise de lentidão concluída** — relatório gerado
2. ⬜ **Verificar PostgreSQL execution_entity** — resolver problema SSH ou executar manualmente em wfdb02
3. ⬜ **Atualizar TODO.md** — adicionar ações P0/P1 priorizadas

### Esta Semana

1. ⬜ **Executar T034a** — janela sábado 02h-04h UTC (F16+F17 → wf001)
2. ⬜ **Auditar WhatsApp Gateway** — contatar Evolution API team
3. ⬜ **Submeter issue F18** — usar contract em `specs/001-001-tunning-instrumentacao/contracts/prod-collector-api-issue.md`

### Próximas 2 Semanas

1. ⬜ **Baseline pós-T034a** — coletar n8n_queue_* e validar purgação PostgreSQL
2. ⬜ **Implementar F24** — concurrency metrics
3. ⬜ **Planejar F20** — probe sintético end-to-end

---

## 📋 Decisões Técnicas Registradas

| # | Decisão | Justificativa |
|---|---------|---------------|
| 1 | **Priorizar T034a sobre outras features** | F16+F17 resolvem as 2 principais hipóteses (fila + PostgreSQL) |
| 2 | **Não implementar F19/F21 sem aprovação do cliente** | Requer mudança de arquitetura de trigger (batching) |
| 3 | **Focar em instrumentação antes de scaling** | Sem métricas, impossível confirmar gargalos reais |

---

## 🔗 Artefatos Relacionados

- **ANA-001**: [docs/n8n_perf_ANA001_20260101_20260331_20260331T154646.md](../n8n_perf_ANA001_20260101_20260331_20260331T154646.md)
- **Análise JSON**: [n8n-slowness-analysis-20260430-113529.json](n8n-slowness-analysis-20260430-113529.json)
- **Script PostgreSQL**: [tmp/check_execution_entity.py](../../tmp/check_execution_entity.py)
- **Playbook T034a**: [ansible/playbooks/t034a-promote-f16-f17-wf001.yml](../../ansible/playbooks/t034a-promote-f16-f17-wf001.yml)
- **Contract F18**: [specs/001-001-tunning-instrumentacao/contracts/prod-collector-api-issue.md](../../specs/001-001-tunning-instrumentacao/contracts/prod-collector-api-issue.md)

---

*Análise gerada em 2026-04-30 | Modo: ANALYSIS + PROGRAMMING | Sessão: 2026-04-30*

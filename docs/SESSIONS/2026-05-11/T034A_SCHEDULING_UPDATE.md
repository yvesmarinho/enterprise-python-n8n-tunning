# T034a — Agendamento de Janela de Manutenção

**Data**: 2026-05-11
**Decisão**: Aprovação de janela de manutenção para promoção F16+F17 para wf001
**Aprovado por**: project-manager

---

## 🗓️ Janela Aprovada

| Item | Detalhe |
|------|---------|
| **Data** | 2026-05-17 (sábado) |
| **Horário BRT** | 15h00 às 19h00 (4 horas) |
| **Horário UTC** | 18h00 às 22h00 (4 horas) |
| **Duração Estimada** | 25-30 minutos de execução efetiva |
| **Margem de Segurança** | ~3h30 para rollback/troubleshooting |

---

## 📋 Checklist Atualizado

| # | Item | Owner | Deadline | Status |
|---|------|-------|----------|--------|
| 1 | Fix Prometheus DOWN wf001 | devops-engineer | 2026-05-11 | ✅ CONCLUÍDO |
| 2 | Coletar baseline métricas wf001 | performance-analyst | 2026-05-11 | ✅ CONCLUÍDO |
| 3 | Obter aprovação project-manager | project-manager | 2026-05-11 | ✅ CONCLUÍDO |
| 4 | Notificar stakeholders (121Labs, WhatsApp) | project-manager | 2026-05-15 | 🔵 Pendente (48h antes) |
| 5 | Executar backup PostgreSQL `n8n_db` | databases-engineer | 2026-05-16 | 🔵 Pendente (24h antes) |
| 6 | Dry-run final T034a | devops-engineer | 2026-05-16 | 🔵 Pendente (24h antes) |

---

## 🎯 Escopo da Janela

### Features a Promover (wfdb01 → wf001)

| ID | Feature | Artefato | Validação Requerida |
|----|---------|----------|---------------------|
| F16 | Queue Metrics (RabbitMQ) | `f16-queue-metrics.yml` | ❌ **BLOQUEADOR**: RabbitMQ exporter não instalado |
| F17 | PostgreSQL Tuning | `f17-postgres-tuning.yml` | ✅ Pronto |

### Dependências Externas

1. **RabbitMQ Exporter (F16)** — 🔴 CRÍTICO
   - Issue: [#1 - RabbitMQ Exporter](https://github.com/yvesmarinho/enterprise-observability/issues/1)
   - Repositório: `yvesmarinho/enterprise-observability`
   - Estimativa: 40 minutos
   - Prioridade: P1 — Alta
   - **Status**: Issue submetida (2026-05-11), aguardando implementação
   - **Impacto**: F16 NÃO pode ser promovido sem RabbitMQ exporter ativo

2. **Memory Metrics wf001** — 🟡 Importante (não bloqueia T034a)
   - Issue: [#2 - Memory Metrics](https://github.com/yvesmarinho/enterprise-observability/issues/2)
   - Repositório: `yvesmarinho/enterprise-observability`
   - Estimativa: 40 minutos
   - Prioridade: P1 — Alta
   - **Status**: Issue submetida (2026-05-11), aguardando implementação
   - **Impacto**: Bloqueia F23, baseline incompleto (métrica 7 sem valor)

---

## 📊 Estado Atual (2026-05-11 10:25 UTC)

### ✅ Pré-requisitos Completos

- [x] Prometheus wf001 operacional (T034)
- [x] Baseline métricas coletado (`baseline_metrics_pre_t034a_20260511_101240.json`)
- [x] Aprovação project-manager obtida
- [x] Playbooks Ansible testados em wfdb01
- [x] Critérios de validação pós-promoção definidos

### 🔴 Bloqueadores

- [ ] **RabbitMQ Exporter não instalado em wf001**
  - F16 Queue Metrics **depende** de `kbudde/rabbitmq-exporter:v0.29.0`
  - Scrape endpoint: `http://wf001.vya.digital:9419/metrics`
  - Usuário RabbitMQ necessário: `dialer` (tag `monitoring`)
  - **Ação**: Aguardar implementação da issue em `enterprise-observability`

### 🟡 Gaps Não-Bloqueadores

- [ ] **Memory Metrics wf001 vazias**
  - `node_memory_*` retorna vazio (relabeling incorreto)
  - Não impacta F16 ou F17
  - Bloqueia F23 (Memory Usage Alerts)
  - **Ação**: Aguardar implementação da issue em `enterprise-observability`

---

## 📋 Timeline de Execução

| Deadline | Tarefa | Owner |
|----------|--------|-------|
| **2026-05-15 10h UTC** | Notificar stakeholders (48h antes) | project-manager |
| **2026-05-16 10h UTC** | Executar backup PostgreSQL `n8n_db` | databases-engineer |
| **2026-05-16 14h UTC** | Dry-run final T034a em ambiente de teste | devops-engineer |
| **2026-05-17 18h UTC** | ⏰ **INÍCIO JANELA** — Execução T034a | devops-engineer |
| **2026-05-17 18h30 UTC** | Validação pós-promoção (critérios baseline) | performance-analyst |
| **2026-05-17 19h00 UTC** | Rollback deadline (se necessário) | devops-engineer |
| **2026-05-17 22h UTC** | ⏰ **FIM JANELA** | - |

---

## ⚠️ Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| RabbitMQ exporter não pronto | Média | Alto | Priorizar issue em `enterprise-observability`, notificar urgência |
| Latência PostgreSQL sobe >50% | Baixa | Médio | Rollback planejado, backup 24h antes |
| Workflows críticos falham | Baixa | Alto | Dry-run 24h antes, lista de workflows críticos validados |
| Janela de 4h insuficiente | Muito Baixa | Médio | Execução estimada: 25-30 min (margem 8x) |

---

## 📞 Stakeholders a Notificar (Item #4)

1. **121Labs** — Cliente PABX
   - Workflows afetados: `121labs-pabx-webhook-processor` (429K execuções em 90 dias)
   - Impacto esperado: Downtime 5-10 min durante restart N8N
   - Contato: [TBD — project-manager informará]

2. **WhatsApp Gateway Team**
   - Workflows afetados: `hub-whatsapp-api-gateway-evolution-api` (84K execuções em 90 dias)
   - Impacto esperado: Downtime 5-10 min durante restart N8N
   - Contato: [TBD — project-manager informará]

3. **Equipe de Observabilidade**
   - Workflows afetados: Nenhum (apenas coleta de métricas)
   - Impacto esperado: Nenhum
   - **Ação**: Enviar issues RabbitMQ + Memory Metrics com prioridade P1

---

## 🔄 Plano de Rollback

### Trigger de Rollback

Rollback **OBRIGATÓRIO** se qualquer condição:

1. Latência p95 > 800ms (baseline: 450ms, tolerância: +50%)
2. Taxa de erro > 2% (baseline: 0.8%, tolerância: +150%)
3. Workflows críticos (121Labs PABX, WhatsApp Gateway) falhando
4. PostgreSQL connections > 80 (baseline: 45, tolerância: +77%)
5. RabbitMQ queue > 20 mensagens por 10 minutos (baseline: 3)

### Procedimento de Rollback

```bash
# 1. SSH em wf001 (com SPA knock)
make ssh-spa-knock-one HOST=wf001

# 2. Reverter variáveis de ambiente N8N
cd /opt/docker_user/n8n
git diff .env  # revisar mudanças F16+F17
git checkout HEAD~1 .env

# 3. Restart N8N
docker compose restart n8n

# 4. Validar recuperação
watch -n 5 'curl -s http://localhost:5678/healthz'

# 5. Confirmar métricas baseline
# (executar script de validação)
```

**Tempo estimado de rollback**: 5-8 minutos

---

## 📝 Notas

- **Janela original**: 2026-05-10 02h-04h UTC (passou sem execução)
- **Motivo reagendamento**: Bloqueador RabbitMQ exporter não resolvido a tempo
- **Progresso**: 3/6 itens do checklist concluídos (50%)
- **Próxima sessão**: Acompanhar implementação das issues no `enterprise-observability`

---

**Gerado em**: 2026-05-11T10:25:00Z
**Responsável**: project-manager
**Status**: ✅ Aprovado e documentado

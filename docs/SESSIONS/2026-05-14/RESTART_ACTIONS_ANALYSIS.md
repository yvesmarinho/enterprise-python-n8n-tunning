# 🔄 Análise de Ações de Restart — T034a

**Gerado em**: 2026-05-14T10:24:00Z
**Objetivo**: Identificar ações de restart que podem ser executadas FORA da janela de produção (2026-05-17 15h-19h BRT)
**Modo**: ANALYSIS
**Sessão**: 2026-05-14

---

## 🎯 Resumo Executivo

Das ações planejadas para T034a, **apenas 1 restart é obrigatório DURANTE a janela de produção** (N8N restart — 5-10 min downtime).

**Todas as demais ações de infraestrutura podem ser executadas ANTES da janela**, reduzindo o tempo efetivo de downtime e os riscos operacionais.

---

## ✅ Ações de Restart FORA DA JANELA DE PRODUÇÃO

### 1. Prometheus Reload (Issue #2 — Memory Metrics)

**Servidor**: wfdb01.vya.digital (observabilidade)
**Serviço**: Prometheus
**Tipo**: `systemctl reload prometheus` ou `docker compose restart prometheus`
**Downtime**: Zero (reload graceful) ou ~5 segundos (restart)
**Impacto**: Nenhum (não afeta produção)

**Quando executar**: A qualquer momento, quando issue #2 for implementada

**Comandos**:
```bash
# SSH em wfdb01 (com SPA knock)
make ssh-spa-knock-one HOST=wfdb01
~/.local/bin/ssh-wfdb01

# Opção 1: Reload graceful (preferencial)
sudo systemctl reload prometheus

# Opção 2: Restart via Docker (se containerizado)
cd /opt/docker_user/observability
docker compose restart prometheus

# Validação
curl -s http://localhost:9090/-/healthy
# Verificar métricas de memória wf001
curl -s 'http://localhost:9090/api/v1/query?query=node_memory_MemAvailable_bytes{instance="wf001"}' | jq
```

**Critério de aceite**:
- Prometheus UP após reload
- Métricas `node_memory_*{instance="wf001"}` retornando valores

**Status**: 🔵 Aguardando implementação issue #2 (enterprise-observability)

---

### 2. RabbitMQ Exporter Deploy (Issue #1)

**Servidor**: wf001.vya.digital (PRODUÇÃO)
**Serviço**: rabbitmq-exporter (novo container)
**Tipo**: `docker compose up -d rabbitmq-exporter`
**Downtime**: Zero (deploy de novo serviço, não afeta N8N)
**Impacto**: Nenhum (apenas adiciona monitoramento)

**Quando executar**: Assim que issue #1 for implementada, **ANTES de 2026-05-16 10h UTC**

**Comandos**:
```bash
# SSH em wf001 (com SPA knock)
make ssh-spa-knock-one HOST=wf001
~/.local/bin/ssh-wf001

# Deploy do exporter (sem afetar N8N)
cd /opt/docker_user/rabbitmq  # ou caminho definido pelo enterprise-observability
docker compose up -d rabbitmq-exporter

# Validação
docker ps | grep rabbitmq-exporter
curl -s http://localhost:9419/metrics | grep rabbitmq_queue
```

**Critério de aceite**:
- Container `rabbitmq-exporter` UP
- Métricas `rabbitmq_queue_*` disponíveis em `:9419/metrics`
- Prometheus/VictoriaMetrics coletando métricas

**Status**: 🔴 BLOQUEADOR — aguardando implementação issue #1 (enterprise-observability)

**Criticidade**: ⚠️ **Se não implementado até 2026-05-16 10h UTC → T034a DEVE ser reagendada**

---

### 3. Usuário RabbitMQ 'dialer' (Issue #1 — pré-requisito)

**Servidor**: wf001.vya.digital (PRODUÇÃO)
**Serviço**: RabbitMQ (criação de usuário)
**Tipo**: `rabbitmqctl add_user` (operação administrativa, não afeta filas)
**Downtime**: Zero (não requer restart)
**Impacto**: Nenhum (apenas cria usuário read-only)

**Quando executar**: Junto com deploy do RabbitMQ exporter (issue #1)

**Comandos**:
```bash
# SSH em wf001
~/.local/bin/ssh-wf001

# Acessar container RabbitMQ
docker exec -it rabbitmq bash

# Criar usuário 'dialer' com tag monitoring
rabbitmqctl add_user dialer <senha_segura>
rabbitmqctl set_user_tags dialer monitoring
rabbitmqctl set_permissions -p / dialer "" "" ".*"

# Validação
rabbitmqctl list_users
# Esperado: dialer [monitoring]
```

**Critério de aceite**:
- Usuário `dialer` criado com tag `monitoring`
- Permissões read-only configuradas

**Status**: 🔵 Aguardando implementação issue #1

---

### 4. Node Exporter Validação em wf001 (Issue #2 — diagnóstico)

**Servidor**: wf001.vya.digital (PRODUÇÃO)
**Serviço**: node_exporter (validação, não restart)
**Tipo**: Verificação (leitura)
**Downtime**: Zero (apenas leitura)
**Impacto**: Nenhum

**Quando executar**: Ao diagnosticar issue #2 (pode ser feito imediatamente)

**Comandos**:
```bash
# SSH em wf001
~/.local/bin/ssh-wf001

# Verificar se node_exporter está ativo
docker ps | grep node-exporter
# OU
systemctl status node_exporter

# Verificar métricas localmente
curl -s http://localhost:9100/metrics | grep node_memory_MemAvailable_bytes
```

**Critério de aceite**:
- Node exporter UP
- Métricas `node_memory_*` disponíveis localmente (confirma que o problema é no Prometheus)

**Status**: ✅ Pode ser executado imediatamente (não afeta produção)

---

## 🔴 Ações de Restart DURANTE A JANELA DE PRODUÇÃO (OBRIGATÓRIAS)

### 5. N8N Restart (T034a — Aplicação F16+F17)

**Servidor**: wf001.vya.digital (PRODUÇÃO)
**Serviço**: N8N
**Tipo**: `docker compose restart n8n`
**Downtime**: ⚠️ **5-10 minutos**
**Impacto**: 🔴 **Alto — workflows param de processar durante restart**

**Quando executar**: **2026-05-17 15h10 BRT (18h10 UTC)** — SOMENTE durante janela de manutenção

**Por que DEVE ser na janela**:
1. Aplica mudanças críticas de `.env` (F16 queue metrics + F17 data prune)
2. Requer restart do container N8N para carregar novas variáveis
3. Causa downtime observável (webhooks retornam 503)
4. Stakeholders foram notificados sobre este horário específico

**Comandos**:
```bash
# SSH em wf001
~/.local/bin/ssh-wf001

# Aplicar mudanças .env via playbook Ansible
# (executado remotamente do workstation)
ansible-playbook ansible/playbooks/t034a-promote-f16-f17-wf001.yml \
  -i ansible/inventory/ -l wf001

# O playbook inclui automaticamente:
# 1. Backup .env atual
# 2. Aplicação de F16+F17 (alteração .env)
# 3. Restart N8N
# 4. Validação healthcheck

# Monitorar logs durante restart
docker compose -f /opt/docker_user/n8n/docker-compose.yml logs -f n8n
```

**Critério de aceite**:
- N8N UP após restart (<10 min)
- `/healthz` respondendo HTTP 200
- Métricas `n8n_queue_*` disponíveis (F16)
- Workflows críticos executando normalmente

**Duração estimada**: 25-30 minutos (incluindo validações)

**Status**: ⏰ Agendado para 2026-05-17 15h10 BRT

---

## 🟢 Ações de Restart PÓS-JANELA (Nenhuma Identificada)

Nenhuma ação de restart de serviço é necessária APÓS a janela T034a.

**Validações pós-janela** (sem restart):
- Coleta de métricas pós-promoção (leitura)
- Testes de workflows críticos (webhooks)
- Monitoramento de performance 24h (observação)

---

## 📊 Matriz de Decisão — Quando Fazer Cada Restart

| # | Ação | Servidor | Downtime | Pode ser ANTES? | Pode ser DURANTE? | Pode ser DEPOIS? | Status Atual |
|---|------|----------|----------|-----------------|-------------------|------------------|--------------|
| 1 | Prometheus reload (issue #2) | wfdb01 | 0-5s | ✅ SIM (preferencial) | ✅ SIM | ✅ SIM | 🔵 Aguardando issue #2 |
| 2 | RabbitMQ exporter deploy (issue #1) | wf001 | 0s | ✅ SIM (obrigatório) | ❌ Não recomendado | ❌ Tarde demais | 🔴 Aguardando issue #1 (BLOQUEADOR) |
| 3 | Usuário RabbitMQ 'dialer' | wf001 | 0s | ✅ SIM (junto c/ #2) | ❌ Não recomendado | ❌ Tarde demais | 🔵 Aguardando issue #1 |
| 4 | Node exporter validação | wf001 | 0s | ✅ SIM (diagnóstico) | ✅ SIM | ✅ SIM | ✅ Pode executar agora |
| 5 | N8N restart | wf001 | 5-10 min | ❌ NÃO (causa downtime) | ✅ SIM (OBRIGATÓRIO) | ❌ Fora da janela | ⏰ Agendado 2026-05-17 15h10 BRT |

---

## 🎯 Recomendações

### Prioridade P0 (Antes de 2026-05-16)

1. **Escalar issue #1** (RabbitMQ exporter) para implementação urgente
   - Deadline crítico: 2026-05-16 10h UTC
   - Se não implementado → T034a DEVE ser reagendada

2. **Executar deploy RabbitMQ exporter** assim que issue #1 for resolvida
   - Validar métricas `rabbitmq_queue_*` antes do dry-run final (T043)

3. **Validar node_exporter em wf001** (issue #2 diagnóstico)
   - Pode ser feito imediatamente (hoje, 2026-05-14)
   - Confirma se problema é no Prometheus ou no exporter

### Prioridade P1 (Antes de 2026-05-17)

4. **Prometheus reload** (quando issue #2 for corrigida)
   - Executar em wfdb01 assim que correção estiver pronta
   - Validar métricas `node_memory_*{instance="wf001"}` funcionando

### Prioridade P2 (Durante janela 2026-05-17)

5. **N8N restart** — ÚNICA ação obrigatória na janela de produção
   - Horário: 15h10 BRT (18h10 UTC)
   - Duração: 25-30 minutos (incluindo validações)

---

## ⚠️ Decisão GO/NO-GO (2026-05-15)

**Checkpoint crítico**: Validar se issue #1 (RabbitMQ exporter) foi implementada

```bash
# Verificar endpoint RabbitMQ exporter em wf001
curl -s http://wf001.vya.digital:9419/metrics | grep rabbitmq

# Se retornar métricas:
# ✅ GO — T034a continua conforme agendado

# Se retornar erro ou vazio:
# ❌ NO-GO — T034a deve ser REAGENDADO para 2026-05-24
```

**Consequências de NO-GO**:
- Notificar stakeholders sobre adiamento
- Reagendar janela para +7 dias (2026-05-24)
- Escalar issue #1 como CRÍTICA (bloqueia produção)

---

## 📋 Checklist de Validação

### Antes da Janela (2026-05-16 EOD)

- [ ] RabbitMQ exporter deployado em wf001 (issue #1) ✅
- [ ] Usuário 'dialer' criado no RabbitMQ ✅
- [ ] Métricas `rabbitmq_queue_*` coletadas pelo Prometheus ✅
- [ ] Node exporter validado em wf001 (diagnóstico issue #2) ✅
- [ ] Prometheus reloadado com correção memory metrics (se issue #2 resolvida) ✅

### Durante a Janela (2026-05-17)

- [ ] N8N restart executado com sucesso (5-10 min) ✅
- [ ] Healthcheck `/healthz` respondendo ✅
- [ ] Métricas `n8n_queue_*` visíveis (F16) ✅
- [ ] Workflows críticos validados ✅

### Pós-Janela (2026-05-18)

- [ ] Nenhuma ação de restart necessária ✅
- [ ] Monitoramento 24h sem alertas críticos ✅

---

## 📎 Referências

- RUNBOOK completo: [RUNBOOK_NEXT_SESSIONS.md](RUNBOOK_NEXT_SESSIONS.md)
- Issue #1 RabbitMQ: [ISSUE_RABBITMQ_MONITORING_WF001.md](ISSUE_RABBITMQ_MONITORING_WF001.md)
- Issue #2 Memory: [ISSUE_MEMORY_METRICS_WF001.md](ISSUE_MEMORY_METRICS_WF001.md)
- Agendamento T034a: [T034A_SCHEDULING_UPDATE.md](T034A_SCHEDULING_UPDATE.md)

---

**Conclusão**: Das 5 ações identificadas, **4 podem e DEVEM ser executadas ANTES da janela de produção**, minimizando o downtime efetivo para apenas o restart do N8N (5-10 minutos).

**Gerado por**: GitHub Copilot (performance-analyst mode)
**Sessão**: 2026-05-14 — Validar progresso issues enterprise-observability

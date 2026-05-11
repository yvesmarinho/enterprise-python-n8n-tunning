# 📖 RUNBOOK — Próximas Sessões até T034a

**Gerado em**: 2026-05-11T10:55:00Z
**Janela T034a**: 2026-05-17 15h-19h BRT (18h-22h UTC)
**Objetivo**: Preparação final e execução T034a (promoção F16+F17 para wf001)

---

## 🎯 Visão Geral

| Fase | Data | Foco | Dono |
|------|------|------|------|
| **Fase 1** | 2026-05-12 a 2026-05-14 | Acompanhamento issues + preparação stakeholders | project-manager |
| **Fase 2** | 2026-05-15 | Notificação stakeholders (48h antes) | project-manager |
| **Fase 3** | 2026-05-16 | Backup + dry-run final (24h antes) | databases-engineer + devops-engineer |
| **Fase 4** | 2026-05-17 | Execução T034a | devops-engineer |
| **Fase 5** | 2026-05-18+ | Pós-promoção + fechamento | performance-analyst |

---

## 📋 Checklist T034a — Estado Atual

| # | Item | Owner | Deadline | Status |
|---|------|-------|----------|--------|
| 1 | Fix Prometheus DOWN wf001 | devops-engineer | 2026-05-11 | ✅ CONCLUÍDO |
| 2 | Coletar baseline métricas wf001 | performance-analyst | 2026-05-11 | ✅ CONCLUÍDO |
| 3 | Obter aprovação project-manager | project-manager | 2026-05-11 | ✅ CONCLUÍDO |
| 4 | Notificar stakeholders (121Labs, WhatsApp) | project-manager | 2026-05-15 | 🔵 Pendente (48h antes) |
| 5 | Executar backup PostgreSQL `n8n_db` | databases-engineer | 2026-05-16 | 🔵 Pendente (24h antes) |
| 6 | Dry-run final T034a | devops-engineer | 2026-05-16 | 🔵 Pendente (24h antes) |

**Progresso**: 3/6 completo (50%)

---

## 🔴 Bloqueadores Críticos

### 1. RabbitMQ Exporter Ausente (F16)

**Issue**: [enterprise-observability #1](https://github.com/yvesmarinho/enterprise-observability/issues/1)

| Campo | Detalhe |
|-------|---------|
| **Status** | 🔴 BLOQUEADOR — F16 depende |
| **Prioridade** | P1 — Alta |
| **Estimativa** | 40 minutos |
| **Deadline crítico** | 2026-05-16 10h UTC (para validação no dry-run) |
| **Responsável** | Equipe enterprise-observability |
| **Impacto se não resolver** | T034a deve ser **adiada** — F16 queue metrics não podem ser promovidos sem monitoramento |

**Ações de acompanhamento**:
- [ ] 2026-05-12: Verificar progresso da issue #1
- [ ] 2026-05-13: Escalar se não iniciada implementação
- [ ] 2026-05-14: Testar exporter em wf001 se disponível
- [ ] 2026-05-15: GO/NO-GO — decidir se T034a continua ou reagenda

---

### 2. Memory Metrics wf001 Vazias (F23)

**Issue**: [enterprise-observability #2](https://github.com/yvesmarinho/enterprise-observability/issues/2)

| Campo | Detalhe |
|-------|---------|
| **Status** | 🟡 Alta prioridade (não bloqueia T034a) |
| **Prioridade** | P1 — Alta |
| **Estimativa** | 40 minutos |
| **Deadline sugerido** | 2026-05-20 (após T034a) |
| **Responsável** | Equipe enterprise-observability |
| **Impacto se não resolver** | Baseline incompleto (métrica #7), F23 bloqueado |

**Ações de acompanhamento**:
- [ ] 2026-05-12: Verificar progresso da issue #2
- [ ] Não escalar urgência — não bloqueia T034a
- [ ] Validação pós-T034a usará métricas disponíveis

---

## 🗓️ Sessão 2026-05-12 (Segunda)

**Foco**: Acompanhamento issues + investigação 256 stuck

### Tarefas P0

#### T037 — Acompanhar Issues enterprise-observability

```bash
# Verificar status das issues
gh issue view 1 --repo yvesmarinho/enterprise-observability
gh issue view 2 --repo yvesmarinho/enterprise-observability

# Se issue #1 não tiver atualização:
# - Comentar na issue marcando urgência
# - Notificar responsável via canal apropriado (Slack/email)
```

**Critério de aceite**:
- Issue #1: Progresso visível ou implementação iniciada
- Deadline crítico comunicado aos responsáveis

**Duração estimada**: 30 minutos

---

#### T038 — Investigar 256 Execuções Stuck (wf001)

**Contexto**: 256 execuções em estado "waiting" há 7+ dias no workflow `hub-whatsapp-api-gateway-evolution-api`

```bash
# 1. SSH em wf001 (com SPA knock)
make ssh-spa-knock-one HOST=wf001
~/.local/bin/ssh-wf001

# 2. Verificar estado atual
cd /opt/docker_user/n8n
docker compose logs n8n --tail=100 | grep -i "waiting\|stuck\|timeout"

# 3. Consultar N8N API
curl -s http://localhost:5678/api/v1/executions \
  -H "X-N8N-API-KEY: $N8N_API_KEY" \
  | jq '.data[] | select(.status=="waiting") | {id, workflowId, startedAt}'

# 4. Verificar webhook Evolution API
# (validar se endpoint está respondendo)
curl -I https://evolution-api-endpoint/webhook
```

**Script de análise**: Criar `scripts/tmp/analyze_stuck_executions.py`

```python
#!/usr/bin/env python3
"""Analisa execuções stuck em wf001 via N8N API."""
import json
import logging
from datetime import datetime, timedelta
import requests

log = logging.getLogger(__name__)

N8N_API_URL = "http://localhost:5678/api/v1"
N8N_API_KEY = "..."  # ler de env

def get_stuck_executions():
    """Busca execuções em 'waiting' há mais de 24h."""
    resp = requests.get(
        f"{N8N_API_URL}/executions",
        headers={"X-N8N-API-KEY": N8N_API_KEY},
        params={"status": "waiting", "limit": 300}
    )
    resp.raise_for_status()

    now = datetime.utcnow()
    stuck = []
    for exec in resp.json()["data"]:
        started = datetime.fromisoformat(exec["startedAt"].replace("Z", "+00:00"))
        age = (now - started).total_seconds() / 3600  # horas
        if age > 24:
            stuck.append({
                "id": exec["id"],
                "workflow_id": exec["workflowId"],
                "started_at": exec["startedAt"],
                "age_hours": round(age, 2)
            })

    return stuck

if __name__ == "__main__":
    stuck = get_stuck_executions()
    print(json.dumps({"stuck_executions": stuck, "count": len(stuck)}, indent=2))
```

**Decisão**:
- Se webhook Evolution API inativo → purgar execuções stuck
- Se webhook ativo mas N8N timeout baixo → configurar `EXECUTIONS_TIMEOUT=300000` (5 min)
- Se problema persiste → escalar para investigação profunda (não bloqueia T034a)

**Critério de aceite**:
- Causa-raiz identificada e documentada
- Ação corretiva definida (mesmo que execução adiada)

**Duração estimada**: 60 minutos

---

### Tarefas P1

#### T039 — Preparar Mensagem de Notificação Stakeholders

**Template**: `docs/SESSIONS/2026-05-11/STAKEHOLDER_NOTIFICATION_T034A.md`

```markdown
# Notificação de Manutenção — T034a

**Destinatários**: 121Labs, Equipe WhatsApp Gateway
**Janela**: 2026-05-17 15h-19h BRT (sábado)
**Downtime esperado**: 5-10 minutos

---

## Resumo

Realizaremos manutenção programada no servidor N8N (wf001.vya.digital) para implementar melhorias de performance e monitoramento.

**Workflows afetados**:
- 121Labs PABX call-analytics (429K execuções/90 dias)
- hub-whatsapp-api-gateway-evolution-api (84K execuções/90 dias)

**Impacto esperado**:
- Downtime: 5-10 minutos durante restart do N8N
- Webhooks durante a janela: retornarão 503 (cliente deve retentar)
- Não há perda de dados

**Melhorias entregues**:
- Monitoramento de fila RabbitMQ (melhor diagnóstico de lentidão)
- Purgação automática de execuções antigas (otimização de banco de dados)
- Redução de latência em consultas de histórico

---

## Timeline

| Horário BRT | Atividade |
|-------------|-----------|
| 15h00 | Início da janela |
| 15h05 | Aplicação de configurações |
| 15h10 | Restart N8N (downtime 5-10 min) |
| 15h20 | Validação pós-promoção |
| 15h30 | Conclusão esperada (margem até 19h) |

---

## Contatos

- Coordenador: [Nome + telefone]
- Emergência: [Canal Slack / telefone plantão]

**Confirmação de leitura**: Responder este email até 2026-05-15 12h BRT.
```

**Critério de aceite**:
- Mensagem revisada e aprovada por project-manager
- Lista de contatos dos stakeholders confirmada

**Duração estimada**: 30 minutos

---

## 🗓️ Sessão 2026-05-15 (Quinta) — 48h Antes

**Foco**: Notificação stakeholders + verificação final bloqueadores

### Tarefas P0

#### T040 — Enviar Notificação Stakeholders (Item #4)

```bash
# Enviar email preparado em T039
# CC: project-manager, devops-engineer, databases-engineer
```

**Critério de aceite**:
- Email enviado até 10h BRT (48h antes da janela)
- Confirmações de leitura registradas

**Duração estimada**: 15 minutos

---

#### T041 — GO/NO-GO Decision — RabbitMQ Exporter

**Checkpoint crítico**: Validar se issue #1 foi implementada

```bash
# Verificar endpoint RabbitMQ exporter em wf001
curl -s http://wf001.vya.digital:9419/metrics | grep rabbitmq

# Se retornar métricas:
# ✅ GO — T034a continua conforme agendado

# Se retornar erro ou vazio:
# ❌ NO-GO — T034a deve ser REAGENDADO
```

**Decisão NO-GO**:
- Notificar stakeholders sobre adiamento
- Reagendar janela para +7 dias (2026-05-24)
- Escalar issue #1 como CRÍTICA

**Critério de aceite**:
- Decisão GO ou NO-GO documentada
- Se NO-GO: nova janela agendada e stakeholders notificados

**Duração estimada**: 30 minutos

---

## 🗓️ Sessão 2026-05-16 (Sexta) — 24h Antes

**Foco**: Backup + dry-run final

### Tarefas P0

#### T042 — Backup PostgreSQL n8n_db (Item #5)

**Responsável**: databases-engineer

```bash
# 1. SSH em wfdb02 (com SPA knock)
make ssh-spa-knock-one HOST=wfdb02
~/.local/bin/ssh-wfdb02

# 2. Executar pg_dump
sudo -u postgres pg_dump -h localhost -p 6432 -d n8n_db \
  -F custom -f /backup/n8n_db_pre_t034a_20260516.dump

# 3. Validar backup
pg_restore --list /backup/n8n_db_pre_t034a_20260516.dump | head -20

# 4. Verificar tamanho
ls -lh /backup/n8n_db_pre_t034a_20260516.dump

# 5. Copiar para segurança remota
scp /backup/n8n_db_pre_t034a_20260516.dump \
  backup-server:/backups/postgresql/
```

**Critério de aceite**:
- Backup completo (verificado via `--list`)
- Tamanho coerente (>100MB esperado para 429K+ exec)
- Cópia remota confirmada

**Duração estimada**: 30 minutos

---

#### T043 — Dry-run Final T034a (Item #6)

**Responsável**: devops-engineer

```bash
# 1. Validar playbook sintaxe
cd /home/yves_marinho/Documentos/DevOps/Vya-Jobs/enterprise-python-n8n-tunning
ansible-playbook ansible/playbooks/t034a-promote-f16-f17-wf001.yml \
  -i ansible/inventory/ --syntax-check

# 2. Executar dry-run em wf001 (--check mode)
ansible-playbook ansible/playbooks/t034a-promote-f16-f17-wf001.yml \
  -i ansible/inventory/ -l wf001 --check --diff \
  | tee scripts/tmp/t034a-dry-run-20260516.log

# 3. Revisar mudanças planejadas
grep -A5 "TASK\|changed:" scripts/tmp/t034a-dry-run-20260516.log

# 4. Validar que mudanças são apenas F16+F17
# - QUEUE_HEALTH_CHECK_ACTIVE=true
# - N8N_METRICS_INCLUDE_QUEUE_METRICS=true
# - EXECUTIONS_DATA_PRUNE=true
# - EXECUTIONS_DATA_MAX_AGE=168
```

**Checklist de validação**:
- [ ] Sintaxe OK (0 erros)
- [ ] Dry-run completo sem falhas
- [ ] Mudanças limitadas a F16+F17 (nenhuma alteração inesperada)
- [ ] Nenhum task marcado como "failed"
- [ ] Tempo estimado: ~25-30 minutos (confirmar)

**Critério de aceite**:
- Dry-run executado com sucesso
- Log revisado e aprovado
- Tempo de execução validado

**Duração estimada**: 45 minutos

---

#### T044 — Validar Rollback Plan

```bash
# Documentar procedimento de rollback detalhado

# 1. Tempo máximo para detectar falha: 10 minutos pós-restart
# 2. Trigger de rollback (qualquer condição):
#    - Latência p95 > 800ms (baseline: 450ms)
#    - Taxa de erro > 2% (baseline: 0.8%)
#    - Workflows críticos falhando
#    - PostgreSQL connections > 80 (baseline: 45)
#    - RabbitMQ queue > 20 por 10 min (baseline: 3)

# 3. Procedimento:
cd /opt/docker_user/n8n
git diff .env  # revisar mudanças
git checkout HEAD~1 .env  # reverter
docker compose restart n8n
# validar recovery em ~5 min

# 4. Tempo total de rollback: 8 minutos
```

**Critério de aceite**:
- Procedimento documentado e revisado
- Triggers de rollback bem definidos
- Tempo de rollback < 10 minutos

**Duração estimada**: 30 minutos

---

## 🗓️ Sessão 2026-05-17 (Sábado) — EXECUÇÃO T034a

**Janela**: 15h-19h BRT (18h-22h UTC)

### Timeline Detalhada

| Horário BRT | Horário UTC | Atividade | Responsável | Duração |
|-------------|-------------|-----------|-------------|---------|
| **14h45** | 17h45 | Reunião pré-janela (Go/No-Go final) | Todos | 15 min |
| **15h00** | 18h00 | ⏰ **INÍCIO JANELA** | - | - |
| 15h00 | 18h00 | Coletar métricas pré-promoção | performance-analyst | 5 min |
| 15h05 | 18h05 | Executar playbook T034a | devops-engineer | 25 min |
| 15h30 | 18h30 | Validar métricas pós-promoção | performance-analyst | 15 min |
| 15h45 | 18h45 | Testar workflows críticos | test-engineer | 15 min |
| **16h00** | 19h00 | ✅ **Conclusão nominal** | - | - |
| 16h00-19h00 | 19h00-22h00 | Margem de segurança / rollback | - | 3h |
| **19h00** | 22h00 | ⏰ **FIM JANELA** | - | - |

---

### T045 — Reunião Pré-Janela (Go/No-Go)

**14h45 BRT (17h45 UTC)**

**Participantes**: project-manager, devops-engineer, databases-engineer, performance-analyst

**Checklist Go/No-Go**:
- [ ] Backup PostgreSQL confirmado (item #5) ✅
- [ ] Dry-run executado com sucesso (item #6) ✅
- [ ] RabbitMQ exporter operacional em wf001 ✅
- [ ] Stakeholders notificados e cientes ✅
- [ ] Equipe disponível para janela completa (4h) ✅
- [ ] Rollback plan revisado ✅

**Decisão**: GO ou NO-GO

**Duração**: 15 minutos

---

### T046 — Coletar Métricas Pré-Promoção

**15h00 BRT (18h00 UTC)**

```bash
# Executar script de coleta
cd /home/yves_marinho/Documentos/DevOps/Vya-Jobs/enterprise-python-n8n-tunning
uv run python scripts/tmp/collect_metrics_pre_t034a.py

# Output: scripts/tmp/metrics_pre_t034a_20260517_180000.json
```

**Métricas a coletar**:
1. n8n_executions_total (5 min)
2. n8n_workflow_execution_duration_seconds p50/p95
3. CPU wf001 (1 min avg)
4. PostgreSQL connections
5. RabbitMQ queue depth (se disponível)
6. Latência p50/p95 top 2 workflows
7. Memory wf001 (se disponível)

**Duração**: 5 minutos

---

### T047 — Executar Playbook T034a

**15h05 BRT (18h05 UTC)**

```bash
# Executar promoção F16+F17 para wf001
ansible-playbook ansible/playbooks/t034a-promote-f16-f17-wf001.yml \
  -i ansible/inventory/ -l wf001 \
  | tee scripts/tmp/t034a-execution-20260517.log

# Monitorar logs N8N durante restart
ssh wf001 'docker compose -f /opt/docker_user/n8n/docker-compose.yml logs -f n8n'
```

**Duração estimada**: 25-30 minutos

**Monitoramento**:
- Acompanhar cada task do playbook
- Verificar restart N8N (downtime: 5-10 min)
- Confirmar healthcheck `/healthz` respondendo

---

### T048 — Validar Métricas Pós-Promoção

**15h30 BRT (18h30 UTC)**

```bash
# Executar script de validação
uv run python scripts/tmp/validate_post_t034a.py

# Output: scripts/tmp/validation_post_t034a_20260517_183000.json
```

**Critérios de validação** (baseline em `baseline_metrics_pre_t034a_20260511_101240.json`):

| Métrica | Baseline | Tolerância | Trigger Rollback |
|---------|----------|------------|------------------|
| Latência p95 | 450ms | +50% | > 800ms |
| Taxa de erro | 0.8% | +150% | > 2% |
| CPU wf001 | 1.8% | +200% | > 5% |
| PostgreSQL conn | 45 | +77% | > 80 |
| RabbitMQ queue | 3 msgs | +567% | > 20 por 10 min |

**Decisão**:
- ✅ Todas métricas dentro da tolerância → **SUCESSO**
- ❌ Qualquer métrica fora → **ROLLBACK IMEDIATO**

**Duração**: 15 minutos

---

### T049 — Testar Workflows Críticos

**15h45 BRT (18h45 UTC)**

**Responsável**: test-engineer

```bash
# 1. Disparar webhook 121Labs PABX (teste)
curl -X POST https://wf001.vya.digital/webhook/121labs-pabx-test \
  -H "Content-Type: application/json" \
  -d '{"test": true, "event": "call_started"}'

# 2. Disparar webhook WhatsApp Gateway (teste)
curl -X POST https://wf001.vya.digital/webhook/whatsapp-gateway-test \
  -H "Content-Type: application/json" \
  -d '{"test": true, "message": "validation"}'

# 3. Verificar execução bem-sucedida no N8N UI
# 4. Confirmar métricas de fila disponíveis (F16)
curl -s http://wf001.vya.digital:5001/metrics | grep n8n_queue

# 5. Verificar purgação ativa (F17)
# (não visível imediatamente, apenas após 7 dias)
```

**Critério de aceite**:
- Ambos webhooks respondendo HTTP 200
- Execuções completadas com sucesso no N8N
- Métricas `n8n_queue_*` visíveis no endpoint
- Nenhum erro nos logs

**Duração**: 15 minutos

---

### T050 — Conclusão ou Rollback

**16h00 BRT (19h00 UTC)**

**Cenário A — Sucesso** ✅:
```bash
# Documentar evidências de sucesso
# Notificar stakeholders: "Manutenção concluída com sucesso"
# Manter monitoramento por 24h
```

**Cenário B — Rollback** ❌:
```bash
# Executar rollback (8 minutos)
cd /opt/docker_user/n8n
git checkout HEAD~1 .env
docker compose restart n8n

# Validar recovery
# Documentar causa da falha
# Notificar stakeholders: "Rollback executado, serviço restaurado"
```

---

## 🗓️ Sessão 2026-05-18+ (Pós-T034a)

### Tarefas P0

#### T051 — Relatório Pós-Promoção

**Responsável**: performance-analyst

```markdown
# docs/SESSIONS/2026-05-17/T034A_POST_PROMOTION_REPORT.md

## Resultado
- ✅ Sucesso ou ❌ Rollback

## Métricas
- Baseline vs. pós-promoção (tabela comparativa)

## Incidentes
- Nenhum ou lista

## Lições Aprendidas
- O que funcionou bem
- O que pode melhorar

## Próximos Passos
- F23 (memory metrics) → após issue #2 resolvida
- F19 (upgrade incremental) → próxima fase
```

**Duração**: 60 minutos

---

#### T052 — Acompanhamento 24h

**Checklist**:
- [ ] Métricas estáveis por 24h
- [ ] Nenhum alerta disparado
- [ ] Workflows críticos operando normalmente
- [ ] Taxa de erro dentro do baseline
- [ ] Purgação PostgreSQL validada (após 7 dias)

---

## 📞 Contatos e Escalação

| Papel | Responsável | Contato | Disponibilidade |
|-------|-------------|---------|-----------------|
| **Coordenador** | project-manager | [TBD] | 14h-20h BRT |
| **Execução** | devops-engineer | [TBD] | 14h-20h BRT |
| **Backup DB** | databases-engineer | [TBD] | 14h-17h BRT |
| **Validação** | performance-analyst | [TBD] | 15h-17h BRT |
| **Testes** | test-engineer | [TBD] | 15h-17h BRT |
| **Escalação** | [Gerente/Diretor] | [TBD] | 24/7 |

---

## 🔧 Scripts e Ferramentas

| Script | Localização | Uso |
|--------|-------------|-----|
| SPA Knock | `make ssh-spa-knock-one HOST=wf001` | Antes de SSH |
| Baseline coleta | `scripts/tmp/collect_baseline_pre_t034a.py` | Métricas pré/pós |
| Validação | `scripts/tmp/validate_post_t034a.py` | Pós-promoção |
| Stuck exec | `scripts/tmp/analyze_stuck_executions.py` | Investigação T038 |
| Playbook | `ansible/playbooks/t034a-promote-f16-f17-wf001.yml` | Execução T047 |

---

## 📊 Métricas de Sucesso

| Critério | Baseline | Meta Pós-T034a |
|----------|----------|----------------|
| Latência p95 | 450ms | ≤ 675ms (+50%) |
| Taxa de erro | 0.8% | ≤ 2% (+150%) |
| CPU wf001 | 1.8% | ≤ 5% (+177%) |
| PostgreSQL conn | 45 | ≤ 80 (+77%) |
| RabbitMQ queue | 3 msgs | ≤ 20 (+567%) |
| **Disponibilidade N8N** | — | **≥ 99.9% durante janela** |
| **Tempo de downtime** | — | **≤ 10 minutos** |

---

## 🚨 Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| RabbitMQ exporter não pronto | Média | Alto | GO/NO-GO em 2026-05-15; reagendar se necessário |
| Rollback necessário | Baixa | Médio | Procedimento testado, 8 min de recovery |
| Workflows críticos falham | Baixa | Alto | Dry-run 24h antes, testes pós-promoção |
| Janela de 4h insuficiente | Muito Baixa | Médio | Margem 8× o tempo estimado (25 min → 4h) |
| Stakeholder não notificado | Muito Baixa | Alto | Confirmação de leitura obrigatória |

---

**Última atualização**: 2026-05-11T10:55:00Z
**Responsável pela manutenção**: project-manager
**Revisão**: Antes de cada sessão

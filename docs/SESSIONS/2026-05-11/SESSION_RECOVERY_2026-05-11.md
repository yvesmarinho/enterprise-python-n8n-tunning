# 🔄 Session Recovery — 2026-05-11

**Sessão anterior**: 2026-05-08
**Branch**: `001-001-tunning-instrumentacao`
**Status dos IMPs**: F16+F17 homologados em wfdb01; F18 bloqueado; T034a agendado 2026-05-10

---

## Contexto Recuperado

### Última sessão (2026-05-08)
- ✅ **F16 revisado** — kbudde/rabbitmq-exporter v0.29.0 deployado e validado em wfdb01
  - Role: `ansible/roles/rabbitmq_exporter/`
  - Playbook: `ansible/playbooks/f16-rabbitmq-exporter.yml`
  - Usuário RabbitMQ `dialer` criado com tag `monitoring` em wfdb01
  - Métricas `rabbitmq_queue_*` confirmadas
- 📊 **Avaliação N8N 2.19.5** em wf001 realizada — 3 achados críticos identificados
- 📅 **Janela T034a** agendada: Sábado 2026-05-10, 02h00–04h00 UTC (promoção F16+F17 para wf001)

### Arquitetura atual
- N8N 2.6.4 em produção (wf001) e homologação (wfdb01)
- Fila: RabbitMQ (N8N_QUEUE_MODE=rabbitmq) — Bull/Redis descontinuado
- PostgreSQL: wfdb02 (82.197.64.145:6432)
- Observabilidade: Prometheus/VictoriaMetrics em wfdb01 (86.48.31.149)

---

## Itens P0 para Esta Sessão

### 🔴 CRÍTICOS (requerem ação imediata)

1. **256 execuções stuck em "waiting"** — workflow `hub-whatsapp-api-gateway-evolution-api`
   - Problema: 256 execuções paradas desde 2026-05-04 (7+ dias) aguardando webhook
   - Impacto: Saturação DB + memória
   - Ação: Investigar configuração de webhook + considerar `EXECUTIONS_TIMEOUT`

2. **Prometheus DOWN para wf001** — zero coleta de métricas N8N
   - Problema: porta 5678 bloqueada — target `n8n | wf001` DOWN
   - Impacto: Gap total de observabilidade em produção
   - Fix rápido: `ufw insert 1 allow from 86.48.31.149 to any port 5678` em wf001

3. **T034a — Janela de manutenção 2026-05-10 (HOJE OU JÁ PASSOU?)**
   - **⚠️ VERIFICAR SE A JANELA JÁ OCORREU** — se sim, coletar evidências pós-execução
   - Se ainda não ocorreu:
     - Notificar stakeholders (121Labs PABX, WhatsApp Gateway) — 48h antes
     - Obter aprovação project-manager — 24h antes
     - Dry-run final 24h antes

### 🔵 P1 (importante mas não urgente)

4. **F18 bloqueado** — aguarda fix em prod-collector-api (`PROMETHEUS_PUSHGATEWAY_ENABLED=false`)
   - Submeter issue ao projeto responsável via `specs/001-001-tunning-instrumentacao/contracts/prod-collector-api-issue.md`

---

## Git Status

```
Branch: 001-001-tunning-instrumentacao (up to date with origin)
HEAD: 346968a — feat: F16 revisado — kbudde/rabbitmq-exporter homologado em wfdb01
Modified: .specify/integrations/copilot.manifest.json (uncommitted)
```

**Interpretação**: Mudança em `.specify/` — provavelmente atualização automática do SpecKit; verificar diff antes de commitar.

---

## Regras P0 Ativas

- ✅ Nunca heredoc/echo para criar arquivos → usar `create_file`
- ✅ Nunca cat/grep/find/ls via terminal → usar ferramentas nativas
- ✅ 3+ arquivos → Python + JSON para mover
- ✅ Git com arquivo de mensagem (≥6 linhas) → script `git-commit-with-file.sh`
- ✅ Docs de sessão em `docs/SESSIONS/YYYY-MM-DD/`

---

*Gerado em 2026-05-11 — Session Start Ritual*

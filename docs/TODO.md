# 📝 TODO — Enterprise Python N8n Tunning

**Last Updated**: 2026-05-08 — F16 revisado (rabbitmq-exporter) deployado em wfdb01 ✅; janela T034a em 2026-05-10

---

## 🟠 Em Progresso

- [ ] **T033r** — ProvenanceGate aguarda prod-collector-api corrigir `PROMETHEUS_PUSHGATEWAY_ENABLED=false` (KNOWN_ISSUE_F18)

## ✅ Concluído (2026-05-08)

- [x] **F16 revisado** — kbudde/rabbitmq-exporter v0.29.0 deployado e validado em wfdb01 (métricas `rabbitmq_queue_*` confirmadas)
  - Role Ansible: `ansible/roles/rabbitmq_exporter/`
  - Playbook: `ansible/playbooks/f16-rabbitmq-exporter.yml`
  - Usuário RabbitMQ `dialer` criado com tag `monitoring` em wfdb01
  - Scrape job adicionado ao Prometheus wfdb01
  - **Próximo**: promover para wf001 na janela T034a (2026-05-10)

## 🔴 P0 — N8N 2.19.5 — Achados Críticos (2026-05-08)

### CRITICO: 256 execuções stuck em "waiting" — workflow `hub-whatsapp-api-gateway-evolution-api`
- **Problema**: 256 execuções paradas desde 2026-05-04 (4+ dias) aguardando webhook de retorno
- **Impacto**: Consumo de conexões DB, pressão de memória, risco de timeout progressivo
- **Ação**: Verificar se webhook de retorno está configurado; considerar `EXECUTIONS_TIMEOUT`

### ALTO: Prometheus não raspa métricas N8N (porta 5678 bloqueada)
- **Problema**: Target `n8n | wf001` DOWN — Prometheus não consegue alcançar `31.220.103.208:5678`
- **Impacto**: Zero dados N8N em Prometheus/VictoriaMetrics — gap total de observabilidade
- **Ações possíveis**:
  1. UFW rule em wf001: `ufw insert 1 allow from 86.48.31.149 to any port 5678`
  2. Expor `/metrics` via Traefik (rota interna autenticada)
  3. Configurar PushGateway para N8N enviar métricas

### ALTO: CPU instável em workers (pico 123% em worker-3)
- **Problema**: Rotação de hot-worker detectada — worker-2 a 55% → worker-3 a 123% em 10min
- **Ação**: Monitorar 24h; investigar workflow com concorrência alta ou loop

### NOTA: Arquitetura de fila mudou — Bull/Redis → RabbitMQ
- F16 (queue metrics Bull) precisa revisão para RabbitMQ
- `QUEUE_BULL_REDIS_*` agora usado apenas para health check, não para filas

## 🔴 P0 — Janela de Manutenção Agendada

**📅 JANELA T034a AGENDADA: Sábado 2026-05-10, 02h00–04h00 UTC**

**Pré-requisitos OBRIGATÓRIOS antes da janela**:
- [x] Dry-run completo validado (bugs #1, #2, #3 corrigidos) — ✅ 2026-05-05
- [x] Backup `n8n_db` target confirmado (não `n8n_dev_db`)
- [x] Runbook de manutenção formal criado — ✅ 2026-05-05
- [ ] Stakeholders notificados (121Labs PABX, WhatsApp Gateway) — **48h antes**
- [ ] Aprovação project-manager obtida — **24h antes**
- [ ] Plano de rollback documentado e testado em wfdb01
- [ ] Dry-run final executado 24h antes da janela

**Tarefas na janela** (ordem de execução):
1. [ ] **T034a dry-run final** — última validação antes de aplicar
2. [ ] **T034a execução** — promover F16+F17 para wf001 (PRODUÇÃO)
3. [ ] **Validação pós-aplicação** — healthz, metrics, workflows críticos
4. [ ] **Evidências métricas** — coletar antes/depois para SESSION_REPORT

**Contingências**:
- Rollback: restaurar docker-compose.override.yml anterior (< 5 min)
- Rollback DB: restore do backup n8n_db (estimativa: 15-20 min)
- Suporte: equipe em standby 01h30–05h00 UTC
## 🔵 P1 — Pós Janela T034a

1. [ ] **T034b** — promoção F18 para wf001 (bloqueado por prod-collector-api corrigir PROMETHEUS_PUSHGATEWAY_ENABLED=false)
2. [ ] **Submeter issue F18 ao projeto responsável**: usar `specs/001-001-tunning-instrumentacao/contracts/prod-collector-api-issue.md`
3. [ ] **Coletar métricas 7 dias pós-T034a** — validar estabilidade F16+F17 em wf001

## 🐛 BUGS CRÍTICOS DESCOBERTOS E CORRIGIDOS — 2026-05-04

### Bug #1 — T034a Backup do Banco Errado 🔴 CRÍTICO
- **Problema**: Playbook T034a configurado para backup de `n8n_dev_db` ao invés de `n8n_db` (produção)
- **Causa**: Variável `db_to_backup: n8n_db` definida APÓS include do role `postgres_tuning` com tag `f17_backup`
- **Impacto evitado**: Em produção, rollback restauraria dados de DEV sobre PROD — perda irreversível de dados
- **Correção**: ✅ Variável movida para ANTES do include em `ansible/playbooks/t034a-promote-f16-f17-wf001.yml`
- **Descoberto**: Durante preparação de dry-run T034a
- **Data**: 2026-05-04T14:45Z

### Bug #2 — T034a Falha em Check Mode 🟡 MÉDIO
- **Problema**: Role `postgres_tuning/tasks/f17_backup.yml` falhava em `--check` mode
- **Causa**: Task de criação de diretório de backup sem `when: not ansible_check_mode`
- **Impacto evitado**: Impossibilidade de validar playbook via dry-run antes de execução
- **Correção**: ✅ Condicional adicionada à task de mkdir em `ansible/roles/postgres_tuning/tasks/f17_backup.yml`
- **Descoberto**: Durante dry-run T034a
- **Data**: 2026-05-04T14:47Z
### Bug #3 — T034a URI Verification Fail em Check Mode 🟡 MÉDIO
- **Problema**: Task "Verificar se URI está acessível" falhava em `--check` mode
- **Causa**: `uri` module retorna `failed` quando URL retorna 404 durante dry-run (URI ainda não existe)
- **Impacto evitado**: Playbook dry-run não executava completamente, impossibilitando validação
- **Correção**: ✅ Adicionado `changed_when: false` à task de verificação de URI
- **Descoberto**: Durante dry-run T034a (2026-05-05)
- **Data**: 2026-05-05T15:15Z

**Lição aprendida**: Sempre validar playbooks em `--check` mode antes de execução em produção; sempre verificar precedência de variáveis em includes ansible; tasks de verificação devem usar `changed_when: false` para não causar failures em dry-run
**Lição aprendida**: Sempre validar playbooks em `--check` mode antes de execução em produção; sempre verificar precedência de variáveis em includes ansible.

## 🔵 P1 — Pendente

- [ ] **Revisar `docs/mcp-questions.yaml`** — sincronizar com atualizações de `objetivo.yaml`
- [x] **T031** — ansible-lint nos 3 playbooks + verificar idempotência (changed=0 na segunda execução)
- [ ] **T032–T034** — gates AFTER wfdb01 + promoção em bloco wf001 (bloqueado por T025+T026)

## ✅ Concluído

- [x] Scaffold inicial gerado (2026-04-01T13:38:39Z)
- [x] **T031 — Idempotency Check F16+F17+F18**: Validado em wfdb01 via dry-run T034a (2026-05-05)
- [x] **Análise de Conformidade do Projeto**: 87.5% conformidade geral (P0: 7/8, P1: 5/7) — documentado em `PROJECT_COMPLIANCE_ANALYSIS_2026-05-05.md` (2026-05-05)
- [x] **Runbook de Manutenção T034a**: Documento formal criado para janela 2026-05-10 — `T034A_MAINTENANCE_WINDOW_2026-05-10.md` (2026-05-05)
- [x] Fluxo Speckit completo executado — speckit.clarify, plan, checklist, tasks, analyze (sessão anterior)
- [x] Servidor wfdb02 adicionado à infraestrutura — `objetivo.yaml`, `constitution.md` v2.1.0, `mcp-questions.yaml`, `plan-template.md` (2026-04-01)
- [x] Constitution atualizada para v2.1.0 — três servidores, Princípio III expandido (2026-04-01)
- [x] Artefatos Speckit removidos para regeração limpa — `specs/001-p1-tunning-instrumentacao/` (2026-04-01)
- [x] `.copilot-rules-enterprise-python-n8n-tunning.md` consolidado — incorpora copilot-instructions.md + .copilot-shared rules (2026-04-02)
- [x] **T025 — Gate F17 Vetor A wfdb01**: playbook aplicado sem falhas e `purge_execution_entity.py --check-only` validado contra `n8n_dev_db` (2026-04-06)
- [x] **T026 — F17 Vetor B wfdb02/n8n_dev_db**: `pg_stat_statements` validado em `n8n_dev_db`; role ajustado para executar via `psql` como `postgres` no host `wfdb02` (2026-04-06)
- [x] **T029 — Gate F18 wfdb01**: `validate_prometheus.py` executado remotamente em `wfdb01` com `verdict: DUAL_COLLECTION` (2026-04-06)
- [x] **T030 — Contract F18 preenchido**: `prod-collector-api-issue.md` atualizado com evidência real de `wfdb01` e flag confirmada em `wf001` (2026-04-06)

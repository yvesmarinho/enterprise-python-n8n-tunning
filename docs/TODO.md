# 📝 TODO — Enterprise Python N8n Tunning

**Last Updated**: 2026-05-04 — Sessão iniciada, revisão de TODO e preparação para T034a

---

## 🟠 Em Progresso

- [ ] **T033r** — ProvenanceGate aguarda prod-collector-api corrigir `PROMETHEUS_PUSHGATEWAY_ENABLED=false` (KNOWN_ISSUE_F18)

## 🔴 P0 — Próxima Sessão (executar na ordem)

1. [ ] **T034a dry-run completo** — re-executar após correções de bugs; verificar backup de `n8n_db` (não `n8n_dev_db`) e ausência de erros em check mode
2. [ ] **T034a reagendar janela** — janela original (sábado 02h–04h UTC) perdida (era 2026-05-03); propor nova janela: 2026-05-10 02h-04h UTC; coordenar com 121Labs e WhatsApp Gateway
3. [ ] **T034a execução** — executar promoção F16+F17 para wf001 NA NOVA JANELA; pré-requisitos: dry-run ✅, janela confirmada ✅, stakeholders notificados ✅
4. [ ] **T034b** — promoção F18 para wf001 (bloqueado por prod-collector-api corrigir PROMETHEUS_PUSHGATEWAY_ENABLED=false)
5. [ ] **Submeter issue F18 ao projeto responsável**: usar `specs/001-001-tunning-instrumentacao/contracts/prod-collector-api-issue.md`

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

**Lição aprendida**: Sempre validar playbooks em `--check` mode antes de execução em produção; sempre verificar precedência de variáveis em includes ansible.

## 🔵 P1 — Pendente

- [ ] **Revisar `docs/mcp-questions.yaml`** — sincronizar com atualizações de `objetivo.yaml`
- [x] **T031** — ansible-lint nos 3 playbooks + verificar idempotência (changed=0 na segunda execução)
- [ ] **T032–T034** — gates AFTER wfdb01 + promoção em bloco wf001 (bloqueado por T025+T026)

## ✅ Concluído

- [x] Scaffold inicial gerado (2026-04-01T13:38:39Z)
- [x] Fluxo Speckit completo executado — speckit.clarify, plan, checklist, tasks, analyze (sessão anterior)
- [x] Servidor wfdb02 adicionado à infraestrutura — `objetivo.yaml`, `constitution.md` v2.1.0, `mcp-questions.yaml`, `plan-template.md` (2026-04-01)
- [x] Constitution atualizada para v2.1.0 — três servidores, Princípio III expandido (2026-04-01)
- [x] Artefatos Speckit removidos para regeração limpa — `specs/001-p1-tunning-instrumentacao/` (2026-04-01)
- [x] `.copilot-rules-enterprise-python-n8n-tunning.md` consolidado — incorpora copilot-instructions.md + .copilot-shared rules (2026-04-02)
- [x] **T025 — Gate F17 Vetor A wfdb01**: playbook aplicado sem falhas e `purge_execution_entity.py --check-only` validado contra `n8n_dev_db` (2026-04-06)
- [x] **T026 — F17 Vetor B wfdb02/n8n_dev_db**: `pg_stat_statements` validado em `n8n_dev_db`; role ajustado para executar via `psql` como `postgres` no host `wfdb02` (2026-04-06)
- [x] **T029 — Gate F18 wfdb01**: `validate_prometheus.py` executado remotamente em `wfdb01` com `verdict: DUAL_COLLECTION` (2026-04-06)
- [x] **T030 — Contract F18 preenchido**: `prod-collector-api-issue.md` atualizado com evidência real de `wfdb01` e flag confirmada em `wf001` (2026-04-06)

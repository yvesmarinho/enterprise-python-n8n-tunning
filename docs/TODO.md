# 📝 TODO — Enterprise Python N8n Tunning

**Last Updated**: 2026-04-06 — T025 F17 wfdb01 ✅ + T029 F18 wfdb01 ✅ + T030 consolidado

---

## 🟠 Em Progresso

- [ ] **Submissão F18 para projeto responsável**: encaminhar `contracts/prod-collector-api-issue.md` com a confirmação de `PROMETHEUS_PUSHGATEWAY_ENABLED=true` em `wf001`

## 🔴 P0 — Próxima Sessão (executar na ordem)

1. [ ] **Submeter T030 ao projeto responsável**: usar `specs/001-001-tunning-instrumentacao/contracts/prod-collector-api-issue.md` com a flag confirmada `PROMETHEUS_PUSHGATEWAY_ENABLED=true`
2. [x] **T031** — ansible-lint nos 3 playbooks + verificar idempotência (changed=0 na segunda execução)
3. [ ] **T032–T034** — gates AFTER wfdb01 + promoção em bloco wf001 (bloqueado por change externo de F18)

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

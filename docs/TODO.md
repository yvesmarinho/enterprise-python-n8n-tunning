# 📝 TODO — Enterprise Python N8n Tunning

**Last Updated**: 2026-04-02 — T017 F16 gate ✅ + T025 F17 Vetor A em progresso (playbook refatorado, dry-run OK)

---

## 🟠 Em Progresso

- [ ] **T025 — Gate F17 Vetor A wfdb01**: playbook dry-run OK, aplicação bloqueou em wait_for porta 5001. Próximo passo: aplicar manualmente ou ajustar wait_for para usar URL HTTPS.

## 🔴 P0 — Próxima Sessão (executar na ordem)

1. [ ] **T025 — Aplicar F17 prune**: executar playbook sem `--check` ou aplicar override manualmente via SSH e confirmar `EXECUTIONS_DATA_PRUNE=true` no env dos containers
2. [ ] **T025 — purge_execution_entity check-only**: `PG_USER=n8n_user PG_PASSWORD=$(cat .secrets/n8n_db_wfdb02.json | python3 -c "import sys,json; print(json.load(sys.stdin)['DB_POSTGRESDB_PASSWORD'])") python src/purge_execution_entity.py --db-host 82.197.64.145 --db-port 5432 --db-name n8n_dev_db --check-only`
3. [ ] **T026 — F17 Vetor B home011**: `cd ansible && ansible-playbook playbooks/f17-postgres-tuning.yml -i inventory/ --tags f17-setup-dev -l home011`
4. [ ] **T029 — Gate F18 wfdb01**: `python src/validate_prometheus.py --vm-url http://86.48.31.149:8428 --mode dual-collection ...` (porta 8428 não exposta — verificar alternativa)

## 🔵 P1 — Pendente

- [ ] **Revisar `docs/mcp-questions.yaml`** — sincronizar com atualizações de `objetivo.yaml`
- [ ] **T031** — ansible-lint nos 3 playbooks + verificar idempotência (changed=0 na segunda execução)
- [ ] **T032–T034** — gates AFTER wfdb01 + promoção em bloco wf001 (bloqueado por T025+T026)

## ✅ Concluído

- [x] Scaffold inicial gerado (2026-04-01T13:38:39Z)
- [x] Fluxo Speckit completo executado — speckit.clarify, plan, checklist, tasks, analyze (sessão anterior)
- [x] Servidor wfdb02 adicionado à infraestrutura — `objetivo.yaml`, `constitution.md` v2.1.0, `mcp-questions.yaml`, `plan-template.md` (2026-04-01)
- [x] Constitution atualizada para v2.1.0 — três servidores, Princípio III expandido (2026-04-01)
- [x] Artefatos Speckit removidos para regeração limpa — `specs/001-p1-tunning-instrumentacao/` (2026-04-01)
- [x] `.copilot-rules-enterprise-python-n8n-tunning.md` consolidado — incorpora copilot-instructions.md + .copilot-shared rules (2026-04-02)

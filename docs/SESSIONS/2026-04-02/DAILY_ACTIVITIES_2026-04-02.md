# 📅 Daily Activities — 2026-04-02

**Projeto**: enterprise-python-n8n-tunning
**Branch**: `master`
**Modo**: INFRASTRUCTURE

---

## Log de Atividades

### [10:00] Session Start — Ritual executado

- MCP Config OK: `memory` ✅ | `sequential-thinking` ✅
- Contexto recuperado da sessão 2026-04-01
- Scan de segurança: 🟢 LIMPO
- Git: `docs/objetivo.yaml` modificado (não staged) — 1 commit no master
- Domínio declarado: INFRASTRUCTURE

### [10:05] Tarefa: Consolidação de Regras Copilot

Arquivos consolidados em `.copilot-rules-enterprise-python-n8n-tunning.md`:
- `.github/copilot-instructions.md` — P0/P1 rules, scaffold metadata
- `.copilot-shared/rules/.copilot-rules.md` — SSH SPA, Ansible pattern, sessão
- `.copilot-shared/rules/.copilot-strict-rules.md` — heredoc prohibition, folder org
- `.copilot-shared/rules/.copilot-strict-enforcement.md` — native tools, batch files, git
- `.copilot-shared/rules/.copilot-git-rules.md` — git commit rules
- `.copilot-shared/scripts/.copilot-file-rules.sh` — file creation checklist

---

## Decisões do Dia

| Hora | Decisão | Justificativa |
|------|---------|---------------|
| 10:05 | Consolidar rules em `.copilot-rules-enterprise-python-n8n-tunning.md` | Arquivo estava com rules defasadas (scaffold-only) |

---

## Pendências Sessão 1 (10h – ≈14h)

- [ ] Revisar `docs/mcp-questions.yaml` — sincronizar com `objetivo.yaml`
- [ ] Refazer fluxo Speckit: `speckit.specify → clarify → plan → checklist → tasks → analyze → implement`
- [ ] Commitar `docs/objetivo.yaml` pendente

---

## Log de Atividades — Sessão 2 (≈14h–16h45)

### [14:00] Session Recovery — Contexto recuperado

Sessão anterior bloqueada em T017 (VictoriaMetrics sem porta exposta).
`docs/SESSIONS/2026-04-02/SESSION_RECOVERY_2026-04-02.md` gerado com estado.
Arquivo `.secrets/n8n_db_wfdb02.json` corrigido de formato ENV para JSON válido.

### [14:15] T017 — Gate F16 em wfdb01 — ✅ Concluído

**Artefatos criados/modificados**:
| Arquivo | O que mudou |
|---------|-------------|
| `docs/SESSIONS/2026-04-02/T017_GATE_F16_EVIDENCE.md` | Criado — evidência BEFORE/AFTER F16 wfdb01 |
| `docs/SESSIONS/2026-04-02/gate-evidence-f16-20260402T185642Z.json` | JSON de métricas coletadas |
| `specs/001-001-tunning-instrumentacao/tasks.md` | T017 marcado [X] |

**Destaques**: VictoriaMetrics (porta 8428) não exposta ao host — evidência coletada via endpoint HTTPS Traefik `https://testn8n.vya.digital`.

### [14:30] .secrets/n8n_db_wfdb02.json — Correção formato

Arquivo estava em formato ENV (KEY=VALUE), convertido para JSON válido com tipos corretos (port/pool_size como integers).

**Credenciais confirmadas**:
- Host: `82.197.64.145` | Port: `5432` (direto, não PgBouncer)
- Database DEV: `n8n_dev_db` | Database PROD: `n8n_db`
- User: `n8n_user`

### [15:00] T025 — Gate F17 Vetor A em wfdb01 — 🔄 Em Progresso

**Evidência BEFORE coletada** do `n8n_dev_db` em wfdb02:
- `execution_entity`: **415 linhas**, **1184 kB**

**Artefatos criados/modificados**:
| Arquivo | O que mudou |
|---------|-------------|
| `ansible/inventory/group_vars/wfdb02.yml` | CRIADO — db_host/db_port/db_name corretos para wfdb02 |
| `ansible/playbooks/f17-postgres-tuning.yml` | Refatorado: play names quoted (YAML fix), plays usam `import_role tasks_from`, Play 5 com `when` removido do play |
| `ansible/roles/postgres_tuning/tasks/main.yml` | `include_tasks` → `import_tasks` |
| `ansible/roles/postgres_tuning/tasks/f17_prune.yml` | `n8n_f16_enabled: true` (preserva F16), template path corrigido para `role_path/../n8n_env/templates/` |

**Bugs corrigidos nesta fase**:
- YAML syntax: `name: F17 — Vetor A: EXECUTIONS_DATA_PRUNE` → quoted (colon issue)
- Tag filtering: `include_tasks` → `import_role tasks_from` por play
- Template not found: `src: docker-compose.override.j2` → caminho absoluto via `role_path`
- F16 overwrite: `n8n_f16_enabled: false` → `true` em f17_prune.yml

**Estado**: dry-run (`--check --diff`) passou em assert/stat tasks; playbook pendurado na task de template (provavelmente wait_for porta 5001 após restart). **Não aplicado em produção ainda.**

---

## Decisões do Dia (Sessão 2)

| Hora | Decisão | Justificativa |
|------|---------|---------------|
| 15:10 | Usar `import_role tasks_from` em vez de `role:` nas plays | Tag filtering correta com import estático |
| 15:20 | Template path via `role_path/../n8n_env/templates/` | f17_prune.yml está em postgres_tuning mas template está em n8n_env |
| 15:25 | `n8n_f16_enabled: true` em f17_prune | override F17 não deve remover F16 já activo |
| 15:30 | Porta direta 5432 para grupo wfdb02 | Playbook usa pg_dump que precisa conexão direta, não PgBouncer |

---

## Pendências Sessão 2

- [ ] **T025 — F17 prune aplicar**: playbook wait_for após restart precisa timeout maior ou porta alternativa (5001 pode não estar aberta externamente). Executar manualmente via `~/.local/bin/ssh-wfdb01`.
- [ ] **T025 — verify AFTER**: após override aplicado, confirmar N8N reiniciou com `EXECUTIONS_DATA_PRUNE=true`.
- [ ] **T025 — purge_execution_entity**: `PG_USER=n8n_user PG_PASSWORD=... python src/purge_execution_entity.py --db-host 82.197.64.145 --db-port 5432 --db-name n8n_dev_db --check-only`
- [ ] **T026 — Vetor B home011**: `ansible-playbook f17-postgres-tuning.yml --tags f17-setup-dev -l home011`
- [ ] **T029-T034**: gates F18 e promoção wf001 — depende T025+T026

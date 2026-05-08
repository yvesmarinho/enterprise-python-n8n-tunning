# DAILY_ACTIVITIES — 2026-05-08

**Projeto**: enterprise-python-n8n-tunning
**Branch**: 001-001-tunning-instrumentacao
**Data**: 2026-05-08

---

## Início de Sessão

| Campo | Valor |
|-------|-------|
| Hora de início | 2026-05-08 (manhã) |
| Git HEAD | `05dbf60` |
| Working tree | clean |
| Contexto recuperado de | `docs/SESSIONS/2026-05-05/FINAL_STATUS_2026-05-05.md` |

### Status ao Iniciar
- ✅ Sessão anterior (2026-05-05) finalizada com sucesso
- ✅ T034a dry-run validado, Bug #3 corrigido
- ⚠️ Janela de manutenção T034a agendada para **2026-05-10 02:00–04:00 UTC** (em 2 dias)
- 🔴 T034b bloqueado (prod-collector-api)

---

## Log de Atividades

<!-- Registrar atividades abaixo com timestamp e status -->

### [SESSION-START] Inicialização da Sessão

### [11:30-11:55 BRT] Avaliação de Desempenho N8N 2.19.5

**Contexto**: N8N atualizado para 2.19.5 em wf001; stack Prometheus com gaps; nova avaliação solicitada.

**Dados coletados via SSH SPA (wf001 + wfdb01 + wfdb02)**:
- N8N 2.19.5 confirmado em wf001 — 8 containers, uptime ~13h
- wfdb01 ainda em 2.19.1 — upgrade aplicado apenas em produção
- Arquitetura de fila: Bull/Redis → **RabbitMQ** (`N8N_QUEUE_MODE=rabbitmq`)
- PostgreSQL: 5.049 execuções em 24h via execution_entity

**Throughput (24h)**: sucesso 89.8% | erros 5.8% | pico 141 exec/h às 09h BRT

**Achados críticos**:
1. 🔴 **256 execuções stuck em `waiting`** — workflow `hub-whatsapp-api-gateway-evolution-api` parado desde 2026-05-04 (4+ dias)
2. 🔴 **Prometheus target N8N DOWN** — porta 5678 bloqueada por firewall (zero dados históricos)
3. 🟠 **CPU instável workers** — worker-3 a 123%, worker-2 a 55% (rotação hot-worker)
4. 🟡 **133 webhook crashes** com duração média 4.4h (sem EXECUTIONS_TIMEOUT configurado)

**Artefatos**:
- `src/collect_perf_2_19_5.py` — coleta automatizada (para execuções futuras)
- `src/analyze_perf_2_19_5.py` — análise com dados inline coletados na sessão
- `tmp/perf_analysis_2_19_5_20260508_145003.json` — JSON completo da avaliação
- **Status**: ✅ CONCLUÍDO
- **Ação**: Criação de documentos de sessão (`SESSION_RECOVERY`, `DAILY_ACTIVITIES`)
- **Artefatos**:
  - `docs/SESSIONS/2026-05-08/SESSION_RECOVERY_2026-05-08.md` ✅
  - `docs/SESSIONS/2026-05-08/DAILY_ACTIVITIES_2026-05-08.md` ✅

---

### [12:00-12:30 BRT] F16 Revisado — Análise de Obsolescência Bull/Redis

**Status**: ✅ CONCLUÍDO
**Contexto**: F16 original (Bull queue metrics) baseado em Bull/Redis — arquitetura migrada para RabbitMQ.
**Ação**: Investigação completa da compatibilidade do F16 com N8N_QUEUE_MODE=rabbitmq. Levantamento de 7 evidências técnicas demonstrando que Bull/Redis não é mais a fila de execução do N8N.
**Resultado**: F16 declarado obsoleto para arquitetura atual; nova opção A proposta — kbudde/rabbitmq-exporter.
**Decisão técnica (D-20260508-01)**: Implementar kbudde/rabbitmq-exporter v0.29.0 como substituto do F16 para homologação em wfdb01.

---

### [12:30-13:40 BRT] F16 Revisado — Deploy RabbitMQ Exporter em wfdb01

**Status**: ✅ CONCLUÍDO
**Ação**: Criação completa do role Ansible `rabbitmq_exporter` com playbook de deploy, template Docker Compose e integração com Prometheus.

**Artefatos criados/modificados**:
| Arquivo | O que mudou |
|---------|-------------|
| `ansible/roles/rabbitmq_exporter/defaults/main.yml` | Criado — defaults do role (image, ports, user) |
| `ansible/roles/rabbitmq_exporter/tasks/main.yml` | Criado — include de deploy_exporter + update_prometheus |
| `ansible/roles/rabbitmq_exporter/tasks/deploy_exporter.yml` | Criado + 4 revisões — lógica de deploy, criação de usuário monitoring, validação via curlimages/curl |
| `ansible/roles/rabbitmq_exporter/tasks/update_prometheus.yml` | Criado — blockinfile scrape job + SIGHUP reload |
| `ansible/roles/rabbitmq_exporter/templates/docker-compose.rabbitmq-exporter.j2` | Criado — template override para kbudde/rabbitmq-exporter |
| `ansible/playbooks/f16-rabbitmq-exporter.yml` | Criado — playbook completo com SPA knock, deploy, rollback |
| `ansible/playbooks/audit-infra-wfdb01.yml` | Criado — playbook de auditoria via slurp |
| `ansible/inventory/group_vars/wfdb01.yml` | Atualizado — vars rabbitmq, prometheus, exporter |
| `ansible/ansible.cfg` | Atualizado — adicionado `-i ~/.ssh/id_rsa` em ssh_args |
| `scripts/tmp/rabbitmq-exporter-vars.yml` | Criado (gitignored) — senha exporter |

**Problemas resolvidos durante a sessão**:
1. `ansible.cfg` errado: sistema carregava `/etc/ansible/ansible.cfg` → fix: `ANSIBLE_CONFIG=ansible/ansible.cfg`
2. SSH key ausente: `/etc/ansible/keys/archaris_key` não existe → fix: `-i ~/.ssh/id_rsa` em ssh_args
3. `when: rmq_override_deploy.changed` pulava `docker compose up` → fix: removed `when`
4. `wget` inexistente no container Go binary → fix: `docker run --rm curlimages/curl:8.7.1`
5. 401 Unauthorized: usuário `dialer` sem tag `monitoring` + não existe em wfdb01 → fix: task `rabbitmqctl add_user` + `set_user_tags monitoring` + `set_permissions`

**Resultado final**:
- Container `rabbitmq-exporter` UP em wfdb01, porta 9419
- Métricas `rabbitmq_queue_*` confirmadas via assert
- Scrape job adicionado ao prometheus.yaml e Prometheus recarregado via SIGHUP
- Playbook idempotente: `ok=18, changed=4, failed=0`

---

## Sumário do Dia

| Métrica | Valor |
|---------|-------|
| Atividades concluídas | 3 (avaliação perf + análise F16 + deploy F16 revisado) |
| Atividades bloqueadas | 1 (T034b — aguarda prod-collector-api) |
| Commits realizados | 1 (session-end) |
| Artefatos criados | 12 (roles, tasks, templates, playbooks, scripts) |
| Artefatos modificados | 4 (ansible.cfg, wfdb01.yml, TODO.md, mcp.json) |

---

*Atualizado continuamente durante a sessão. Seção de sumário preenchida no `session-end`.*

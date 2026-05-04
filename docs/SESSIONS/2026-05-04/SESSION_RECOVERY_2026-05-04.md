# 🔄 Session Recovery — 2026-05-04

**Projeto**: enterprise-python-n8n-tunning
**Branch**: `001-001-tunning-instrumentacao`
**Última sessão**: 2026-04-30 (intervalo: 4 dias)
**Recovery timestamp**: 2026-05-04T14:35Z

---

## Contexto Recuperado

### MCP Configuration Status
✅ MCP Config OK — `memory` ✅ | `sequential-thinking` ✅

### Project Rules Loaded
- ✅ `.copilot-rules-enterprise-python-n8n-tunning.md` (Layer 1 — base rules)
- ✅ `.github/copilot-instructions.md` (project-specific instructions)
- ✅ Domain Profile: `devops-analysis.prompt.md` (default mode)

### P0 Rules Confirmed in Memory
| Regra | Status |
|-------|--------|
| P0: Nunca heredoc/echo para criar arquivos | ✅ |
| P0: Nunca cat/grep/find/ls via terminal (usar ferramentas nativas) | ✅ |
| P0: 3+ arquivos → Python + JSON para mover | ✅ |
| P0: Git com arquivo de mensagem (≥6 linhas) | ✅ |
| P1: Docs de sessão em `docs/SESSIONS/YYYY-MM-DD/` | ✅ |

---

## Security Scan
🟢 **LIMPO** — nenhum arquivo sensível fora de `.secrets/`
✅ `.secrets/` está no `.gitignore`

---

## Git Repository Status

**Branch**: `001-001-tunning-instrumentacao`
**Last commit**: `735a833` — docs(analysis): Análise de lentidão N8N concluída + T034a runbook
**Working tree**: Modified files:
- `docs/TODO.md` (not staged)

**Recent commits** (last 5):
1. `735a833` — docs(analysis): Análise de lentidão N8N concluída + T034a runbook
2. `3a5b8a8` — docs(session-2026-04-08): end.session — DAILY_ACTIVITIES, SESSION_REPORT, TODO, CHAT
3. `7073fef` — feat(t034a/t035/t036): lint playbook wf001, corrigir validate_prometheus, evidências T036
4. `f25754f` — chore(sessions): artefatos das sessões 2026-04-07 e 2026-04-08
5. `5b102c2` — feat(session-2026-04-06): hardening runbook, DB boundary propagation, ProvenanceGate evidence, issue #15

---

## Estado do Projeto (Última Sessão: 2026-04-30)

### Análise de Lentidão N8N — ✅ CONCLUÍDA

**Pergunta central**: Por que o N8N está lento tanto nos workflows quanto na operação?

**Resposta**: Workflows individuais **SÃO rápidos** (p95 < 100ms). Lentidão percebida é **TEMPO DE FILA não instrumentado**.

**Diagnóstico estruturado**:
1. ✅ Hardware NÃO é gargalo — CPU wf001: 1-3%
2. ✅ Workflows NÃO são lentos — p95 < 100ms em 100% das execuções
3. 🔴 **Hipótese principal: Fila N8N saturada** — 2.3 exec/s por 9h (121Labs PABX)
4. 🟠 **Hipótese secundária: PostgreSQL saturado** — 429K+ linhas execution_entity

**Ofensores de volume**:
- **121Labs PABX call-analytics**: 429K exec/90d (57%), pico 8.4K/hora
- **hub-whatsapp-api-gateway-evolution-api**: 84K exec desde 04/mar (+1860%)

**Lacunas críticas de instrumentação**: 6
- F16 (queue metrics), F20 (probe end-to-end), F22 (buckets sub-100ms)
- F23 (memória wf001), F24 (concurrency), F17 Vetor B (pg_stat_statements prod)

---

## Itens P0 Pendentes (do TODO.md)

### 🔴 P0 — Próxima Sessão (executar na ordem)

1. ⬜ **T034a execução** — promoção F16+F17 para wf001
   - **Janela agendada**: sábado 02h–04h UTC
   - **Pré-requisitos**: todos ✅
   - **Playbook**: `ansible/playbooks/t034a-promote-f16-f17-wf001.yml`
   - **Action**: Dry-run primeiro: `ansible-playbook ... --check --diff`

2. ⬜ **T034b** — promoção F18 para wf001
   - **Bloqueio**: prod-collector-api precisa corrigir `PROMETHEUS_PUSHGATEWAY_ENABLED=false`
   - **Dependência**: KNOWN_ISSUE_F18

3. ⬜ **Submeter issue F18 ao projeto responsável**
   - **Artefato pronto**: `specs/001-001-tunning-instrumentacao/contracts/prod-collector-api-issue.md`
   - **Ação**: Abrir issue no repositório prod-collector-api

### 🔵 P1 — Pendente

- ⬜ **Revisar `docs/mcp-questions.yaml`** — sincronizar com atualizações de `objetivo.yaml`
- ⬜ **T032–T034** — gates AFTER wfdb01 + promoção em bloco wf001 (aguarda T025+T026)

---

## Estado das Features (Instrumentação e Tunning)

### Features P1 — wfdb01 (desenvolvimento/teste)

| Feature | Status | Gate | Observação |
|---------|--------|------|------------|
| F16 | ✅ validado | T025 ✅ | Queue metrics habilitadas |
| F17 Vetor A | ✅ validado | T025 ✅ | purge_execution_entity.py --check-only OK |
| F17 Vetor B | ✅ validado | T026 ✅ | pg_stat_statements em n8n_dev_db |
| F18 | ⚠️ KNOWN_ISSUE | T029 ✅ | Dual-collection confirmada; aguarda correção |

### Features P1 — wf001 (produção)

| Feature | Status | Bloqueio | Ação |
|---------|--------|----------|------|
| F16 | ⬜ pendente | T034a agendado | Janela sábado 02h-04h UTC |
| F17 | ⬜ pendente | T034a agendado | Janela sábado 02h-04h UTC |
| F18 | ⬜ bloqueado | Correção externa | Aguarda prod-collector-api fix |

---

## Artefatos da Última Sessão (2026-04-30)

| Arquivo | Descrição |
|---------|-----------|
| `docs/SESSIONS/2026-04-30/ANALYSIS_SLOWNESS_N8N_2026-04-30.md` | Relatório consolidado de análise |
| `docs/SESSIONS/2026-04-30/n8n-slowness-analysis-20260430-113529.json` | Resultado estruturado (JSON) |
| `docs/SESSIONS/2026-04-30/T034a_RUNBOOK_MANUTENCAO.md` | Runbook para janela de manutenção |
| `src/analyze_n8n_slowness.py` | Script análise consolidada ANA-001 |
| `src/collect_n8n_metrics_7d.py` | Script coleta VictoriaMetrics (não executado) |
| `tmp/check_execution_entity.py` | Script PostgreSQL (execução pendente) |

---

## Recomendações para Esta Sessão

### Foco Sugerido: DEVOPS-ENGINEER

**Ações prioritárias**:

1. **Finalizar preparação T034a**:
   - Confirmar janela de manutenção (sábado 02h–04h UTC ainda válida?)
   - Executar dry-run completo do playbook
   - Validar backup de `docker-compose.yml` e `.env` em wf001
   - Confirmar comunicação com stakeholders

2. **Avançar T034b (se possível)**:
   - Verificar se prod-collector-api corrigiu o flag
   - Se sim: criar playbook análogo para F18
   - Se não: submeter issue formal

3. **Atualizar documentação**:
   - `docs/mcp-questions.yaml` ↔ `docs/objetivo.yaml` sincronização
   - Registrar decisões em `docs/copilot/CHAT-*` conforme necessário

---

## Pendências Identificadas

- ⚠️ **T033r** — ProvenanceGate aguarda prod-collector-api corrigir `PROMETHEUS_PUSHGATEWAY_ENABLED=false`
- ⚠️ `docs/TODO.md` possui modificações não commitadas — revisar e adicionar ao commit

---

**Recovery complete** ✅
**Session 2026-05-04 ready to start**

# 📝 Daily Activities — 2026-05-21

**Branch**: 001-001-tunning-instrumentacao
**Início**: sessão atual
**Modo de trabalho**: ANALYSIS
**Objetivo**: Coletar dados no prometheus para varificar desempenho após atualização.

---

## Timeline de Atividades

### Session Start — Ritual de Início

- ✅ MCP configurado em `.vscode/mcp.json` com servidores `memory` e `sequential-thinking`
- ✅ Contexto recuperado de `docs/TODO.md` e `docs/INDEX.md`
- ✅ Última atividade lida: `docs/SESSIONS/2026-05-14/DAILY_ACTIVITIES_2026-05-14.md`
- ✅ Último FINAL_STATUS disponível lido: `docs/SESSIONS/2026-05-11/FINAL_STATUS_2026-05-11.md`
- ✅ Regras ativas carregadas em `.copilot-rules-enterprise-python-n8n-tunning.md`
- ✅ Security scan executado (padrões sensíveis)
- ✅ Estado do Git verificado (`git status` + `git log -5`)
- ✅ `SESSION_RECOVERY_2026-05-21.md` criado
- ✅ `DAILY_ACTIVITIES_2026-05-21.md` criado
- ✅ Modo declarado: ANALYSIS
- ✅ Domain Profile carregado: `.github/prompts/domain/devops-analysis.prompt.md`
- ✅ Objetivo declarado: coletar dados no Prometheus para verificar desempenho após atualização

### Análise Pós-Upgrade N8N 2.19.5 (08/05/2026)

- ✅ Execução de `src/assess_n8n_v2195_performance.py` para janela de 13 dias (08/05 → 21/05)
- ❌ VictoriaMetrics inacessível em `http://localhost:18428` (sem túnel ativo)
- ❌ VictoriaMetrics inacessível em `http://86.48.31.149:8428` (endpoint externo indisponível)
- ✅ Artefatos gerados:
	- `n8n-v2195-assessment-20260521-123943.json`
	- `n8n-v2195-assessment-20260521-124001.json`
- ✅ Fallback executado via `src/check_n8n_metrics.py`:
	- `https://workflow.vya.digital` -> FAIL (endpoint acessivel, 4 metricas de fila ausentes, `raw_count=43`)
	- `https://testn8n.vya.digital` -> PASS (4/4 métricas de fila presentes, `raw_count=47`)
- ✅ Evidência consolidada em `n8n-metrics-check-20260521-124509.json`
- ✅ Correção de histórico aplicada: URL correta de produção é `workflow.vya.digital`
- ✅ Parecer técnico registrado em `PROMETHEUS_POST_UPGRADE_ANALYSIS_2026-05-21.md`
- ✅ Script enviado via SCP e executado em `wfdb01` para checar VM (`scripts/tmp/vm_history_check.py`)
- ⚠️ VM respondeu dentro do container (`query=1`), mas query histórica de `n8n_workflow_executions_total` retornou vazio
- ✅ Coleta direta de métricas em produção mostrou 43 métricas `n8n_*`, incluindo `n8n_workflow_execution_duration_seconds_*`
- ❌ Métrica `n8n_workflow_executions_total` ausente em produção
- ❌ Métricas de fila `n8n_scaling_mode_queue_jobs_*` ausentes em produção
- ✅ Novo script remoto (`scripts/tmp/vm_query_via_container.py`) executado via SCP+SSH com encode de PromQL
- ✅ Evidência local coletada: `tmp/vm_query_via_container_20260521_131939.json`
- ❌ Histórico VM para as métricas-alvo não confirma retenção útil:
	- `increase(...executions_total[2d|7d])` => vazio
	- `increase(...execution_duration_seconds_count[2d|7d])` => vazio
	- janelas 30d => valor `0`
- ⚠️ Apenas séries `collector_api_wf001_usa*` apareceram em 30d (instance `0.0.0.0:5000`), ambas com valor `0`
- ✅ Correção de configuração no repositório: `ansible/inventory/group_vars/wf001.yml` atualizado para `https://workflow.vya.digital`
- ✅ Script de auditoria de targets (`scripts/tmp/prometheus_targets_audit.py`) executado com saída JSON
- ✅ Evidência de targets: `prometheus-targets-audit-20260521-132724.json`
- 🔴 Causa confirmada: target `job=n8n` em `DOWN` no Prometheus (`31.220.103.208:5678/metrics` -> `connection refused`)
- ✅ Interpretação: histórico curto no VM não é retenção de 2 dias, é falha de ingestão do target N8N
- ✅ Script adicional de diagnóstico runtime (`scripts/tmp/prometheus_n8n_scrape_diagnose.py`) executado via SCP+SSH com saída JSON
- ✅ Evidência local coletada: `tmp/prometheus_n8n_scrape_diagnose_20260521_135803.json`
- ✅ Confirmação no runtime do Prometheus: `job_name: "n8n"` ainda aponta para `31.220.103.208:5678`
- ✅ Teste comparativo de conectividade (wfdb01):
	- `http://31.220.103.208:5678/metrics` -> `connection refused`
	- `https://workflow.vya.digital/metrics` -> `HTTP 200`
- ✅ Plano técnico mapeado: alterar scrape `n8n` para `workflow.vya.digital:443` com `scheme: https`, recarregar Prometheus e validar target `UP`
- ✅ Código gerado para execução robusta sem pipeline: `scripts/tmp/run_prometheus_n8n_fix_flow.py`
- ✅ Código validado (py_compile) e executado via Python local
- ✅ Evidência consolidada: `tmp/prometheus_n8n_fix_flow_20260521_143853.json`
- ✅ Evidência de fix: `tmp/prometheus_n8n_scrape_fix_20260521_143840.json`
- ✅ Evidência de auditoria pós-fix: `tmp/prometheus_targets_audit_20260521_143849.json`
- ✅ Resultado: target `job=n8n` em `UP` com `scrapeUrl=https://workflow.vya.digital:443/metrics`
- ✅ Recoleta VM pós-fix executada por script sem pipeline: `scripts/tmp/run_vm_query_after_fix_flow.py`
- ✅ Evidências geradas: `tmp/vm_query_after_fix_flow_20260521_145127.json` e `tmp/vm_query_via_container_20260521_145123.json`
- ✅ Resultado VM atualizado:
	- `dur_count_2d=28`, `dur_count_7d=28`, `dur_count_30d=28`
	- `exec_total_2d=EMPTY`, `exec_total_7d=EMPTY`, `exec_total_30d=0`
- ✅ Interpretação: ingestão N8N voltou a aparecer para `...duration_seconds_count`; consultas por `...executions_total` seguem incompatíveis com o endpoint/ambiente atual
- ✅ Issue aberta no projeto de dashboards: `https://github.com/yvesmarinho/enterprise-observability-dashboards/issues/1`
- ✅ Nova coleta pós-fix executada para comparação histórica: `tmp/vm_query_after_fix_flow_20260521_151917.json`
- ✅ Conclusão formal da análise registrada em: `docs/SESSIONS/2026-05-21/ANALYSIS_CONCLUSION_2026-05-21.md`

## Próximos Passos

1. Ajustar queries/dashboards para usar `n8n_workflow_execution_duration_seconds_count` como série principal de execução histórica
2. Investigar ausência de `n8n_scaling_mode_queue_jobs_*` em `workflow.vya.digital/metrics`
3. Revisar origem das séries `collector_api_*` com incremento 30d = 0

### Session End — Consolidação

- ✅ Encerramento da análise da sessão formalizado em `ANALYSIS_CONCLUSION_2026-05-21.md`
- ✅ Issue no projeto dedicado de dashboards aberta para correções de visualização/queries:
	- `https://github.com/yvesmarinho/enterprise-observability-dashboards/issues/1`
- ✅ Evidência comparativa mais recente coletada e registrada:
	- `tmp/vm_query_after_fix_flow_20260521_151917.json`
	- `tmp/vm_query_via_container_20260521_151914.json`
- ✅ Atualizações documentais executadas:
	- `docs/TODO.md`
	- `docs/INDEX.md`
	- `docs/SESSIONS/2026-05-21/FINAL_STATUS_2026-05-21.md`
- ⚠️ Diretório `tmp/` não limpo neste encerramento para preservar evidências usadas no relatório e permitir retomada imediata da análise comparativa na próxima sessão.

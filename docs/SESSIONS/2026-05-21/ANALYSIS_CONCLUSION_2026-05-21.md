# Analysis Conclusion — 2026-05-21

## Escopo desta conclusão
- Objetivo da sessão: analise de observabilidade/performance do N8N apos upgrade para 2.19.5.
- Fora de escopo: implementacao de dashboards neste repositorio.

## Encaminhamento para projeto de dashboards
- Issue criada em projeto dedicado: https://github.com/yvesmarinho/enterprise-observability-dashboards/issues/1
- Repo alvo: `enterprise-observability-dashboards`
- Tema: corrigir queries para usar serie historica disponivel (`n8n_workflow_execution_duration_seconds_count`) com fallback/compatibilidade.

## Coleta atual (pos-fix)
- Fluxo executado: `scripts/tmp/run_vm_query_after_fix_flow.py`
- Evidencia consolidada: `tmp/vm_query_after_fix_flow_20260521_151917.json`
- Evidencia detalhada VM: `tmp/vm_query_via_container_20260521_151914.json`

Resumo da coleta atual:
- `exec_total_2d = EMPTY`
- `exec_total_7d = EMPTY`
- `exec_total_30d = 0`
- `dur_count_2d = 37`
- `dur_count_7d = 37`
- `dur_count_30d = 37`

## Comparacao com historico do projeto (ANA-001)
Referencia historica:
- Documento: `docs/n8n_perf_ANA001_20260101_20260331_20260331T154646.md`
- Janela: 2026-01-01 a 2026-03-31 (90 dias)
- Baseline principal:
  - Execucoes `job=n8n, instance=wf001`: 148.058
  - Execucoes `collector_api_wf001_usa`: 366.303
  - 23 workflows ativos
  - p95 individual < 0,1s

Comparativo tecnico:
1. Antes (ANA-001): havia volumetria historica robusta para execucoes totais em series de contagem.
2. Agora (pos-fix): a serie `n8n_workflow_executions_total` permanece indisponivel/nao confiavel no recorte atual (`EMPTY/0`).
3. Agora (pos-fix): a serie `n8n_workflow_execution_duration_seconds_count` voltou a apresentar incremento consistente (37), indicando ingestao util apos restauracao do target `n8n`.
4. Implicacao analitica: para continuidade da analise de tendencia no contexto atual, `...duration_seconds_count` deve ser tratada como serie primaria operacional.

## Conclusao da analise
- A causa-raiz do historico "curto" foi operacional (target `job=n8n` em DOWN), ja resolvida.
- A ingestao foi restabelecida (target UP) e a coleta atual confirma retorno de sinal para `...duration_seconds_count`.
- Persistiu incompatibilidade/ausencia pratica de `...executions_total` no estado atual do ambiente.
- Portanto, a analise deve prosseguir baseada em `n8n_workflow_execution_duration_seconds_count` ate normalizacao completa da superficie de metricas.

## Recomendacoes imediatas (analise)
1. Padronizar consultas analiticas deste projeto para `sum(increase(n8n_workflow_execution_duration_seconds_count[janela]))`.
2. Manter rastreio de `n8n_workflow_executions_total` apenas como controle de compatibilidade.
3. Repetir coleta diaria por 3-7 dias para validar estabilidade do incremento em `dur_count`.

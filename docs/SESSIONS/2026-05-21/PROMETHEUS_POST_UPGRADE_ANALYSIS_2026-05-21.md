# Prometheus Post-Upgrade Analysis — 2026-05-21

## Contexto
- Upgrade confirmado: N8N 2.19.5 em 2026-05-08.
- Janela analisada: 2026-05-08 a 2026-05-21 (13 dias).
- Objetivo: coletar evidencias no Prometheus/VictoriaMetrics para avaliar desempenho apos atualizacao.

## Evidencias coletadas

### 1) Avaliacao pos-upgrade via VictoriaMetrics
- Script: `src/assess_n8n_v2195_performance.py`
- Tentativas:
  - `--vm-url http://localhost:18428` (esperando tunel SSH) -> falha
  - `--vm-url http://86.48.31.149:8428` (endpoint externo) -> falha
- Resultado comum:
  - `vm_reachable=false`
  - `error="VictoriaMetrics inacessivel"`
- Artefatos:
  - `docs/SESSIONS/2026-05-21/n8n-v2195-assessment-20260521-123943.json`
  - `docs/SESSIONS/2026-05-21/n8n-v2195-assessment-20260521-124001.json`

### 2) Fallback de metrica direto no endpoint N8N
- Script: `src/check_n8n_metrics.py`
- Produção (`https://workflow.vya.digital`) -> endpoint acessivel, mas com ausencia das 4 metricas de fila esperadas
- Teste (`https://testn8n.vya.digital`) -> sucesso, 4/4 metricas de fila encontradas
- Artefato consolidado:
  - `docs/SESSIONS/2026-05-21/n8n-metrics-check-20260521-124509.json`

### 3) Correcao de historico operacional
- URL de producao correta do N8N: `https://workflow.vya.digital`.
- A referencia anterior a `https://n8n.vya.digital` foi corrigida nos artefatos desta sessao.

### 4) Achado de compatibilidade de metricas (causa-raiz provavel)
- Coleta direta em `https://workflow.vya.digital/metrics` retornou 43 nomes `n8n_*`.
- A metrica `n8n_workflow_executions_total` NAO esta presente no endpoint atual.
- As metricas de fila `n8n_scaling_mode_queue_jobs_*` tambem NAO estao presentes em producao.
- A familia `n8n_workflow_execution_duration_seconds_{bucket,count,sum}` continua presente.
- Implicacao: consultas historicas baseadas em `n8n_workflow_executions_total` tendem a retornar vazio e passam a sugerir, incorretamente, que o historico caiu para janelas muito curtas.

### 5) Validacao direta no VictoriaMetrics (via container em wfdb01)
- Metodo: script remoto executado por `scp + ssh` com queries via `docker exec enterprise-victoriametrics`.
- Evidencia: `tmp/vm_query_via_container_20260521_131939.json`.
- Resultado:
  - `sum(increase(n8n_workflow_executions_total[2d]))` -> vazio
  - `sum(increase(n8n_workflow_executions_total[7d]))` -> vazio
  - `sum(increase(n8n_workflow_executions_total[30d]))` -> 0
  - `sum(increase(n8n_workflow_execution_duration_seconds_count[2d]))` -> vazio
  - `sum(increase(n8n_workflow_execution_duration_seconds_count[7d]))` -> vazio
  - `sum(increase(n8n_workflow_execution_duration_seconds_count[30d]))` -> 0
  - `sum by (job,instance) (...) [30d]` retornou apenas:
    - `job=collector_api_wf001_usa, instance=0.0.0.0:5000` com valor 0
    - `job=collector_api_wf001_usa_ping_data, instance=0.0.0.0:5000` com valor 0
- Leitura tecnica: nao ha evidencia de ingestao historica util para as series N8N analisadas no VM atual; o problema observado nao e "retencao de 2 dias", e sim ausencia (ou zero) de dados relevantes na fonte monitorada.

### 6) Auditoria de targets do Prometheus (causa-raiz confirmada)
- Metodo: script Python versionado + `scp` + execucao remota no wfdb01.
- Evidencia: `docs/SESSIONS/2026-05-21/prometheus-targets-audit-20260521-132724.json`.
- Resultado:
  - `job=n8n`, `instance=wf001` -> `health=down`
  - `scrapeUrl=http://31.220.103.208:5678/metrics`
  - `lastError=connection refused`
  - `job=pushgateway_wfdb01` -> `health=up`
- Conclusao: o historico N8N nao aparece no VictoriaMetrics porque o scrape primario de N8N esta fora do ar no Prometheus; nao e um problema de retencao de 2 dias.

### 7) Mapeamento do scrape runtime e proposta objetiva de correcao
- Metodo: script remoto `scripts/tmp/prometheus_n8n_scrape_diagnose.py` com saida JSON.
- Evidencia: `tmp/prometheus_n8n_scrape_diagnose_20260521_135803.json`.
- Achados:
  - O `prometheus.yml` runtime no container `enterprise-prometheus` contem:
    - `job_name: "n8n"`
    - `targets: ["31.220.103.208:5678"]`
    - `metrics_path: /metrics`
  - Teste de conectividade no host `wfdb01`:
    - `http://31.220.103.208:5678/metrics` -> `connection refused`
    - `https://workflow.vya.digital/metrics` -> `HTTP 200`
- Mapeamento tecnico para remediacao minima:
  - Trocar o alvo do `job_name: "n8n"` para `workflow.vya.digital:443` com `scheme: https`.
  - Manter `metrics_path: /metrics`, labels e intervalos atuais.
  - Recarregar Prometheus via `SIGHUP` e validar `job=n8n` em `health=up` na API de targets.

## Analise tecnica

### Fatos observados
- A coleta historica no VictoriaMetrics nao avancou hoje por falta de conectividade.
- O endpoint de teste expoe metricas de fila compativeis com N8N 2.19.5.
- O endpoint de producao correto (`workflow.vya.digital`) responde, porem sem metricas de fila esperadas.
- A validacao dentro do container VictoriaMetrics mostra apenas series de `collector_api_*` com incremento 30d igual a zero e sem series `job=n8n` nas consultas-alvo.
- O Prometheus confirma `job=n8n` em estado DOWN por `connection refused` na URL `31.220.103.208:5678/metrics`.

### Inferencias
- O stack de metricas continua funcional em ambiente de teste (instrumentacao ativa).
- A lacuna para concluir a analise de desempenho em producao combina fator operacional (acesso) + proveniencia incorreta/insuficiente de series no VM.
- Existe mudanca de superficie de metricas em producao (ou diferenca de configuracao por ambiente), com impacto direto nas queries de historico usadas ate aqui.
- Sem target `job=n8n` UP, o VictoriaMetrics recebe no maximo dados indiretos (`collector_api_*`), que hoje estao zerados para janela 30d.

### Limites da conclusao
- Sem acesso ao VictoriaMetrics, nao foi possivel calcular delta de throughput/latencia pos-upgrade em producao.
- A validacao direta em producao foi parcial: endpoint acessivel, mas sem as metricas de fila-alvo.

## Prioridade de acao
1. P0: Restaurar `job=n8n` para `UP` no Prometheus (corrigir endpoint/porta/rede em `31.220.103.208:5678/metrics`).
2. P0: Validar por que o endpoint de producao nao expoe `n8n_scaling_mode_queue_jobs_*`.
3. P0: Revisar origem `collector_api_*` (Pushgateway) com incremento 0 em 30d.
4. P1: Reexecutar analise historica apos `job=n8n` voltar a `UP`.
5. P1: Ajustar dashboards/queries para metrica disponivel ate estabilizar a superficie final.

## Veredito desta etapa
- Status: `ROOT_CAUSE_IDENTIFIED` para o problema de historico curto.
- Motivo: `job=n8n` DOWN no Prometheus (connection refused), portanto sem ingestao historica primaria no VictoriaMetrics.
- Confianca da conclusao: alta para causa de observabilidade; media para impacto funcional de fila ate concluir investigacao de metricas ausentes.

## Atualizacao de remediacao (2026-05-21 14:38 UTC)
- Fluxo de correcao executado por script Python sem pipeline shell:
  - `scripts/tmp/run_prometheus_n8n_fix_flow.py`
- Evidencias geradas:
  - `tmp/prometheus_n8n_fix_flow_20260521_143853.json`
  - `tmp/prometheus_n8n_scrape_fix_20260521_143840.json`
  - `tmp/prometheus_targets_audit_20260521_143849.json`
- Resultado tecnico:
  - Target `job=n8n` agora em `health=up`.
  - `scrapeUrl=https://workflow.vya.digital:443/metrics`.
  - `lastError` vazio no target `n8n`.
- Observacao:
  - O script de fix encontrou configuracao ja ajustada (`would_change=false`), indicando que a alteracao do scrape ja estava persistida no runtime/file de configuracao durante esta janela de validacao.

## Recoleta VictoriaMetrics apos target `n8n` UP (2026-05-21 14:51 UTC)
- Fluxo executado por script Python sem pipeline:
  - `scripts/tmp/run_vm_query_after_fix_flow.py`
- Evidencias:
  - `tmp/vm_query_after_fix_flow_20260521_145127.json`
  - `tmp/vm_query_via_container_20260521_145123.json`
- Resultado resumido:
  - `sum(increase(n8n_workflow_execution_duration_seconds_count[2d])) = 28`
  - `sum(increase(n8n_workflow_execution_duration_seconds_count[7d])) = 28`
  - `sum(increase(n8n_workflow_execution_duration_seconds_count[30d])) = 28`
  - `sum(increase(n8n_workflow_executions_total[2d])) = EMPTY`
  - `sum(increase(n8n_workflow_executions_total[7d])) = EMPTY`
  - `sum(increase(n8n_workflow_executions_total[30d])) = 0`
- Leitura tecnica:
  - Ha sinal de ingestao para a familia `...duration_seconds_count` apos restauracao do target.
  - A familia `n8n_workflow_executions_total` permanece indisponivel/inadequada para historico neste ambiente.
  - Proximo ajuste deve priorizar queries e dashboards baseados na familia disponivel (`...duration_seconds_count`) para continuidade da analise pos-upgrade.

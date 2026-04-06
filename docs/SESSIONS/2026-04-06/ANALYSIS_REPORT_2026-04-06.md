# 🔎 Analysis Report — 2026-04-06

**Projeto**: enterprise-python-n8n-tunning
**Modo**: ANALYSIS
**Base principal**: `docs/n8n_perf_ANA001_20260101_20260331_20260331T154646.md`
**Objetivo**: analisar o cenário atual da infraestrutura e priorizar ajustes que melhorem o desempenho percebido do N8N

---

## 1. Fontes Confrontadas

- Relatório ANA-001 de performance e observabilidade
- Estado atual em `docs/TODO.md`
- Implementação existente em `ansible/playbooks/f16-queue-metrics.yml`, `ansible/playbooks/f17-postgres-tuning.yml` e `ansible/playbooks/f18-dual-collection-audit.yml`
- Scripts operacionais `src/check_n8n_metrics.py`, `src/purge_execution_entity.py` e `src/validate_prometheus.py`

---

## 2. Achados Principais

### A001 — O gargalo provável continua sendo lógico, não computacional

**Evidência**:
- ANA-001 mostra p95 individual abaixo de 100ms para todos os workflows observados
- CPU do `wf001` permanece em 1–3% mesmo durante picos
- O volume está concentrado em dois workflows: `121Labs PABX call-analytics` e `hub-whatsapp-api-gateway-evolution-api`

**Conclusão**:
A infraestrutura de host não aparece como gargalo primário. A hipótese mais forte continua sendo combinação de throughput alto com fila e custo operacional de persistência, não falta de CPU.

**Confiança**: alta

### A002 — A observabilidade ainda é o maior ponto cego operacional

**Evidência**:
- O relatório aponta ausência ou insuficiência de métricas para confirmar tempo de fila percebido
- F16 já foi levado até gate em `wfdb01`, mas a documentação mistura nomes de métricas `n8n_queue_*` com métricas reais verificadas em script (`n8n_scaling_mode_queue_jobs_*`)
- Sem uma fonte canônica de métricas e sem probe sintético, a equipe ainda mede melhor o sintoma técnico do que a latência percebida pelo cliente

**Conclusão**:
Antes de qualquer otimização estrutural maior, a prioridade correta é consolidar a medição de fila, proveniência das séries e latência fim a fim.

**Confiança**: alta

### A003 — O tema F18 está contraditório no relatório e deve ser tratado como pendente

**Evidência**:
- O ANA-001 traz trechos dizendo que o relabeling do exporter já resolveu o problema e que nenhuma ação adicional seria necessária
- O mesmo documento, em seções posteriores, afirma que a dupla coleta segue ativa via Pushgateway e scrape direto ao mesmo tempo
- O backlog do repositório e os artefatos de F18 (`T029`, `src/validate_prometheus.py`, `ansible/playbooks/f18-dual-collection-audit.yml`) assumem corretamente que o problema ainda precisa ser confirmado e fechado operacionalmente

**Conclusão**:
A interpretação segura é: **F18 não está resolvido**. O relatório deve ser lido com prioridade para as seções que tratam a dupla coleta como ativa até que T029 confirme o estado real em `wfdb01`.

**Confiança**: alta

### A004 — F17 é importante, mas ainda não há prova de gargalo no PostgreSQL; há prova de dívida operacional

**Evidência**:
- ANA-001 trata `execution_entity` volumosa como hipótese secundária de pressão no banco
- O backlog e a automação já avançaram em backup, prune e preparação de `pg_stat_statements`
- O gate de aplicação ainda não fechou, então o ganho operacional de retenção e pruning não foi materializado

**Conclusão**:
F17 deve continuar como prioridade alta por risco operacional e higiene de dados, mas não deve ser vendido como causa-raiz confirmada da lentidão percebida sem estatísticas do banco.

**Confiança**: média

### A005 — Há drift entre relatório, backlog e scripts que precisa ser resolvido antes da próxima execução

**Evidência**:
- `docs/TODO.md` e `specs/.../tasks.md` ainda citam comandos e portas divergentes para validações de F17
- `src/check_n8n_metrics.py` valida métricas `n8n_scaling_mode_queue_jobs_*`, enquanto o relatório e partes das tasks continuam falando em `n8n_queue_*`
- `src/purge_execution_entity.py` usa placeholder `$1` em `SIZE_QUERY`, incompatível com o padrão de parâmetros do psycopg2, o que torna o gate de diagnóstico arriscado antes de nova execução real

**Conclusão**:
Existe prontidão parcial de automação, mas ainda não há prontidão operacional limpa. A próxima rodada precisa começar reconciliando esses artefatos para evitar falso negativo ou falsa validação.

**Confiança**: alta

---

## 3. Priorização Recomendada

### Agora

1. Fechar a verdade operacional de F18 em `wfdb01` e tratar dupla coleta como pendência real até prova em contrário.
2. Corrigir o drift entre relatório, TODO e scripts de gate de F16/F17.
3. Concluir T025 apenas depois de validar que o script de diagnóstico e a porta alvo do banco refletem o ambiente real.

### Próximo ciclo

1. Auditar funcionalmente `hub-whatsapp-api-gateway-evolution-api` para distinguir crescimento legítimo de falta de rate limiting.
2. Concluir F17 Vetor A e Vetor B para reduzir risco operacional do PostgreSQL e habilitar medição mais confiável.
3. Planejar F20 como probe sintético, porque hoje ainda não existe medição da latência percebida fim a fim.

### Médio prazo

1. Avaliar batching ou desacoplamento do workflow `121Labs PABX call-analytics`.
2. Considerar isolar cargas de alto volume em instância dedicada somente depois de consolidar métricas e eliminar a dupla coleta.
3. Refinar buckets sub-100ms apenas após resolver a observabilidade principal de fila e proveniência.

---

## 4. Sequência Técnica Sugerida

| Ordem | Ação | Dono sugerido | Gate |
|------|------|---------------|------|
| 1 | Confirmar F18 em `wfdb01` e fixar a fonte canônica das métricas | performance-analyst + devops-engineer | T029 |
| 2 | Reconciliar métricas/portas/scripts do backlog com a implementação real | devops-engineer | revisão local |
| 3 | Aplicar e validar F17 Vetor A com evidência BEFORE/AFTER | databases-engineer + devops-engineer | T025 |
| 4 | Validar `pg_stat_statements` em `wfdb02:n8n_dev_db` antes de qualquer operação em `n8n_db` | databases-engineer | T026 |
| 5 | Auditar workflow WhatsApp/Evolution API | n8n-specialist | análise funcional |
| 6 | Desenhar probe sintético e critério de aceitação | performance-analyst + project-manager | F20 |

---

## 5. Decisão Executiva

Se a equipe tiver capacidade para atacar apenas um eixo nesta sessão, o melhor investimento não é aumentar infraestrutura. O melhor investimento é **fechar a observabilidade confiável do fluxo real**: dupla coleta, fila e gate de F17. Sem isso, qualquer tuning adicional corre o risco de tratar consequência e não causa.

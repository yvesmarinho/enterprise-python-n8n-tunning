# Feature Specification: P1 Tunning e Instrumentação N8N (F16 + F17 + F18)

**Feature Branch**: `001-001-tunning-instrumentacao`
**Created**: 2026-04-02
**Status**: Active
**Input**: `docs/objetivo.yaml` — features F16, F17, F18 (ANA-001 Phase P1)

## User Scenarios & Testing *(mandatory)*

### User Story 1 — F16: Habilitação de Métricas de Fila N8N (Priority: P1)

Como engenheiro de observabilidade, quero que o N8N exponha métricas de
profundidade de fila (`n8n_queue_*`) para poder confirmar ou descartar a
hipótese de saturação de fila identificada no ANA-001.

**Why this priority**: Hipótese primária não confirmável do ANA-001 — fila
saturada pode causar lentidão percebida. Sem esta métrica, não há baseline para
as demais ações de tunning.

**Independent Test**: Após aplicar o playbook, executar
`curl http://wfdb01:5001/metrics | grep n8n_queue` deve retornar ao menos uma
série ativa. O story é completo quando a métrica aparece no VictoriaMetrics.

**Acceptance Scenarios**:

1. **Given** N8N container sem `N8N_METRICS_INCLUDE_QUEUE_METRICS`, **When** o
   playbook F16 é executado contra wfdb01, **Then** o endpoint `/metrics` expõe
   séries `n8n_queue_*` com valores numéricos.
2. **Given** métricas de fila ativas, **When** o alerta de profundidade de fila
   > threshold é disparado, **Then** aparece no Alertmanager/VictoriaMetrics em
   ≤ 2 ciclos de scrape (< 60s).
3. **Given** validação aprovada em wfdb01, **When** o playbook é promovido para
   wf001, **Then** o mesmo conjunto de métricas aparece no VictoriaMetrics com
   `instance=wf001`.

---

### User Story 2 — F17: Purgação e Tunning PostgreSQL N8N (Priority: P1)

Como DBA/engenheiro de performance, quero ativar a purgação automática de
execuções históricas e o monitoramento de queries para controlar o crescimento
da tabela `execution_entity` (atualmente 429K+ linhas) e identificar queries
lentas.

**Why this priority**: A tabela `execution_entity` com 429K+ linhas é o segundo
principal offensor de performance da stack N8N. Sem purgação, a degradação é
progressiva e irreversível.

**Independent Test**: Após aplicação em wfdb01, executar
`SELECT count(*) FROM execution_entity` retorna valor < baseline registrado,
e `SELECT * FROM pg_extension WHERE extname = 'pg_stat_statements'` retorna
resultado. O story é completo quando políticas de retenção estão ativas.

**Acceptance Scenarios**:

1. **Given** `execution_entity` com 429K+ linhas e sem purgação, **When** o
   playbook F17 configura `EXECUTIONS_DATA_PRUNE=true` com retenção 30 dias,
   **Then** novas execuções expiradas são purgadas automaticamente (sinalizado
   por redução mensurada em 24h).
2. **Given** PostgreSQL 16 sem `pg_stat_statements`, **When** o playbook
   ativa `shared_preload_libraries = 'pg_stat_statements'` e reinicia o serviço
   com manutenção agendada, **Then** `pg_stat_statements` retorna queries
   monitoradas com `total_exec_time`, `calls` e `mean_exec_time`.
3. **Given** backup `pg_dump` validado em wfdb02 antes da purgação, **When** a
   operação de purga é executada, **Then** o restore-test em wfdb01 replica os
   dados sem inconsistências.

---

### User Story 3 — F18: Documentação de Dupla Coleta e Change Request (Priority: P1)

Como engenheiro de observabilidade, quero documentar o estado de dupla coleta
confirmado pelo ANA-001, descobrir a configuração exata do `prod-collector-api`
responsável pelo envio ao Pushgateway, e emitir um change request formal para
o projeto responsável, de forma que a correção seja rastreável e auditável.

**Why this priority**: `prod-collector-api` não faz parte do escopo de tunning
deste projeto. A responsabilidade pela correção pertence ao projeto que mantém
o serviço. O artefato de F18 é o change request documentado — não o playbook
de modificação.

**Independent Test**: F18 é completo quando: (a) inspeção remota do
`prod-collector-api` está documentada com o nome exato da variável de controle,
(b) relatório de estado de dupla coleta gerado com PromQL evidence, e (c)
issue formal emitido para o projeto responsável com todos os dados necessários
para a correção.

**Acceptance Scenarios**:

1. **Given** dupla coleta ativa confirmada pelo ANA-001, **When** o script de
   diagnóstico de F18 é executado contra wfdb01, **Then** um relatório JSON
   documenta: séries duplicadas identificadas, labels de origem, magnitude da
   dupla contagem (%) e nome exato da variável de controle no prod-collector-api.
2. **Given** relatório de diagnóstico completo, **When** o artefato de change
   request é gerado, **Then** o issue contém: nome da variável confirmado,
   query PromQL de validação, critérios de aceite pós-correção (SC-006/SC-007),
   e referência à regra de promoção em bloco P1.
3. **Given** projeto responsável implementou a correção (fora deste projeto),
   **When** o ProvenanceGate script é executado após a mudança, **Then**
   `{instance=~".*0\.0\.0\.0.*", job="pushgateway"}` retorna ausente por ≥ 1h
   e contagens coerentes (tolerância ±1%) são confirmadas antes da promoção
   em bloco P1 para wf001.

---

### Edge Cases

- F17: O que acontece se o PostgreSQL em wfdb02 não puder ser reiniciado na janela
  de manutenção? → Rollback: remover `pg_stat_statements` do `shared_preload_libraries`
  e reagendar. `EXECUTIONS_DATA_PRUNE` não requer reinício.
- F16: O que acontece se `n8n_queue_*` não aparecer após habilitar as variáveis?
  → Verificar versão do N8N (≥ 0.130 necessária); validar geração de carga
  durante a verificação.
- F18: O que acontece se a inspeção do `prod-collector-api` revelar um
  mecanismo de controle diferente da variável esperada? → O change request
  para o projeto responsável deve documentar o mecanismo identificado e
  solicitar a desabilitação pelo método correto. F18 não inclui modificação
  direta do `prod-collector-api`.
- Todos: O que fazer se o playbook falhar no meio da execução? → Playbooks
  são idempotentes — reexecutar é seguro. Estado pre-playbook documentado no
  SESSION_REPORT.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O playbook MUST ativar `N8N_METRICS_INCLUDE_QUEUE_METRICS=true` e
  `QUEUE_HEALTH_CHECK_ACTIVE=true` via `docker-compose.override.yml` no ambiente
  wfdb01 sem downtime prolongado (< 2 minutos de reinício do container N8N).
- **FR-002**: O playbook MUST validar que as métricas `n8n_queue_*` aparecem no
  endpoint `/metrics` do container N8N após aplicação (F16).
- **FR-003**: O playbook MUST criar alert rule Prometheus para
  `n8n_queue_depth > threshold` configurável por variável (F16).
- **FR-004**: O playbook MUST configurar `EXECUTIONS_DATA_PRUNE=true` com
  `EXECUTIONS_DATA_PRUNE_MAX_AGE=720` (30 dias em horas) no container N8N (F17).
- **FR-005**: O playbook MUST ativar `pg_stat_statements` no PostgreSQL 16 de
  wfdb02 com janela de manutenção documentada (F17).
- **FR-006**: O playbook MUST executar `pg_dump` completo em wfdb02 antes de
  qualquer alteração destrutiva no PostgreSQL (F17).
- **FR-007**: F18 MUST executar diagnóstico remoto do `prod-collector-api`
  (inspeção de variáveis de ambiente sem modificação), documentar o nome exato
  da variável de controle do Pushgateway, e gerar um change request formal
  (issue) para o projeto responsável pelo serviço. O `prod-collector-api`
  NÃO DEVE ser modificado diretamente por este projeto (F18).
- **FR-008**: Todos os playbooks MUST ser idempotentes — re-execução não causa
  mudanças inesperadas (Princípio V).
- **FR-009**: A automação MUST coletar métricas before/after do VictoriaMetrics
  e armazená-las em `docs/SESSIONS/YYYY-MM-DD/SESSION_REPORT_*.md`.
- **FR-010**: O wfdb01 gate MUST ser aprovado para **todas as três features
  (F16, F17 e F18) em conjunto** antes de qualquer promoção para wf001. A
  promoção é em **bloco** — nenhuma feature pode ser promovida individualmente
  para wf001. Critérios: smoke tests HTTP 200 em `/healthz`, `/metrics`,
  `/api/v1/workflows` + ≥ 1 ciclo de pico (13:00–22:00 UTC) + evidências
  before/after para F16, F17 e F18 validadas pelo test_engineer.
- **FR-011**: F18 MUST executar validação ProvenanceGate após o projeto
  responsável aplicar a mudança no `prod-collector-api`: confirmar via PromQL
  que todas as séries de métricas N8N possuem proveniência única (scrape direto
  apenas) e que `{instance=~".*0\.0\.0\.0.*", job="pushgateway"}` está
  ausente por ≥ 1 hora antes de incluir F18 no gate de promoção em bloco.
- **FR-012**: O playbook de F17 (Vetor B — pg_stat_statements) DEVE coletar
  a configuração existente do PostgreSQL de wfdb02 (parâmetros, extensões,
  banco `n8n_db`) e provisionar um ambiente equivalente em
  `home011.localdomain` (192.168.15.198:6432), respeitando os limites de
  hardware do notebook. A validação de pg_stat_statements DEVE ser concluída
  com sucesso em home011 antes de qualquer operação Vetor B em wfdb02.

### Key Entities

- **NativeEnvConfig**: Variáveis de ambiente N8N para métricas de fila e
  purgação — gerenciadas via `docker-compose.override.yml`.
- **PostgresConfig**: Configurações de tunning do PostgreSQL 16 em wfdb02 —
  `pg_stat_statements`, `EXECUTIONS_DATA_PRUNE`, política de retenção.
- **PrometheusCollectionConfig**: Configuração de scrape e estado do Pushgateway
  no prod-collector-api — de dupla coleta para scrape único.
- **WfdbGateEvidence**: Registro de evidências do gate wfdb01 → wf001 — métricas
  antes/depois, smoke tests, sign-off do test_engineer.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001 (F16)**: `n8n_queue_depth` e ≥ 2 outras séries `n8n_queue_*` visíveis
  no VictoriaMetrics para `instance=wf001` dentro de 2 ciclos de scrape após
  aplicação.
- **SC-002 (F16)**: Hipótese de fila saturada confirmada ou descartada com dados
  reais (≥ 24h de histórico de `n8n_queue_depth` coletado).
- **SC-003 (F17)**: `execution_entity` apresenta crescimento ≤ baseline diário
  em 48h após ativação da purgação.
- **SC-004 (F17)**: ≥ 10 queries mais lentas do N8N identificadas e documentadas
  via `pg_stat_statements` no SESSION_REPORT.
- **SC-005 (F17)**: Backup `pg_dump` de wfdb02 concluído, tamanho > 0 e
  restore-test bem-sucedido em wfdb01.
- **SC-006 (F18)**: Série `{instance=~".*0.0.0.0.*", job="pushgateway"}` não
  registra novos pontos por ≥ 1 hora após aplicação.
- **SC-007 (F18)**: Contagens de `n8n_workflow_executions_total` coerentes com
  registros do banco (tolerância ±1%) após remoção da dupla coleta.
- **SC-008 (Todos)**: Rollback de qualquer feature possível em < 5 minutos
  revertendo o `docker-compose.override.yml` e recriando os containers.

## Assumptions

- N8N versão 2.6.4 (confirmada em wf001 pelo ANA-001) suporta todas as
  variáveis de F16 (requer ≥ 0.130 para métricas de fila).
- Acesso SSH via SPA (fwknop) disponível conforme `.secrets/ssh.json` para
  wfdb01, wf001 e wfdb02.
- O banco de dados N8N reside exclusivamente em wfdb02 (82.197.64.145:6432) —
  wf001 é apenas o servidor de aplicação. **Nome do banco confirmado: `n8n_db`.**
- PostgreSQL de desenvolvimento para validação de Vetor B (pg_stat_statements)
  de F17: `home011.localdomain` (192.168.15.198:6432). Toda validação de Vetor B
  DEVE ser aprovada em home011 antes de operações em wfdb02. O playbook coleta
  a configuração de wfdb02 e recria a estrutura em home011 respeitando os
  limites de hardware.
- `docker-compose.override.yml` não existe nos servidores alvo (será criado
  pelo playbook); se existir, será preservado e complementado.
- Janela de manutenção para reinício do PostgreSQL em wfdb02 (pg_stat_statements)
  será aprovada pelo `project-manager` antes da execução em produção.
- `prod-collector-api` não é modificado por este projeto. F18 gera change
  request para o projeto responsável. O nome da variável de controle do
  Pushgateway será descoberto por inspeção remota e incluído no change request.

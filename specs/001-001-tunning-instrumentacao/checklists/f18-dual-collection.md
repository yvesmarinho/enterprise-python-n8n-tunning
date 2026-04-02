# Requirements Quality Checklist: F18 — Correção de Dupla Coleta Prometheus

**Purpose**: Validar completude, clareza, consistência e cobertura dos requisitos
de F18 antes da geração de tasks.md (author self-review)
**Created**: 2026-04-02
**Feature**: [spec.md](../spec.md) — User Story 3 | [plan.md](../plan.md)

> ⚠️ **REGRA DE OURO — DEV-BEFORE-PROD**
> F18 altera a configuração de **prod-collector-api**, que está presente tanto
> em wfdb01 (ambiente de monitoramento) quanto em wf001 (ambiente de produção).
>
> A sequência obrigatória é:
> 1. **Inspecionar** o `prod-collector-api` em wfdb01 para confirmar o nome
>    exato da variável de controle do Pushgateway.
> 2. **Aplicar** a desabilitação em wfdb01 e **aguardar ≥ 1 hora** sem novos
>    dados de pushgateway.
> 3. **Validar** a coerência de contagens no VictoriaMetrics em wfdb01.
> 4. **Aguardar** aprovação do gate (ciclo de pico 121Labs coberto).
> 5. **Somente então** aplicar em wf001.
>
> Aplicar em wf001 antes de validar completamente em wfdb01 é **proibido**.
> Esta sequência deve estar documentada em cada requisito e task gerada.

---

## Requisito de Dev-Before-Prod Gate (Verificar Primeiro)

- [ ] CHK066 — O requisito FR-010 (gate wfdb01) aplica-se explicitamente a F18?
  O spec define que a ausência de dados de pushgateway por ≥ 1h em wfdb01
  É uma condição necessária e suficiente do gate, ou há outras condições
  (coerência de contagens, smoke tests) também obrigatórias? [Completeness,
  Spec §FR-010 vs §SC-006]

- [ ] CHK067 — O requisito especifica a janela de observação mínima em wfdb01
  antes da promoção para wf001? SC-006 diz "≥ 1 hora sem novos pontos"  —
  mas está claro que esse critério deve ser atingido **em wfdb01** (não
  apenas em qualquer ambiente)? [Clarity, Spec §SC-006]

- [ ] CHK068 — Existe um requisito de inspeção prévia do `prod-collector-api`
  em **wfdb01** (ou equivalente) para confirmar o nome exato da variável
  de controle antes de qualquer modificação? Pesquisa mencionada na research.md
  (R-004) mas não está em nenhum FR. [Completeness, Gap — research.md §R-004]

- [ ] CHK069 — O risco de que outros serviços em wf001 (além do prod-collector-api)
  também enviam métricas para o Pushgateway está documentado como um check
  obrigatório pré-execução em F18? Desabilitar o Pushgateway sem este check
  pode quebrar outros fluxos de monitoramento. [Infrastructure Safety, Gap]

---

## Completude dos Requisitos

- [ ] CHK070 — O path exato do compose file do `prod-collector-api` nos
  servidores está documentado como um requisito confirmado ou apenas como
  assumption? (research.md R-004 diz "diretório provável — a confirmar")
  [Completeness, Ambiguity — research.md §R-004]

- [ ] CHK071 — O requisito define qual query PromQL exata será usada para
  validar a ausência de dupla coleta? SC-006 usa
  `{instance=~".*0.0.0.0.*", job="pushgateway"}` — esta query está documentada
  em FR-007 ou apenas em SC-006? [Completeness, Gap — Spec §FR-007]

- [ ] CHK072 — A "tolerância de ±1%" em SC-007 para comparação de contagens
  com o banco N8N está documentada como requisito (FR) ou apenas como critério
  de aceite (SC)? Há um método de medição especificado (query SQL + PromQL)?
  [Completeness, Gap — Spec §SC-007]

- [ ] CHK073 — O conceito de "ProvenanceGate" mencionado em `objetivo.yaml`
  F18 escopo está documentado nos requisitos do spec? O que é o ProvenanceGate
  exatamente? Como é implementado e validado? [Completeness, Gap —
  objetivo.yaml §F18 escopo vs Spec §Requirements]

- [ ] CHK074 — A coleta de evidências before/after para F18 (série pushgateway
  ativa antes, ausente depois) está especificada como FR? FR-009 é genérico —
  há um FR específico de F18 que define qual snapshot coletar antes de
  desabilitar o Pushgateway? [Completeness, Gap — Spec §FR-009]

- [ ] CHK075 — O rollback de F18 (re-habilitar o Pushgateway) está documentado
  como um requisito explícito, com o procedimento descrito? Apenas mencionar
  o princípio de rollback não é suficiente. [Completeness, Gap — Spec §SC-008]

---

## Clareza dos Requisitos

- [ ] CHK076 — FR-007 diz "valida ausência de novos dados no Pushgateway" —
  o método de validação especificado é PromQL (VictoriaMetrics), inspeção
  direta do Pushgateway via `/api/v1/metrics`, ou ambos? Sem especificação,
  cada implementador pode escolher um método diferente. [Clarity,
  Ambiguity — Spec §FR-007]

- [ ] CHK077 — "recria o container" mencionado no AS-F18-1 — é um `docker
  compose up -d --force-recreate` ou um `docker compose restart`? A
  diferença é relevante para preservar volumes e configurações. Este detalhe
  deve estar nos requisitos ou estar referenciado nos contracts.
  [Clarity, Ambiguity — Spec §US3 AS-1]

- [ ] CHK078 — "apenas o scrape direto permaneça ativo" em F18 escopo do
  objetivo.yaml — o job name e configuração do scrape direto estão
  documentados (job=n8n, instance=wf001, target=31.220.103.208:5001)?
  Esta informação está em contracts/ mas deveria ser referenciada no spec.
  [Clarity, Spec §US3]

- [ ] CHK079 — SC-007 compara `n8n_workflow_executions_total` com "registros
  do banco N8N" — qual tabela e query SQL específica no banco N8N corresponde
  a esta contagem? A comparação é possível sem esta definição. [Clarity,
  Ambiguity — Spec §SC-007]

---

## Consistência dos Requisitos

- [ ] CHK080 — AS-F18-2 usa a query
  `{job="pushgateway", instance=~".*n8n.*"}` no Independent Test de US3,
  mas SC-006 usa `{instance=~".*0.0.0.0.*", job="pushgateway"}`. As duas
  queries são equivalentes para validar ausência de dupla coleta?
  Há inconsistência de labels? [Consistency, Spec §US3 vs §SC-006]

- [ ] CHK081 — O objetivo.yaml F18 escopo diz "desabilitar
  PROMETHEUS_PUSHGATEWAY_ENABLED=true no prod-collector-api" enquanto
  research.md R-004 diz que o nome da variável "deve ser confirmado via
  inspeção remota". Um requisito não pode depender de uma variável
  não-confirmada — esta inconsistência bloqueia implementação segura?
  [Consistency, Inconsistency — objective.yaml §F18 vs research.md §R-004]

- [ ] CHK082 — AS-F18-3 descreve validação pós-promoção para wf001 como
  parte do User Story 3. Mas US3 é descrito como "Independent Test" que
  valida em wfdb01. O acceptance scenario inclui wf001 mas o Independent
  Test não. Há inconsistência de escopo? [Consistency, Spec §US3]

---

## Qualidade dos Critérios de Aceite

- [ ] CHK083 — SC-006 ("série não registra novos pontos por ≥ 1 hora") —
  como é medido o "registro de novos pontos"? O VictoriaMetrics não apaga
  pontos antigos — a query usaria `last_over_time()` com janela de 1h?
  A query exata deve estar documentada. [Acceptance Criteria,
  Ambiguity — Spec §SC-006]

- [ ] CHK084 — SC-007 (±1% tolerância) — como é calculada a tolerância
  quando há latência de scrape (30s de intervalo)? O N8N pode concluir
  execuções entre a query no banco e a query no VictoriaMetrics. A janela
  de tempo de comparação está especificada? [Acceptance Criteria,
  Ambiguity — Spec §SC-007]

- [ ] CHK085 — SC-008 para F18 (rollback em < 5 min) — reverter F18
  significa reclassificar o estado "DUAL_COLLECTION" como estável
  temporariamente. O rollback de F18 não conflita com F16/F17 que podem
  estar aplicados? A interação entre rollback de features P1 está
  documentada? [Acceptance Criteria, Gap — Spec §SC-008]

---

## Cobertura de Cenários

- [ ] CHK086 — Existe requisito para o cenário em que o `prod-collector-api`
  **não possui** a variável `PROMETHEUS_PUSHGATEWAY_ENABLED` (o serviço
  tem outra forma de controle)? O edge case já está no spec, mas há um
  requisito que define a ação obrigatória (falhar com mensagem clara,
  não prosseguir silenciosamente)? [Coverage, Edge Case — Spec §Edge Cases]

- [ ] CHK087 — O cenário em que o Pushgateway em wfdb01 recebe dados de
  outros serviços além do prod-collector-api está coberto? Verificar
  ausência de dados no Pushgateway pode ser incorreto se outros scrapers
  ainda enviarem dados. [Coverage, Edge Case — Gap]

- [ ] CHK088 — O cenário de estado intermediário — `prod-collector-api`
  desabilitado mas o container ainda em processo de restart — está coberto?
  Durante este intervalo, a série pode parecer ausente prematuramente.
  [Coverage, Exception Flow — Gap]

- [ ] CHK089 — O cenário de F18 aplicado em wf001 causando discrepância
  de dados históricos (série pushgateway parou abruptamente — pode gerar
  alertas falsos) está documentado como expected behavior temporário?
  [Coverage, Edge Case — Gap]

---

## Qualidade dos Requisitos de Segurança de Infraestrutura (Princípio III)

- [ ] CHK090 — Existe requisito para inventariar TODOS os serviços que
  enviam dados ao Pushgateway em wf001 (não apenas prod-collector-api)
  antes de desabilitar qualquer configuração? Sem este inventário, F18
  pode criar um ponto cego de monitoramento. [Infrastructure Safety, Gap]

- [ ] CHK091 — O requisito define que nenhuma label Traefik do
  `prod-collector-api` deve ser alterada durante a modificação das variáveis
  de ambiente? (Princípio III — Traefik labels imutáveis sem confirmação
  explícita) [Infrastructure Safety, Spec §plan.md Constitution Check §III]

- [ ] CHK092 — Existe um requisito de "snapshot de estado baseline" do
  Pushgateway (`/api/v1/metrics`) antes de F18 ser aplicado? Sem este
  snapshot, não há baseline para comparar o estado "após" em caso de
  investigação. [Infrastructure Safety, Gap]

---

## Qualidade dos Requisitos de Segurança de Credenciais (Princípio VII)

- [ ] CHK093 — O acesso SSH SPA (fwknop) para wf001 durante F18 está
  documentado como pré-requisito explícito? wf001 é o servidor de produção
  e requer knock antes de qualquer conexão SSH. [Credential Hygiene,
  Gap — Spec §Assumptions]

- [ ] CHK094 — A inspeção remota de variáveis do container (docker inspect)
  para confirmar o nome da variável do Pushgateway — o output deste comando
  pode expor outras variáveis de ambiente sensíveis (tokens, senhas)?
  Existe requisito para filtrar ou anonimizar o output antes de logar?
  [Credential Hygiene, Infrastructure Safety — Gap]

---

## Rastreabilidade

- [ ] CHK095 — FR-007 (único FR de F18) rastreia diretamente para
  `objetivo.yaml` F18 criterio_aceite? Os três critérios de aceite do
  objetivo.yaml F18 (série 0.0.0.0:5000 sem novos dados, contagens coerentes,
  ProvenanceGate) têm correspondência em FRs ou SCs do spec? [Traceability,
  Gap — Spec §FR-007 vs objetivo.yaml §F18]

- [ ] CHK096 — F18 tem apenas um FR explícito (FR-007) para uma feature que
  cobre desabilitação, validação, coleta de evidências, ProvenanceGate e
  promoção. Esta sub-especificação de FRs é um gap de completude?
  [Traceability, Completeness — Spec §Requirements]

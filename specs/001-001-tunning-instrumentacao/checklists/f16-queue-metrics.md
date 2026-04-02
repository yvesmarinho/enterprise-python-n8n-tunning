# Requirements Quality Checklist: F16 — Habilitação de Métricas de Fila N8N

**Purpose**: Validar completude, clareza, consistência e cobertura dos requisitos
de F16 antes da geração de tasks.md (author self-review)
**Created**: 2026-04-02
**Feature**: [spec.md](../spec.md) — User Story 1 | [plan.md](../plan.md)

> ⚠️ **REGRA DE OURO — DEV-BEFORE-PROD**
> **TODA** validação, teste e homologação de F16 DEVE ser realizada e aprovada
> em **wfdb01 (ambiente de desenvolvimento/teste)** antes de qualquer ação no
> ambiente de produção (wf001). A promoção para wf001 só pode ocorrer após o
> gate wfdb01 estar completamente aprovado — incluindo métricas, smoke tests e
> ciclo de pico. Esta regra é **inegociável** e deve estar explícita nos
> requisitos de cada artefato gerado.

---

## Requisito de Dev-Before-Prod Gate (Verificar Primeiro)

- [ ] CHK001 — É obrigatório, nos requisitos, que F16 seja integralmente aplicado,
  testado e aprovado em **wfdb01** antes de qualquer ação em wf001? A sequência
  wfdb01 → wf001 deve estar bloqueante (hard gate), não apenas recomendada.
  [Completeness, Gap — Spec §FR-010]

- [ ] CHK002 — O critério de aprovação do gate wfdb01 para F16 especificamente
  é completo? Deveria incluir: (a) métricas `n8n_queue_*` visíveis em
  VictoriaMetrics, (b) ≥ 24h de dados coletados, (c) smoke tests HTTP 200,
  (d) ciclo de pico 121Labs 13:00–22:00 UTC coberto, (e) sign-off do
  test_engineer. Todos esses sub-critérios estão documentados? [Completeness,
  Spec §FR-010]

- [ ] CHK003 — Existe algum requisito que defina o que acontece se o gate wfdb01
  for reprovado? A proibição de prosseguir para wf001 está explicitamente
  documentada como um requisito, não apenas como uma boa prática? [Clarity,
  Gap — Spec §FR-010]

- [ ] CHK004 — O requisito de promoção em bloco (F16 + F17 + F18 juntos para
  wf001 após todos passarem o gate wfdb01) está documentado? Ou cada feature
  pode ser promovida individualmente? [Completeness, Gap — objetivo.yaml
  execution_order P1 note]

---

## Completude dos Requisitos

- [ ] CHK005 — A lista completa de séries `n8n_queue_*` esperadas está
  documentada? SC-001 menciona `n8n_queue_depth` + "≥ 2 outros", mas não
  nomeia as demais séries. São elas `n8n_queue_waiting`, `n8n_queue_active`,
  `n8n_queue_completed`, `n8n_queue_failed`? [Completeness, Spec §SC-001]

- [ ] CHK006 — O requisito mínimo de versão do N8N para suporte a métricas de
  fila (≥ 0.130) está documentado como FR explícito ou apenas como Assumption?
  Uma falha de versão deve bloquear a feature com mensagem clara? [Completeness,
  Spec §Assumptions]

- [ ] CHK007 — Há requisito para o valor padrão (default) do threshold do alerta
  `n8n_queue_depth`? FR-003 diz "configurável por variável" mas não define o
  valor default recomendado pelo ANA-001. [Completeness, Gap — Spec §FR-003]

- [ ] CHK008 — O requisito de coleta de evidências before/after está especificado
  **como parte de F16**, incluindo quais séries PromQL coletar antes da aplicação
  em wfdb01 e após a validação em wf001? [Completeness, Spec §FR-009]

- [ ] CHK009 — Existe requisito que defina o conteúdo mínimo obrigatório do
  `docker-compose.override.yml` gerado pelo playbook? (quais variáveis, em
  qual serviço, qual indentação/formato) [Completeness, Gap — Spec §FR-001]

- [ ] CHK010 — A definição de "downtime prolongado" (< 2 minutos em FR-001)
  inclui uma strategy de validação de disponibilidade pré e pós-restart do
  container N8N? Por exemplo, health-check antes do restart e confirmação de
  ready state após? [Completeness, Gap — Spec §FR-001]

---

## Clareza dos Requisitos

- [ ] CHK011 — "≤ 2 ciclos de scrape (< 60s)" no AS-F16-2 assume um intervalo
  de scrape de 30s. Este intervalo está documentado como assumption ou
  requisito? Caso o scrape interval seja diferente em wfdb01 vs wf001, o
  critério de tempo muda? [Clarity, Spec §US1 AS-2]

- [ ] CHK012 — FR-003 diz alerta para `n8n_queue_depth > threshold` — o nome
  exato da variável Ansible que controla o threshold está especificado? Sem
  isso, cada implementador pode nomear diferente. [Clarity, Gap — Spec §FR-003]

- [ ] CHK013 — "validação aprovada em wfdb01" no AS-F16-3 — o que exatamente
  constitui "aprovação"? Quem tem autoridade para aprovar (test_engineer,
  project_manager)? O requisito deveria especificar o ator. [Clarity,
  Ambiguity — Spec §US1 AS-3]

- [ ] CHK014 — SC-001 usa `instance=wf001` como label esperado, mas a validação
  em wfdb01 usaria `instance=wfdb01`. O requisito está claro sobre qual label
  validar em cada ambiente? [Clarity, Spec §SC-001]

- [ ] CHK015 — O termo "expõe séries `n8n_queue_*` com valores numéricos" no
  AS-F16-1 está suficientemente preciso? "Valores numéricos" inclui `0.0`
  (fila vazia)? Qual é o critério para "série ativa"? [Clarity,
  Spec §US1 AS-1]

---

## Consistência dos Requisitos

- [ ] CHK016 — FR-002 diz "validar que as métricas `n8n_queue_*` aparecem" e
  SC-001 diz "≥ 2 outras séries além de `n8n_queue_depth`" — os dois
  requisitos estão alinhados? FR-002 deveria referenciar o critério quantitativo
  de SC-001. [Consistency, Spec §FR-002 vs §SC-001]

- [ ] CHK017 — FR-001 descreve a aplicação em wfdb01 mas não menciona wf001.
  FR-010 define a promoção para wf001. Há consistência sobre qual FR governa
  cada ambiente, ou wf001 está sub-especificado? [Consistency,
  Spec §FR-001 vs §FR-010]

- [ ] CHK018 — O AS-F16-3 menciona promoção para wf001 como parte do US1, mas
  a regra de promoção em bloco (P1 = F16+F17+F18 juntos) do objetivo.yaml
  pode tornar este scenario inconsistente se aplicado apenas a F16.
  O requisito resolve esta tensão? [Consistency, Gap — Spec §US1 AS-3 vs
  objetivo.yaml P1 note]

---

## Qualidade dos Critérios de Aceite

- [ ] CHK019 — SC-001 é mensurável objetivamente ("≥ 2 séries visíveis em 2
  ciclos de scrape")? Qual é o método de medição especificado — PromQL manual,
  script automatizado, query VictoriaMetrics? [Acceptance Criteria,
  Spec §SC-001]

- [ ] CHK020 — SC-002 diz "≥ 24h de histórico de `n8n_queue_depth` coletado" —
  este critério está vinculado ao gate wfdb01 ou ao gate wf001? Se for ao gate
  wfdb01 (o que faz sentido), está explicitamente documentado que a promoção
  só ocorre após 24h de dados em wfdb01? [Acceptance Criteria, Gap — Spec §SC-002]

- [ ] CHK021 — O SC-008 (rollback em < 5 minutos) aplica-se a F16 especificamente?
  O procedimento de rollback do `docker-compose.override.yml` para F16 produz
  estado idêntico ao baseline, ou apenas remove as variáveis adicionadas?
  A distinção está documentada? [Acceptance Criteria, Spec §SC-008]

---

## Cobertura de Cenários

- [ ] CHK022 — Existe requisito para o cenário em que métricas de fila aparecem
  em wfdb01 mas **não** em wf001 após a promoção? (Diferença de configuração
  entre ambientes) [Coverage, Edge Case — Gap]

- [ ] CHK023 — Existe requisito para o cenário em que a fila `n8n_queue_depth`
  retorna sempre `0` porque não há carga no momento da validação? Como
  distinguir "métrica funcional com valor zero" de "métrica ausente"?
  [Coverage, Edge Case — Spec §Edge Cases]

- [ ] CHK024 — O fluxo de recuperação quando a validação pós-restart falha
  (container N8N não retorna healthy após adicionar as variáveis) está coberto
  nos requisitos? [Coverage, Exception Flow — Gap]

---

## Qualidade dos Requisitos de Segurança de Infraestrutura (Princípio III)

- [ ] CHK025 — Existe requisito para fazer backup do `docker-compose.yml`
  **antes** de criar o `docker-compose.override.yml`? O override pode
  interferir com labels Traefik existentes — há requisito de verificação de
  labels existentes antes de escrever o override? [Infrastructure Safety,
  Gap — Spec §Assumptions]

- [ ] CHK026 — O requisito de idempontência especifica que o playbook DEVE
  produzir diffs idênticos (nenhuma mudança) em segunda execução com os mesmo
  inputs? Este critério é verificável via `ansible-playbook --check`?
  [Infrastructure Safety, Spec §FR-008]

---

## Qualidade dos Requisitos de Segurança de Credenciais (Princípio VII)

- [ ] CHK027 — O acesso SSH SPA via fwknop para wfdb01 e wf001 está documentado
  como um **pré-requisito** explícito de F16 (não apenas assumption geral do
  projeto)? [Credential Hygiene, Gap — Spec §Assumptions]

- [ ] CHK028 — A especificação define que nenhuma credencial, token ou IP
  sensível deve aparecer no `docker-compose.override.yml` gerado? As variáveis
  de ambiente para F16 são todas não-sensíveis (booleanos públicos), mas
  o requisito deve confirmar isso explicitamente. [Credential Hygiene,
  Gap — Spec §FR-001]

---

## Rastreabilidade

- [ ] CHK029 — Cada FR de F16 (FR-001, FR-002, FR-003) rastreia para um
  critério de aceite (SC-001, SC-002) e para uma entrada em `objetivo.yaml`
  (F16 escopo/criterio_aceite)? A cadeia objetivo.yaml → spec → plan →
  tasks está completa? [Traceability, Spec §Requirements]

- [ ] CHK030 — O requisito FR-010 (gate wfdb01) está vinculado explicitamente a
  F16 no spec.md? Ou é apenas um requisito geral que pode ser esquecido
  durante a implementação de F16 especificamente? [Traceability,
  Spec §FR-010]

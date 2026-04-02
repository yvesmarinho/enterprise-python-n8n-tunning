# Requirements Quality Checklist: F17 — Purgação e Tunning PostgreSQL N8N

**Purpose**: Validar completude, clareza, consistência e cobertura dos requisitos
de F17 antes da geração de tasks.md (author self-review)
**Created**: 2026-04-02
**Feature**: [spec.md](../spec.md) — User Story 2 | [plan.md](../plan.md)

> ⚠️ **REGRA DE OURO — DEV-BEFORE-PROD**
> F17 possui dois vetores de risco distintos com ambientes diferentes:
>
> **Vetor A — Variáveis de ambiente N8N (EXECUTIONS_DATA_PRUNE)**:
> Aplicar e validar em **wfdb01 (N8N de teste)** → somente após aprovação do
> gate, aplicar em **wf001 (N8N de produção)**.
>
> **Vetor B — PostgreSQL pg_stat_statements (wfdb02)**:
> wfdb02 é um servidor de banco de dados de **produção compartilhado**. Toda
> validação deve ser feita primeiramente em **home011 ou wfdb01 local PostgreSQL**
> (desenvolvimento) e com janela de manutenção aprovada. A promoção direta para
> wfdb02 sem validação em dev é **proibida**.
>
> **Esta distinção de ambientes deve estar nitidamente documentada em cada
> requisito, playbook e task gerada.**

---

## Requisito de Dev-Before-Prod Gate (Verificar Primeiro)

- [ ] CHK031 — O spec distingue claramente os dois vetores de F17 quanto à
  sequência de ambientes? Vetor A (N8N env vars): wfdb01 → wf001. Vetor B
  (PostgreSQL pg_stat_statements): dev local (home011 / wfdb01 PostgreSQL)
  → wfdb02 com janela de manutenção? [Completeness, Gap — Spec §US2]

- [ ] CHK032 — Existe um ambiente de desenvolvimento PostgreSQL explicitamente
  definido para validação de `pg_stat_statements` antes de aplicar em wfdb02
  (produção)? O `home011.localdomain` (PostgreSQL 16, 192.168.15.198:6432) é
  o candidato natural — está documentado como ambiente de validação? [Gap,
  Infrastructure Safety]

- [ ] CHK033 — O gate de aprovação de F17 em wfdb01 (para o Vetor A) está
  separado da janela de manutenção de wfdb02 (Vetor B)? Os dois gates têm
  critérios e responsáveis distintos documentados? [Completeness, Gap —
  Spec §FR-005, §FR-010]

- [ ] CHK034 — Existe requisito explícito que a purgação em N8N de produção
  (wf001) só pode ser ativada **após** backup validado de wfdb02 E após gate
  wfdb01 aprovado? A dependência entre backup e purgação está documentada
  como constraint de sequência, não apenas como boa prática? [Completeness,
  Infrastructure Safety — Spec §FR-006]

- [ ] CHK035 — O pg_stat_statements (Vetor B) pode ser desbloqueado e aplicado
  em wfdb02 **independentemente** da promoção do Vetor A para wf001, ou os
  dois devem ser coordenados? Este relacionamento está documentado? [Completeness,
  Gap — Spec §US2]

---

## Completude dos Requisitos

- [ ] CHK036 — O nome do banco de dados N8N em wfdb02 está documentado como
  requisito confirmado, não apenas como "a confirmar"? Antes de gerar tasks.md,
  este valor deve ser resolvido. [Completeness, Ambiguity — Spec §Assumptions]

- [ ] CHK037 — Há requisito que especifique se o pg_dump usa a porta direta do
  PostgreSQL (6432) ou o Pgbouncer (5432)? pg_dump NÃO deve usar Pgbouncer
  (transaction pooling pode causar inconsistências) — esta distinção está
  documentada? [Completeness, Infrastructure Safety — Gap]

- [ ] CHK038 — O requisito de backup (FR-006) especifica: path de destino,
  nome do arquivo (com timestamp), formato (plain SQL vs custom vs gzip),
  e critério de validação de integridade (tamanho > 0 AND SHA-256 registrado)?
  [Completeness, Spec §FR-006]

- [ ] CHK039 — O restore-test mencionado em SC-005 está documentado como FR
  explícito? Apenas estar em SC-005 não é suficiente — deveria haver FR
  que obrigue o restore a ser executado e validado em wfdb01 antes de
  prosseguir. [Completeness, Gap — Spec §SC-005]

- [ ] CHK040 — Há requisito para `EXECUTIONS_DATA_PRUNE_TIMEOUT` (3600000ms)?
  O data-model.md inclui esta variável mas ela não aparece em FR-004.
  [Completeness, Gap — Spec §FR-004 vs data-model.md]

- [ ] CHK041 — Os parâmetros adicionais do `pg_stat_statements`
  (`pg_stat_statements.track = 'all'` e `pg_stat_statements.max = 10000`)
  estão documentados como requisitos, ou apenas no data-model? Sem FRs
  explícitos, podem ser ignorados na implementação. [Completeness, Gap —
  Spec §FR-005 vs data-model.md]

- [ ] CHK042 — Existe requisito para documentar as queries lentas identificadas
  pelo `pg_stat_statements` em um artefato específico (qual SESSION_REPORT?
  tabela no plan? documento separado?) dentro de um prazo definido?
  [Completeness, Spec §SC-004]

- [ ] CHK043 — O período de monitoramento pós-ativação da purgação para validar
  SC-003 (48h) está documentado como required observation window antes de
  considerar F17 concluído em wfdb01? [Completeness, Gap — Spec §SC-003]

---

## Clareza dos Requisitos

- [ ] CHK044 — FR-005 menciona "janela de manutenção documentada" — onde deve
  ser documentada (SESSION_REPORT, email, ticket)? Quem aprova? Quanto tempo
  de antecedência? Qual a duração esperada do restart do PostgreSQL?
  [Clarity, Ambiguity — Spec §FR-005]

- [ ] CHK045 — FR-006 diz "qualquer alteração destrutiva no PostgreSQL" — está
  definida a lista exata do que conta como "destrutiva"? É:
  (a) apenas operações DDL? (b) qualquer ALTER? (c) apenas operações em
  `execution_entity`? (d) inclusive ativação de `pg_stat_statements`?
  [Clarity, Ambiguity — Spec §FR-006]

- [ ] CHK046 — SC-003 diz "crescimento ≤ baseline diário em 48h" — como é
  definido/medido o "baseline diário" de crescimento? Existe um snapshot
  antes da ativação que serve de referência? Onde é registrado?
  [Clarity, Ambiguity — Spec §SC-003]

- [ ] CHK047 — SC-004 diz "≥ 10 queries mais lentas" — "lentas" tem um
  threshold mínimo (ex: > 1s de mean_exec_time)? Ou são simplesmente as
  top-10 por tempo total, independente da duração? [Clarity,
  Ambiguity — Spec §SC-004]

- [ ] CHK048 — O requisito de purgação define o comportamento esperado para
  execuções "running" ou "waiting" que são mais antigas que 30 dias?
  `EXECUTIONS_DATA_PRUNE` purga apenas execuções finalizadas ou também
  pendentes? [Clarity, Gap — Spec §FR-004]

---

## Consistência dos Requisitos

- [ ] CHK049 — FR-004 e FR-005 mencionam ambos o container N8N e o PostgreSQL
  respectivamente, mas FR-004 não especifica que o N8N deve ser reiniciado
  para que `EXECUTIONS_DATA_PRUNE` entre em vigor. A sequência está
  consistente com FR-001 (F16) que especifica o restart? [Consistency,
  Gap — Spec §FR-004]

- [ ] CHK050 — A Assumption "banco de dados N8N reside exclusivamente em wfdb02"
  é consistente com o edge case que menciona restore-test em wfdb01?
  Se wfdb01 não tem uma replica do banco, o restore-test usaria um banco
  distinto. Esta distinção está documentada? [Consistency,
  Spec §Assumptions vs §US2 AS-3]

- [ ] CHK051 — SC-005 exige "backup tamanho > 0 e restore-test bem-sucedido
  em wfdb01" — mas wfdb01 não hospeda o PostgreSQL de aplicação. O restore-test
  em wfdb01 implica subir um PostgreSQL temporário ou usar o PostgreSQL
  existente do stack de monitoramento? Esta ambiguidade deve ser resolvida.
  [Consistency, Ambiguity — Spec §SC-005]

---

## Qualidade dos Critérios de Aceite

- [ ] CHK052 — SC-003 ("crescimento ≤ baseline diário em 48h") é verificável
  de forma objetiva e automatizada? Existe uma query SQL ou script específico
  documentado para esta verificação? [Acceptance Criteria, Spec §SC-003]

- [ ] CHK053 — SC-004 ("≥ 10 queries documentadas") tem um formato de
  documentação obrigatório? (ex: tabela com query_id, mean_exec_time,
  calls, total_exec_time) Sem formato definido, o critério não é objetivamente
  verificável. [Acceptance Criteria, Gap — Spec §SC-004]

- [ ] CHK054 — SC-008 (rollback em < 5 min) para F17 está completamente
  especificado? O rollback do Vetor A (remover env var, restart N8N) é
  diferente do rollback do Vetor B (reverter shared_preload_libraries,
  restart PostgreSQL). Ambos são descritos? [Acceptance Criteria,
  Gap — Spec §SC-008]

---

## Cobertura de Cenários

- [ ] CHK055 — Existe requisito para o cenário em que `execution_entity`
  cresce mais rápido que a purgação consegue manter? (Taxa de inserção > taxa
  de purga) Há um threshold de alerta para este cenário? [Coverage, Edge Case —
  Spec §Edge Cases]

- [ ] CHK056 — O cenário de falha parcial de F17 está coberto: e se o Vetor A
  (purgação N8N) funcionar mas o Vetor B (pg_stat_statements) falhar? Os
  dois vetores podem ficar em estados independentes? [Coverage,
  Exception Flow — Gap]

- [ ] CHK057 — Existe requisito para o cenário em que o pg_dump é bem-sucedido
  mas o restore-test falha? Qual é a ação obrigatória? (Não prosseguir com
  nenhuma operação destrutiva — está documentado?) [Coverage,
  Exception Flow — Gap]

- [ ] CHK058 — O comportamento do N8N durante a purga inicial (purge run on
  existing 429K rows — pode demorar?) está documentado como expectativa
  de comportamento observado? [Coverage, Edge Case — Gap]

---

## Qualidade dos Requisitos de Segurança de Infraestrutura (Princípio III)

- [ ] CHK059 — O requisito de backup (FR-006) especifica qual porta usar para
  `pg_dump`: 6432 (PostgreSQL direto) e **não** 5432 (Pgbouncer)? Esta
  distinção crítica (pg_dump não funciona corretamente via Pgbouncer em
  transaction pool mode) deve estar em FR, não apenas na constituição.
  [Infrastructure Safety, Gap — Spec §FR-006]

- [ ] CHK060 — O requisito define um prazo máximo de retenção para os arquivos
  de backup gerados? (ex: manter por 30 dias) Backups não gerenciados podem
  encher disco. [Infrastructure Safety, Gap — Spec §FR-006]

- [ ] CHK061 — Há requisito que proíba aplicar qualquer operação do Vetor B
  (pg_stat_statements) diretamente em wfdb02 sem evidência documentada de
  que o procedimento foi testado em ambiente de desenvolvimento (home011)?
  [Infrastructure Safety, Dev-Before-Prod — Gap]

---

## Qualidade dos Requisitos de Segurança de Credenciais (Princípio VII)

- [ ] CHK062 — Os requisitos especificam que a senha do PostgreSQL para pg_dump
  deve ser fornecida via Ansible Vault ou variável de ambiente, e **nunca**
  como argumento de linha de comando (visível em `ps aux`)? [Credential Hygiene,
  Gap — Spec §Assumptions]

- [ ] CHK063 — F17 usa `psycopg2` para conexões Python — o requisito especifica
  que a connection string NÃO deve aparecer em logs, outputs JSON ou artefatos
  de sessão? [Credential Hygiene, Gap — contracts/python-script-cli.md]

---

## Rastreabilidade

- [ ] CHK064 — FR-004 (purgação N8N), FR-005 (pg_stat_statements), FR-006
  (backup) rastreiam para `objetivo.yaml` F17 `criterio_aceite` de forma
  direta e completa? Todo critério de aceite do objetivo.yaml tem um FR
  correspondente no spec? [Traceability, Spec §Requirements]

- [ ] CHK065 — Os dois vetores de F17 têm IDs ou labels distintos para
  rastreabilidade individual em tasks.md? (ex: F17-A e F17-B ou tags separadas)
  Sem isso, tasks podem ser geradas sem clareza de qual vetor pertencem.
  [Traceability, Gap — Spec §US2]

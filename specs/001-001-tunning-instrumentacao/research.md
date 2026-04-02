# Research: P1 Tunning e Instrumentação N8N (F16 + F17 + F18)

**Feature**: `001-001-tunning-instrumentacao` | **Date**: 2026-04-02
**Status**: Complete — todas as incógnitas resolvidas

---

## R-001: Injeção de Variáveis de Ambiente no Container N8N

**Contexto**: F16 e F17 requerem adicionar variáveis de ambiente ao container
N8N em wfdb01 e wf001 sem downtime prolongado.

**Decision**: Usar `docker-compose.override.yml` no diretório
`/opt/docker_user/n8n/` para adicionar variáveis sem modificar o `docker-compose.yml`
base. O `docker compose up -d n8n` recria apenas o serviço N8N com as novas vars.

**Rationale**:
- Docker Compose override é idempotente — re-executar com o mesmo conteúdo não
  causa mudanças no segundo run.
- Não modifica o arquivo base (`docker-compose.yml`), preservando configurações
  originais e facilitando rollback (`rm docker-compose.override.yml` + `up -d`).
- Downtime estimado: < 2 minutos (restart do container N8N).

**Alternatives considered**:
- Editar `docker-compose.yml` diretamente → rejeitado: não idempotente via
  Ansible `lineinfile` em YAML estruturado; perda de rastreabilidade.
- Variáveis via `env_file` separado → possível mas adiciona complexidade de
  gestão de múltiplos arquivos; override é mais idiomático para patches incrementais.

---

## R-002: Endpoint de Métricas do N8N — Configuração de Scrape

**Contexto**: F16 e F18 requerem entender a cadeia exata de coleta de métricas
no prod-collector-api de wf001.

**Decision**: O endpoint de métricas do N8N é exposto via `prod-collector-api`
na porta **5001** de wf001 (31.220.103.208:5001). O scrape direto usa
`job=n8n, instance=wf001`. A coleta via Pushgateway usa
`job=pushgateway, instance=0.0.0.0:5000` — esta segunda rota deve ser removida
em F18.

**Rationale**:
- ANA-001 confirma explicitamente: `targets: [31.220.103.208:5001]` com
  `relabeling instance=wf001` é o scrape correto.
- A série `0.0.0.0:5000` identificada no ANA-001 é o vetor de dupla coleta a
  eliminar.

**Alternatives considered**:
- Scrape direto na porta nativa do N8N (geralmente `:5678/metrics`) → não
  aplicável: o prod-collector-api existe como proxy de métricas com
  enriquecimento de labels.

---

## R-003: Ativação do pg_stat_statements no PostgreSQL 16 (wfdb02)

**Contexto**: F17 requer monitoramento de queries lentas do N8N via
`pg_stat_statements`.

**Decision**: `pg_stat_statements` requer entrada em `shared_preload_libraries`
no `postgresql.conf` de wfdb02 **e um restart do processo PostgreSQL**. O
procedimento é:
1. `ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';`
2. Restart controlado: `systemctl restart postgresql` (ou container recreate)
3. `CREATE EXTENSION IF NOT EXISTS pg_stat_statements;` na base do N8N

**Rationale**:
- `shared_preload_libraries` não é recarregável via `pg_reload_conf()` — restart
  é obrigatório. Isso requer janela de manutenção aprovada pelo `project-manager`.
- F17 pode ser dividido: primeiro ativar `EXECUTIONS_DATA_PRUNE` (sem restart,
  apenas env var), depois `pg_stat_statements` (com restart agendado). As duas
  partes são independentes.

**Alternatives considered**:
- `pg_stat_statements` via `LOAD` por sessão → não persiste entre conexões;
  inútil para análise contínua.
- `auto_explain` como alternativa → captura planos de execução mas não agrega
  por query; `pg_stat_statements` é mais adequado para identificar padrões.

---

## R-004: Desabilitação do Pushgateway no prod-collector-api

**Contexto**: F18 exige entender o mecanismo pelo qual o prod-collector-api
envia dados ao Pushgateway — mas `prod-collector-api` **não faz parte do escopo
de tunning deste projeto**. Qualquer alteração ao serviço deve ser feita pelo
projeto responsável, mediante change request formal.

**Decision**: O escopo de F18 neste projeto é:
1. **Diagnóstico (somente leitura)**: inspecionar o prod-collector-api via
   `docker inspect` para descobrir o nome exato da variável de controle do
   Pushgateway, sem nenhuma modificação.
2. **Relatório de dupla coleta**: documentar o estado atual via PromQL
   (`{instance=~".*0\.0\.0\.0.*"}`) e calcular a magnitude do impacto.
3. **Change request formal**: gerar o artefato de issue para o projeto
   responsável, contendo: variável de controle confirmada, query de validação,
   critérios de aceite (SC-006/SC-007) e ProvenanceGate post-check.

**Rationale**:
- `prod-collector-api` é um serviço de outro projeto. Modificá-lo diretamente
  viola o escopo de tunning e cria dependência não gerenciável.
- A abordagem de change request garante rastreabilidade e responsabilidade clara.
- O contrato de F18 é: **entregar evidência + issue** — não o playbook de correção.

**Alternatives considered**:
- Modificar diretamente via playbook → rejeitado: fora do escopo deste projeto;
  cria acoplamento entre projetos sem governo formal.
- Remover o serviço Pushgateway → afeta outros scrapers potenciais; too broad.

---

## R-005: Estrutura dos Compose Files nos Servidores

**Contexto**: Os playbooks precisam saber paths exatos e estrutura dos
docker-compose files em wfdb01 e wf001.

**Decision**:
- Path base: `/opt/docker_user/n8n/` em ambos (wfdb01 e wf001) — confirmado
  por `objetivo.yaml` (`path_n8n: /opt/docker_user/n8n`).
- O Ansible `pre_task` de cada playbook executará `stat` no compose file e
  fará `assert` antes de prosseguir.
- Cada playbook inclui um Play 1 de SPA knock via `fwknop` conforme padrão
  `.github/copilot-instructions.md`.

**Rationale**:
- Verificação com `stat` + `assert` garante que o playbook falha ruidosamente
  se o path não existir, em vez de criar estruturas erradas.
- Play 1 de SPA knock é obrigatório para todos os servidores VPS do projeto.

**Alternatives considered**:
- Hardcode de path sem verificação → rejeitado: não idempotente na ausência
  do diretório; falha silenciosa.

---

## R-006: Critérios de Métricas Before/After para Gates

**Contexto**: Princípio VI e critérios de aceite de todas as features requerem
coleta de métricas antes e após cada ação.

**Decision**: Usar o script `src/collect_gate_evidence.py` para consultar o
VictoriaMetrics de wfdb01 via PromQL e gerar um relatório JSON.
Métricas chave por feature:

| Feature | Métrica Before | Métrica After |
|---------|---------------|--------------|
| F16 | ausência de `n8n_queue_*` | presença + valores de `n8n_queue_depth` |
| F17 | `COUNT(*) FROM execution_entity` (baseline 429K+) | contagem 24h após purgação |
| F17 | ausência de `pg_stat_statements` | queries top-10 documentadas |
| F18 | série `{instance=~"0.0.0.0.*"}` ativa | série inexistente / zero pontos |

**Rationale**:
- Evidências quantitativas são exigidas pelo Princípio VI e pela regra P0 de
  `objetivo.yaml` (`wf001 → evidências métricas before/after`).
- Script Python reutilizável entre features P1, P2, P3.

---

## Constitution Check Pós-Research

Todos os 7 princípios permanecem ✅ após resolução de incógnitas:

- **I. SDD** ✅ — F16, F17, F18 rastreiam para objetivo.yaml
- **II. Scope** ✅ — Nenhuma incógnita sugere N8N version upgrade
- **III. Safety** ✅ — R-003 confirma janela de manutenção para wfdb02 restart;
  R-005 confirma assert pré-execução
- **IV. wfdb01 Gate** ✅ — R-006 define métricas de evidência para o gate;
  promoção em bloco (F16+F17+F18) obrigatória (FR-010)
- **V. Idempotent** ✅ — R-001 override pattern é idempotente por design
- **VI. Observability** ✅ — R-006 define coleta sistemática de before/after;
  R-007 define ProvenanceGate como validação pós-correção
- **VII. Credential Hygiene** ✅ — R-004 confirma diagnóstico de leitura;
  home011 é ambiente local sem exposição de credentials de produção

---

## R-007: ProvenanceGate — Definição e Implementação

**Contexto**: APós o projeto responsável aplicar a correção no prod-collector-api,
F18 precisa validar que as métricas N8N possuem proveniência única (scrape direto
apenas).

**Decision**: ProvenanceGate é uma validação PromQL executada pelo script
`src/validate_prometheus.py --mode provenance-gate` que confirma **dois critérios**:

1. **Ausência de Pushgateway**: a query `absent_over_time({instance=~".*0\.0\.0\.0.*",
   job="pushgateway"}[1h])` retorna resultado (confirma 1 hora sem novos pontos).
2. **Coerência de contagens**: a diferença entre `n8n_workflow_executions_total`
   (VictoriaMetrics) e `COUNT(*) FROM execution_entity` (banco `n8n_db`) é ≤ 1%.

O ProvenanceGate é **requisito de entrada** para que F18 seja incluído no
bloqueio de promoção P1 (FR-010+FR-011). Sem gate aprovado, F18 não entra
na promoção em bloco.

**Rationale**:
- Valida que não há regressão silenciosa: pushgateway reabilitado entre
  ambientes seria detectado pelo gate.
- PromQL + SQL cross-check garante consistência observabilidade-banco.

**Alternatives considered**:
- Apenas verificar ausência de séries Pushgateway (sem SQL cross-check) →
  rejeitado: não valida coerência de contagens, que é o objetivo central de F18.

---

## R-008: Ambiente home011 como DEV para Vetor B (pg_stat_statements)

**Contexto**: CHK031 identificou que não havia ambiente de desenvolvimento
justificado para validar pg_stat_statements antes de aplicar em wfdb02 (produção).

**Decision**: `home011.localdomain` (192.168.15.198:6432) é o PostgreSQL de
desenvolvimento para F17 Vetor B. O playbook (tag `f17-setup-dev`) DEVE:
1. Conectar em wfdb02 e capturar: `pg_settings` relevantes, extensões instaladas,
   configuração de `shared_preload_libraries`.
2. Aplicar uma configuração equivalente em home011 (PostgreSQL 16 local),
   respeitando os limites de hardware do notebook (RAM/CPU menores).
3. Executar `CREATE EXTENSION IF NOT EXISTS pg_stat_statements` no banco `n8n_db`
   de home011 e validar output de `pg_stat_statements.enabled`.

**Rationale**:
- Vetor B (pg_stat_statements) requer restart do PostgreSQL. Validar o processo
  completo em um ambiente equivalente reduz o risco de surpresas em produção.
- home011 já está listado na infraestrutura do projeto (constitution v2.2.0).
- Regra do projeto: todo teste/homologação DEVE ocorrer no ambiente de
  desenvolvimento antes de iniciar a atualização do ambiente de produção.

**Alternatives considered**:
- Testar diretamente em wfdb01 (N8N test server) → rejeitado: wfdb01 é o
  servidor de teste do N8N, não um ambiente PostgreSQL independente; usar
  home011 mantém o banco de test separado.

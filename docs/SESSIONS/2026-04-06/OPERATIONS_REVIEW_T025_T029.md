# ⚙️ Operations Review — T025 + T029

**Data**: 2026-04-06
**Sessão**: ANALYSIS
**Escopo**: preparar execução segura dos gates F17 (T025) e F18 (T029) em `wfdb01`

---

## 1. Objetivo

Transformar os bloqueios atuais de T025 e T029 em um plano de execução objetivo, com parâmetros já reconciliados com o estado real do repositório.

### Diretriz de escopo de banco (vigente)

- O PostgreSQL de `wfdb01` e exclusivo do stack Prometheus/observabilidade.
- Nao existem bases de dados de outras aplicacoes nesse PostgreSQL local de `wfdb01`.
- Toda analise de desempenho de banco relacionada ao N8N deve ocorrer em `wfdb02` (DEV: `n8n_dev_db`; PROD: `n8n_db`).

---

## 2. T025 — F17 Vetor A (`EXECUTIONS_DATA_PRUNE`)

### Estado atual

- O gate está pendente em `docs/TODO.md`
- O playbook já passou em dry-run, mas a retomada de N8N ficou bloqueada na validação pós-restart
- O script `src/purge_execution_entity.py` já foi corrigido para consultar o tamanho da tabela com placeholders compatíveis com psycopg2

### Bloqueio identificado

O task `ansible/roles/postgres_tuning/tasks/f17_prune.yml` reiniciava `docker compose up -d n8n`, mas `wfdb01` usa os serviços:
- `n8n_editor`
- `n8n_worker`
- `n8n_webhook`
- `n8n_mcp`

Além disso, o wait pós-restart usava `wait_for` em porta fixa, enquanto o gate F16 já validava corretamente via `https://testn8n.vya.digital/metrics`.

### Correção já aplicada

- O restart do F17 agora usa `n8n_services`
- O health check pós-restart agora usa `uri` no endpoint real de métricas

### Pré-requisitos operacionais

1. Credenciais PG disponíveis em `.secrets/n8n_db_wfdb02.json`
2. Acesso SPA para `wfdb01` e `wfdb02`
3. Ambiente com `PG_USER` e `PG_PASSWORD` exportados para o check-only

### Sequência recomendada

1. Dry-run final:
```bash
cd ansible
ansible-playbook playbooks/f17-postgres-tuning.yml -i inventory/ --tags f17-backup,f17-prune -l wfdb01 --check --diff
```

2. Aplicação real:
```bash
cd ansible
ansible-playbook playbooks/f17-postgres-tuning.yml -i inventory/ --tags f17-backup,f17-prune -l wfdb01
```

3. Verificação de banco DEV:
```bash
PG_USER=n8n_user \
PG_PASSWORD=$(python3 -c "import json;print(json.load(open('.secrets/n8n_db_wfdb02.json'))['DB_POSTGRESDB_PASSWORD'])") \
python src/purge_execution_entity.py --db-host 82.197.64.145 --db-port 6432 --db-name n8n_dev_db --check-only
```

4. Verificação de env aplicada no container remoto:
- Confirmar `EXECUTIONS_DATA_PRUNE=true`
- Confirmar preservação de F16 no override

### Critério de sucesso

- Playbook conclui sem bloquear no retorno do N8N
- `/metrics` responde 200 após restart
- `purge_execution_entity.py --check-only` roda com sucesso contra `n8n_dev_db`
- Override aplicado mantém F16 + F17 simultaneamente

### Risco residual

Se o compose real em `wfdb01` divergir dos nomes de serviço registrados em `group_vars/wfdb01.yml`, o restart continuará inconsistente. Nesse caso, a próxima ação deve ser inspecionar o compose remoto antes de reexecutar.

---

## 3. T029 — F18 Dual Collection Gate

### Estado atual

- O script `src/validate_prometheus.py` foi ajustado para a topologia real de `wfdb01`
- O playbook de auditoria continua somente leitura, mas agora descobre a topologia observável real do host
- O gate já foi executado remotamente em `wfdb01` com veredito `DUAL_COLLECTION`

### Resultado observado

- Execução remota em `wfdb01` via `ssh-wfdb01` confirmou `verdict: DUAL_COLLECTION`
- Jobs de métricas `n8n_*` encontrados: `collector_api_wf001_usa`, `collector_api_wf001_usa_ping_data`, `n8n`
- Job relacionado a Pushgateway encontrado: `pushgateway_wfdb01`
- A auditoria Ansible confirmou que `prod-collector-api` **não existe** em `wfdb01`; a proveniência deve ser inferida pela topologia do Prometheus local e pelo serviço responsável em `wf001`
- Inspeção somente leitura em `wf001` confirmou o serviço real `prod-collector-api` com:
	- `PROMETHEUS_PUSHGATEWAY_ENABLED=true`
	- `PROMETHEUS_PUSHGATEWAY_URL=https://prometheus.vya.digital/pushgateway`
	- `PROMETHEUS_PUSHGATEWAY_INTERVAL=60`
	- `PROMETHEUS_JOB_NAME=collector_api_wf001_usa`
	- exposição direta `0.0.0.0:5001 -> 5000/tcp`

### Estratégia operacional correta

Executar a validação **no próprio `wfdb01`** via `ssh-wfdb01`, usando Python remoto contra o VictoriaMetrics interno (`http://172.20.0.13:8428`). O túnel local deixa de ser a estratégia preferencial.

### Sequência recomendada

1. Executar a validação remota no host:

```bash
~/.local/bin/ssh-wfdb01 'python3 - --vm-url http://172.20.0.13:8428 --mode dual-collection --report' < src/validate_prometheus.py
```

2. Executar a auditoria somente leitura:
```bash
cd ansible
ansible-playbook playbooks/f18-dual-collection-audit.yml -i inventory/ -l wfdb01
```

3. Registrar no relatório:
- jobs reais encontrados no VictoriaMetrics (`collector_api_wf001_usa`, `collector_api_wf001_usa_ping_data`, `n8n`, `pushgateway_wfdb01`)
- ausência explícita de `prod-collector-api` em `wfdb01`
- linhas relevantes do scrape topology em `enterprise-prometheus`
- variável de controle confirmada em `wf001`: `PROMETHEUS_PUSHGATEWAY_ENABLED=true`

### Critério de sucesso

- `validate_prometheus.py` retorna `verdict: DUAL_COLLECTION` ou `SINGLE_SCRAPE` com evidência real, não por timeout
- auditoria retorna topologia observável útil mesmo quando `prod-collector-api` não existe no host
- material suficiente para preencher `contracts/prod-collector-api-issue.md`

### Risco residual

Como `prod-collector-api` não está presente em `wfdb01`, a confirmação da flag dependeu de inspeção em `wf001`. A mudança continua fora do escopo deste projeto e deve ser submetida ao projeto responsável pelo container `adminvyadigital/n8n-collector-api:latest`.

---

## 4. Ordem Recomendada de Execução

1. Rodar T025 primeiro, porque já existe avanço real de implementação e um bloqueio objetivo já foi corrigido.
2. Rodar T029 logo em seguida para fechar a dúvida de proveniência e manter F18 como pendência técnica fundamentada, não apenas inferida pelo relatório.
3. Só então revisar T026 e a sequência de promoção.

---

## 5. Decisão Operacional

A execução de T025 em `wfdb01` foi validada com sucesso. O gate T029 também já produziu evidência suficiente: `DUAL_COLLECTION` confirmado remotamente em `wfdb01`, com drift explícito entre a documentação legada (`prod-collector-api`) e a topologia real do host. O próximo passo de F18 é consolidar a issue para o projeto responsável pelo serviço que hoje expõe os jobs `collector_api_*`.

---

## 6. Execução de Continuidade — T032 a T034 (2026-04-06)

### T032 — Gates AFTER em `wfdb01`

- `check_n8n_metrics.py --metrics-url https://testn8n.vya.digital`:
	- `status: pass`
	- métricas encontradas: `n8n_scaling_mode_queue_jobs_active`, `n8n_scaling_mode_queue_jobs_waiting`, `n8n_scaling_mode_queue_jobs_completed`, `n8n_scaling_mode_queue_jobs_failed`
- `purge_execution_entity.py --check-only` em `wfdb02:n8n_dev_db`:
	- `row_count_before: 129`
	- `table_size_before_mb: 1.16`
	- execução bem-sucedida com `PG_USER=n8n_user` e segredo local `.secrets/n8n_db_wfdb02.json` (chave `db_password`)
- `validate_prometheus.py` remoto em `wfdb01` (VM interno `http://172.20.0.13:8428`, modo `dual-collection`):
	- `verdict: DUAL_COLLECTION`
	- jobs detectados: `collector_api_wf001_usa`, `collector_api_wf001_usa_ping_data`, `n8n`, `pushgateway_wfdb01`
- Smoke HTTP:
	- `/healthz` -> `200`
	- `/metrics` -> `200`
	- `/api/v1/workflows` -> `401` (endpoint protegido por autenticação)

### T033 — ProvenanceGate pós-change externo

- Execução local do modo `provenance-gate` com saída em:
	- `docs/SESSIONS/2026-04-06/f18-provenance-gate-report.json`
- Resultado:
	- `verdict: PROVENANCE_FAIL`
	- `pushgateway_absent_1h: false`
	- erro de conectividade para VM informado pelo script: `Connection refused` em `http://86.48.31.149:8428`

### T034 — Promoção em bloco para `wf001`

- **Não executado** por bloqueio de gate:
	- T033 não aprovado (`PROVENANCE_FAIL`)
	- regra do projeto exige gate completo + aprovação antes de promover F16/F17/F18 em bloco para produção

### Próxima ação operacional

1. Corrigir conectividade/rota para endpoint VM de validação do T033 (ou executar ProvenanceGate diretamente no host com endpoint interno válido).
2. Reexecutar T033 e exigir `PROVENANCE_OK`.
3. Somente após isso, abrir janela e executar T034 em `wf001` com monitoramento pós-promoção.

---

## 7. Execução Dependente do Inventário (Hardening + Revalidação)

### 7.1 Hardening aplicado em `wfdb01` (runtime)

- Cadeia `DOCKER-USER` estava vazia, confirmando ausência de contenção para portas publicadas via Docker.
- Foram aplicadas regras de bloqueio externo por interface `eth0`:
	- `DROP tcp dport 9091`
	- `DROP tcp dport 9090`
- Validação externa após aplicação:
	- `86.48.31.149:9090` -> `CLOSED`
	- `86.48.31.149:9091` -> `CLOSED`
	- `86.48.31.149:80` -> `OPEN`
	- `86.48.31.149:443` -> `OPEN`

### 7.2 Persistência das regras

- `netfilter-persistent` ausente em `wfdb01`
- `/etc/iptables` ausente em `wfdb01`
- Conclusão: regras atuais são **runtime** e podem se perder em reboot/reload.

### 7.3 Revalidação T033 no endpoint correto

- ProvenanceGate reexecutado **no próprio `wfdb01`** com VM interno `http://172.20.0.13:8428` e credenciais DB lidas de `/opt/docker_user/n8n/.env`.
- Nota: essas credenciais no `.env` do N8N em `wfdb01` apontam para o banco do N8N em `wfdb02`.
- Resultado atualizado:
	- `verdict: PROVENANCE_FAIL`
	- `pushgateway_absent_1h: false`
	- `error: null` (sem falha de conectividade)

### 7.4 Estado de T034

- Permanece bloqueado: o gate agora falha por condição funcional real (pushgateway ainda ativo), não mais por problema de rota/conectividade.

### 7.5 Nova execução de T033 (status atual)

- Reexecução em `2026-04-06T15:04:46Z` no `wfdb01`, com endpoint interno `http://172.20.0.13:8428`.
- Resultado mantido:
	- `verdict: PROVENANCE_FAIL`
	- `pushgateway_absent_1h: false`
	- `error: null`
- Observação operacional:
	- O script indicou ausência de `psycopg2` no host remoto (`cross-check PostgreSQL ignorado`), então a componente de coerência DB permanece não validada no host.

### 7.6 Execução de T034 (tentativa na sessão)

- Foi executada a parte segura/read-only de auditoria F18 via playbook:
	- `ansible-playbook ansible/playbooks/f18-dual-collection-audit.yml -i ansible/inventory/ -l wf001`
- Resultado:
	- `no hosts matched` (playbook está parametrizado para `wfdb01` nesta versão)
- Decisão aplicada:
	- Promoção em bloco para `wf001` **não executada** nesta sessão por gate T033 reprovado e por regra P0 do projeto.

### 7.7 Ação externa formalizada (enterprise-observability)

- Issue criada para correção da dupla coleta no repositório de observabilidade:
	- https://github.com/admin-vya-digital/enterprise-observability/issues/15
- Título:
	- `Fix: remover dupla coleta de métricas N8N via Pushgateway (ProvenanceGate FAIL)`
- Escopo solicitado na issue:
	- desabilitar caminho duplicado via Pushgateway para métricas N8N
	- validar `pushgateway_absent_1h=true`
	- alcançar `PROVENANCE_OK` como critério de fechamento

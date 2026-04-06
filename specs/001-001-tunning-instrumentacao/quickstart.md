# Quickstart: P1 Tunning e Instrumentação N8N (F16 + F17 + F18)

**Feature**: `001-001-tunning-instrumentacao` | **Date**: 2026-04-02

---

## Pré-requisitos

```bash
# 1. Ambiente Python local (uv)
cd /home/yves_marinho/Documentos/DevOps/Vya-Jobs/enterprise-python-n8n-tunning
uv sync                          # instala dependências

# 2. Dependências Ansible
pip install ansible ansible-lint

# 3. fwknop disponível (SSH SPA)
which fwknop || sudo apt install fwknop-client

# 4. Credenciais seguras (NUNCA no repositório)
ls .secrets/ssh.json             # SPA config por servidor
# PG_PASSWORD definida no shell ou Ansible Vault:
export PG_USER=n8n
export PG_PASSWORD="<vault>"
```

---

## Sequência de Execução (wfdb01 primeiro — gate obrigatório)

### Fase 1: Preparação — Coleta de métricas BEFORE

```bash
# Snapshot antes de qualquer mudança
python src/collect_gate_evidence.py \
  --feature F16 --environment wfdb01 \
  --vm-url http://86.48.31.149:8428 \
  --output-dir docs/SESSIONS/$(date +%Y-%m-%d)/

python src/collect_gate_evidence.py \
  --feature F17 --environment wfdb01 \
  --vm-url http://86.48.31.149:8428 \
  --output-dir docs/SESSIONS/$(date +%Y-%m-%d)/

python src/validate_prometheus.py \
  --vm-url http://86.48.31.149:8428  # deve retornar DUAL_COLLECTION
```

### Fase 2: Aplicar F16 em wfdb01

```bash
# Dry-run primeiro
ansible-playbook ansible/playbooks/f16-queue-metrics.yml \
  -i ansible/inventory/ -l wfdb01 --check --diff

# Aplicar
ansible-playbook ansible/playbooks/f16-queue-metrics.yml \
  -i ansible/inventory/ -l wfdb01

# Verificar
python src/check_n8n_metrics.py --host 86.48.31.149 --port 5001
```

### Fase 3: Aplicar F17 em wfdb01 (purgação + pg_stat_statements)

```bash
# PARTE A: Backup wfdb02 antes de qualquer operação PostgreSQL
ansible-playbook ansible/playbooks/f17-postgres-tuning.yml \
  --tags f17-backup -i ansible/inventory/

# PARTE B: Ativar purgação (sem restart de PostgreSQL)
ansible-playbook ansible/playbooks/f17-postgres-tuning.yml \
  --tags f17-prune -l wfdb01 -i ansible/inventory/

# PARTE C1: Validar pg_stat_statements em n8n_dev_db (DEV — OBRIGATÓRIO ANTES DE n8n_db)
# ⚠️ O ambiente DEV de PostgreSQL agora é o banco n8n_dev_db no próprio wfdb02
ansible-playbook ansible/playbooks/f17-postgres-tuning.yml \
  --tags f17-pgstat -l wfdb02 -i ansible/inventory/ \
  -e f17_pgstat_approved=true

# Verificar contagem e acesso no banco DEV
python src/purge_execution_entity.py \
  --db-host 82.197.64.145 --db-port 6432 \
  --db-name n8n_dev_db --check-only

# PARTE C2: Operações posteriores em n8n_db (produção lógica)
# Requer: validação prévia em n8n_dev_db + janela aprovada pelo project-manager
python src/purge_execution_entity.py \
  --db-host 82.197.64.145 --db-port 6432 \
  --db-name n8n_db --check-only
```

### Fase 4: F18 — Diagnóstico de Dupla Coleta e Geração de Change Request

```bash
# PASSO 1: Inspecionar prod-collector-api (SOMENTE LEITURA — NÃO modificar)
ssh -p 5010 docker_user@86.48.31.149 \
  'docker inspect prod-collector-api | python3 -c "import json,sys; env=json.load(sys.stdin)[0][\"Config\"][\"Env\"]; [print(e) for e in env if \"prometheus\" in e.lower() or \"pushgateway\" in e.lower()]"'
# → Documentar o nome exato da variável de controle encontrada no relatório

# PASSO 2: Confirmar dupla coleta via PromQL
python src/validate_prometheus.py \
  --vm-url http://86.48.31.149:8428 \
  --report --output docs/SESSIONS/$(date +%Y-%m-%d)/f18-dual-collection-report.json
# Esperado: DUAL_COLLECTION confirmado; json inclui séries identificadas e labels

# PASSO 3: Registrar artefato de change request
# Preencher specs/001-001-tunning-instrumentacao/contracts/prod-collector-api-issue.md
# com os dados coletados nos passos 1 e 2 e submeter ao projeto responsável
# ⚠️ F18 NÃO modifica prod-collector-api diretamente.
# A validação ProvenanceGate (Fase 5 extended) será executada APÓS o projeto
# responsável aplicar a mudança.
```

### Fase 5: Gate wfdb01 — Evidências AFTER

```bash
# Coletar métricas after para todas as features
for feature in F16 F17 F18; do
  python src/collect_gate_evidence.py \
    --feature $feature --environment wfdb01 \
    --vm-url http://86.48.31.149:8428 \
    --output-dir docs/SESSIONS/$(date +%Y-%m-%d)/
done

# Smoke tests obrigatórios
curl -sf http://86.48.31.149:5001/healthz && echo "healthz: PASS"
curl -sf http://86.48.31.149:5001/metrics | grep -q "n8n_queue" && echo "queue metrics: PASS"
# Aguardar 1 ciclo de pico (13:00-22:00 UTC) antes de promover para wf001
```

### Fase 6: Promoção em BLOCO para wf001 (após gate wfdb01)

> **⚠️ PROMOÇÃO EM BLOCO**: F16, F17 **e** F18 DEVEM ser promovidos juntos.
> Nenhuma feature pode ser promovida individualmente para wf001.
> F18 só entra no gate após ProvenanceGate validado (Fase 5 extended).

```bash
# SOMENTE após aprovação do gate por test_engineer para F16, F17 E F18
ansible-playbook ansible/playbooks/f16-queue-metrics.yml \
  -i ansible/inventory/ -l wf001

ansible-playbook ansible/playbooks/f17-postgres-tuning.yml \
  --tags f17-prune -l wf001 -i ansible/inventory/
# NOTA: f17-pgstat em wf001 requer janela de manutenção separada

# F18 em wf001: executar diagnóstico + submeter change request ao projeto responsável
# (mesmo processo da Fase 4, mas contra wf001)
```

---

## Rollback (qualquer feature, qualquer ambiente)

```bash
# Reverter variáveis de ambiente N8N (F16/F17)
ssh -p 5010 docker_user@<host> \
  'cd /opt/docker_user/n8n && rm -f docker-compose.override.yml && docker compose up -d n8n'

# F18: não há rollback de playbook (prod-collector-api não foi modificado por este projeto)
# Caso o projeto responsável já tenha aplicado a mudança, solicitar reversão via issue

# Restaurar PostgreSQL do backup (F17 — emergência)
gunzip -c /tmp/n8n_backup_*.sql.gz | psql -h 82.197.64.145 -p 6432 -U n8n n8n_db
```

---

## Validação lint dos Playbooks

```bash
make lint          # executa ansible-lint em ansible/playbooks/
# Ou diretamente:
ansible-lint ansible/playbooks/f16-queue-metrics.yml
ansible-lint ansible/playbooks/f17-postgres-tuning.yml
ansible-lint ansible/playbooks/f18-fix-dual-collection.yml
```

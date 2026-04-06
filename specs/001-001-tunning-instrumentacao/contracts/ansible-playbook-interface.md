# Contract: Ansible Playbook Interface

**Interface**: Ansible playbooks executados via `ansible-playbook` ou `make`
**Consumers**: Operador DevOps, CI pipeline
**Relevante para**: F16, F17, F18

---

## Inventário

```yaml
# ansible/inventory/hosts.yml
all:
  children:
    wfdb01:
      hosts:
        wfdb01.vya.digital:
          ansible_host: 86.48.31.149
          ansible_port: 5010          # SSH SPA port
          ansible_user: docker_user
    wf001:
      hosts:
        wf001.vya.digital:
          ansible_host: 31.220.103.208
          ansible_port: 5010
          ansible_user: docker_user
    wfdb02:
      hosts:
        wfdb02.vya.digital:
          ansible_host: 82.197.64.145
          ansible_port: 5010
          ansible_user: docker_user
```

## Variáveis Obrigatórias (group_vars)

```yaml
# ansible/inventory/group_vars/all.yml (sem credenciais)
n8n_compose_dir: /opt/docker_user/n8n
n8n_queue_alert_threshold: 100        # n8n_queue_depth alerta
n8n_prune_max_age_hours: 720          # 30 dias
n8n_prune_timeout_ms: 3600000

# wfdb02-específico
db_host: 82.197.64.145
db_port: 6432                         # PostgreSQL direto
db_pgbouncer_port: 5432               # Pgbouncer
db_name: n8n_dev_db                   # gate DEV atual
db_name_prod: n8n_db                  # referência para fase posterior
```

## Execução dos Playbooks

```bash
# SPA knock + playbook (play 1 = knock, play 2 = deploy)
ansible-playbook ansible/playbooks/f16-queue-metrics.yml -i ansible/inventory/

# Tag por feature
ansible-playbook ansible/playbooks/f17-postgres-tuning.yml \
  --tags f17 \
  --extra-vars "backup_dir=/tmp"

# Dry-run obrigatório antes de qualquer execução em wf001
# F18: diagnóstico de dupla coleta (SOMENTE LEITURA — não modifica prod-collector-api)
ansible-playbook ansible/playbooks/f18-dual-collection-audit.yml \
  --check --diff -l wfdb01
```

## Convenções de Tags

| Tag | Escopo |
|-----|--------|
| `f16` | Tasks de métricas de fila |
| `f17` | Tasks de PostgreSQL tuning |
| `f17-backup` | Apenas backup pg_dump |
| `f17-prune` | Apenas configuração de purgação |
| `f17-pgstat` | Apenas pg_stat_statements |
| `f18` | Diagnóstico de dupla coleta (somente leitura) + geração de change request |
| `gate` | Smoke tests e coleta de evidências |
| `wfdb01` | Executar apenas em wfdb01 |
| `wf001` | Executar apenas em wf001 |

## Estrutura Obrigatória de Cada Playbook

```yaml
---
# Play 1: SPA Knock (OBRIGATÓRIO para todos os VPS)
- name: SPA Knock - {{ target_host }}
  hosts: localhost
  connection: local
  tasks:
    - name: Knock SSH SPA
      command: fwknop --rc-file ~/.fwknoprc -n {{ inventory_hostname }}
    - name: Wait for SSH port
      wait_for:
        host: "{{ ansible_host }}"
        port: 5010
        timeout: 30

# Play 2: Feature task
- name: F1x - Description
  hosts: <group>
  become: false
  tags: [f1x]
  tasks:
    - name: Assert compose dir exists
      stat:
        path: "{{ n8n_compose_dir }}/docker-compose.yml"
      register: compose_stat
    - assert:
        that: compose_stat.stat.exists
        fail_msg: "docker-compose.yml not found at {{ n8n_compose_dir }}"
```

## Saídas Esperadas

| Artefato | Localização | Descrição |
|----------|-------------|-----------|
| `docker-compose.override.yml` | `/opt/docker_user/n8n/` | Vars adicionadas (F16/F17) |
| `pg_dump` | configurável via `backup_dir` | Backup wfdb02 (F17) |
| `gate_evidence_*.json` | `docs/SESSIONS/YYYY-MM-DD/` | Evidências before/after |
| Logs Ansible | stdout + `scripts/logs/` | Rastreabilidade de execução |

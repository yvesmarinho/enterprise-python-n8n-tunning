# 📅 Janela de Manutenção T034a — AGENDADA

**Projeto**: enterprise-python-n8n-tunning
**Spec**: 001-001-tunning-instrumentacao
**Tarefa**: T034a — Promoção F16+F17 para wf001 (PRODUÇÃO)
**Data de Agendamento**: 2026-05-05

---

## 🕐 Janela Programada

**Data**: Sábado, 10 de maio de 2026  
**Horário**: 02h00 – 04h00 UTC (23h00 – 01h00 BRT, 09/05)  
**Duração estimada**: 90 minutos (2h reservadas)  
**Tipo**: Manutenção Programada — Instrumentação N8N

---

## 🎯 Escopo da Janela

### Mudanças Aplicadas

**Servidor**: wf001.vya.digital (31.220.103.208) — N8N PRODUÇÃO

| Feature | Descrição | Impacto Esperado |
|---------|-----------|------------------|
| **F16** | Habilitar métricas de fila N8N | Zero downtime — apenas adiciona variáveis env |
| **F17 Vetor A** | Purgação automática execution_entity | Zero downtime — política de retenção 30 dias |

**Banco de dados**: wfdb02 (82.197.64.145) — PostgreSQL PRODUÇÃO
- Backup completo `n8n_db` antes de qualquer operação
- Nenhuma mudança em schema (apenas backup preventivo)

### Serviços Afetados

| Serviço | Impacto | Downtime Estimado |
|---------|---------|-------------------|
| N8N (wf001) | Restart container | < 30 segundos |
| Workflows 121Labs PABX | Execuções pausadas durante restart | < 30 segundos |
| WhatsApp Gateway | Execuções pausadas durante restart | < 30 segundos |
| PostgreSQL (wfdb02) | Sem restart | Zero |

---

## ✅ Pré-requisitos (Checklist)

### 48h Antes (2026-05-08 02h00 UTC)

- [ ] **Notificar stakeholders**
  - [ ] 121Labs — workflows PABX call-analytics (429K exec/90d)
  - [ ] Cliente WhatsApp Gateway — Evolution API integration (84K exec)
  - [ ] Equipe interna Vya
  
- [ ] **Confirmar disponibilidade da equipe**
  - [ ] DevOps Engineer (responsável por execução)
  - [ ] Project Manager (aprovação final)
  - [ ] Suporte standby (01h30–05h00 UTC)

### 24h Antes (2026-05-09 02h00 UTC)

- [ ] **Aprovação final project-manager**
  - [ ] Revisão de riscos
  - [ ] Confirmação de plano de rollback
  - [ ] Go/No-Go decision

- [ ] **Dry-run final em wfdb01**
  ```bash
  cd ansible
  ansible-playbook playbooks/t034a-promote-f16-f17-wf001.yml \
    -i inventory/ --check --diff
  ```
  - [ ] Zero erros reportados
  - [ ] Backup target confirmado: `n8n_db`
  - [ ] Verificações healthz/metrics funcionais

- [ ] **Backup validado**
  - [ ] Backup `n8n_db` executado em wfdb02
  - [ ] SHA-256 checksum registrado
  - [ ] Restore-test aprovado (opcional, mas recomendado)

### 1h Antes (2026-05-10 01h00 UTC)

- [ ] **Baseline de métricas coletado**
  - [ ] Throughput N8N atual (exec/hora)
  - [ ] Latência média workflows críticos
  - [ ] CPU/memória wf001
  - [ ] Tamanho `execution_entity` (row count)

- [ ] **Equipe em standby confirmada**

---

## 🚀 Plano de Execução

### Fase 1: Preparação (02h00 – 02h15 UTC)

```bash
# 1. Coletar baseline BEFORE
cd ~/Documentos/DevOps/Vya-Jobs/enterprise-python-n8n-tunning
python src/collect_gate_evidence.py \
  --feature F16 \
  --environment wf001 \
  --vm-url http://localhost:8428 \
  --output-dir docs/SESSIONS/2026-05-10/

# 2. Validar conectividade
ssh wf001 'docker ps | grep n8n'
ssh wfdb02 'psql -h localhost -p 6432 -U n8n -c "SELECT count(*) FROM execution_entity;"'

# 3. Confirmar backup
ssh wfdb02 'ls -lh /tmp/n8n_backup_*.sql.gz | tail -1'
```

### Fase 2: Execução T034a (02h15 – 02h45 UTC)

```bash
cd ansible

# 1. Dry-run final
ansible-playbook playbooks/t034a-promote-f16-f17-wf001.yml \
  -i inventory/ --check --diff

# 2. Execução real
ansible-playbook playbooks/t034a-promote-f16-f17-wf001.yml \
  -i inventory/

# Output esperado:
# PLAY RECAP
# localhost          : ok=5   changed=2
# wf001.vya.digital  : ok=12  changed=2  failed=0
# wfdb02.vya.digital : ok=2   changed=0  failed=0
```

### Fase 3: Validação (02h45 – 03h15 UTC)

```bash
# 1. Healthz check
curl -sf https://n8n.vya.digital/healthz

# 2. Métricas endpoint
curl -sf https://n8n.vya.digital/metrics | grep -E "(n8n_queue|n8n_workflow)"

# 3. Workflows críticos
# - Testar trigger manual em workflow de teste
# - Validar que workflows 121Labs e WhatsApp continuam executando

# 4. Coletar evidências AFTER
python src/collect_gate_evidence.py \
  --feature F16 \
  --environment wf001 \
  --vm-url http://localhost:8428 \
  --output-dir docs/SESSIONS/2026-05-10/
```

### Fase 4: Documentação (03h15 – 04h00 UTC)

```bash
# 1. Consolidar evidências em SESSION_REPORT
# 2. Confirmar métricas F16 visíveis no VictoriaMetrics
# 3. Registrar baseline before/after
# 4. Fechar janela com status SUCESSO/ROLLBACK
```

---

## 🔄 Plano de Rollback

**Trigger**: Se após 30 minutos de aplicação houver:
- Falha de healthz persistente (> 3 tentativas)
- Workflows críticos não executando
- Erro não previsto em logs N8N

**Procedimento de rollback** (< 5 minutos):

```bash
# 1. Conectar em wf001
ssh wf001

# 2. Restaurar docker-compose.override.yml anterior
cd /opt/docker_user/n8n
git checkout HEAD~1 docker-compose.override.yml

# 3. Restart container
docker compose up -d n8n

# 4. Validar healthz
curl -sf https://n8n.vya.digital/healthz

# 5. Se persistir problema, restaurar backup PostgreSQL (estimativa: 15-20 min)
ssh wfdb02
gunzip -c /tmp/n8n_backup_YYYYMMDDTHHMMSS.sql.gz | \
  psql -h localhost -p 6432 -U n8n n8n_db
```

---

## 📊 Critérios de Sucesso

| Critério | Verificação | Target |
|----------|-------------|--------|
| **Healthz** | `curl https://n8n.vya.digital/healthz` | HTTP 200 |
| **Métricas F16** | `curl /metrics \| grep n8n_queue` | 4+ séries ativas |
| **Workflows críticos** | Execução manual de teste | Sucesso < 5s |
| **Downtime** | Tempo entre stop e start container | < 60 segundos |
| **Rollback** | Se necessário, tempo de restauração | < 5 minutos |

---

## 📝 Comunicação

### Notificação aos Stakeholders (2026-05-08)

**Assunto**: Janela de Manutenção N8N — Sábado 10/05 02h-04h UTC

**Corpo**:
> Prezados,
> 
> Informamos que realizaremos manutenção programada no servidor N8N de produção (wf001.vya.digital) no dia **10 de maio de 2026**, das **02h00 às 04h00 UTC** (23h00 de 09/05 às 01h00 de 10/05, horário de Brasília).
> 
> **Escopo**: Habilitação de métricas de fila e otimização de retenção de dados (features F16 e F17).
> 
> **Impacto**: Restart do container N8N com downtime estimado de **menos de 1 minuto**. Workflows PABX (121Labs) e WhatsApp Gateway (Evolution API) pausarão brevemente durante o restart.
> 
> **Rollback**: Plano de reversão em menos de 5 minutos se necessário.
> 
> Em caso de dúvidas, favor responder este e-mail.
> 
> Atenciosamente,  
> Equipe DevOps Vya

---

## 👥 Equipe Responsável

| Papel | Nome | Responsabilidade | Contato |
|-------|------|------------------|---------|
| **DevOps Engineer** | [Nome] | Execução T034a | [Email/Tel] |
| **Project Manager** | [Nome] | Aprovação Go/No-Go | [Email/Tel] |
| **Suporte Standby** | [Nome] | Rollback/troubleshooting | [Email/Tel] |

---

## 📎 Documentos Relacionados

- [docs/TODO.md](../../TODO.md) — P0 atualizado com janela agendada
- [ansible/playbooks/t034a-promote-f16-f17-wf001.yml](../../../ansible/playbooks/t034a-promote-f16-f17-wf001.yml) — Playbook de execução
- [specs/001-001-tunning-instrumentacao/spec.md](../../../specs/001-001-tunning-instrumentacao/spec.md) — User Stories F16, F17
- [docs/SESSIONS/2026-05-04/SESSION_REPORT_2026-05-04.md](../../2026-05-04/SESSION_REPORT_2026-05-04.md) — Bugs #1, #2 corrigidos
- [docs/SESSIONS/2026-05-05/PROJECT_COMPLIANCE_ANALYSIS_2026-05-05.md](PROJECT_COMPLIANCE_ANALYSIS_2026-05-05.md) — Análise de conformidade

---

**Status**: 🟡 AGENDADA — Aguardando aprovação final project-manager  
**Próxima ação**: Notificar stakeholders em 2026-05-08 02h00 UTC  
**Responsável por follow-up**: DevOps Engineer

---

*Documento criado em 2026-05-05 — Janela de manutenção T034a*

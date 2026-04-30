# 🔧 Runbook Operacional — T034a: Promoção F16+F17 para wf001 (PRODUÇÃO)

**ID**: T034a
**Janela de Manutenção**: Sábado 02h-04h UTC (Sexta 23h-01h BRT)
**Duração Estimada**: 25-30 minutos (aplicação) + 10 min (verificação) = **35-40 minutos total**
**Rollback Time**: 25-35 minutos (se necessário)
**Operador**: DevOps Engineer
**Aprovador**: Project Manager

---

## ✅ Pré-requisitos Obrigatórios (Validar ANTES da Janela)

Todos devem estar ✅ antes de iniciar T034a:

- [ ] **T017** ✅ — F16 validado em wfdb01 (queue metrics funcionando)
- [ ] **T025** ✅ — F17 Vetor A validado em wfdb01 (purgação funcionando)
- [ ] **T026** ✅ — F17 Vetor B validado em wfdb02:n8n_dev_db (pg_stat_statements ativo)
- [ ] **T031** ✅ — ansible-lint aprovado para todos os playbooks
- [ ] **T032** ✅ — Smoke tests wfdb01 passando (healthz, métricas, API)
- [ ] **T036** ✅ — Verificação de execuções presas em wf001 (0 execuções stuck)
- [ ] **Aprovação PM** — Janela de manutenção comunicada aos clientes (121Labs, WhatsApp Gateway)
- [ ] **Backup wfdb02** — Último backup PostgreSQL < 24h

---

## 📋 Checklist Operacional — Sequência de Execução

### **Fase 0: Preparação (T-15min — 01h45 UTC)**

- [ ] **0.1** Conectar SSH aos servidores (validar acesso)
  ```bash
  # Terminal 1: wf001
  make ssh-spa-knock-one HOST=wf001
  ssh -p 5010 archaris@31.220.103.208

  # Terminal 2: wfdb02
  make ssh-spa-knock-one HOST=wfdb02
  ssh -p 5010 archaris@82.197.64.145
  ```

- [ ] **0.2** Validar status atual N8N wf001
  ```bash
  # Em wf001
  cd /opt/docker_user/n8n
  docker compose ps
  docker inspect n8n-n8n_editor-1 --format '{{.State.Status}}'
  curl -sf https://n8n.vya.digital/healthz && echo "HEALTHY"
  ```

- [ ] **0.3** Validar status atual PostgreSQL wfdb02
  ```bash
  # Em wfdb02
  psql -h localhost -p 6432 -U n8n_user -d n8n_db -c "SELECT COUNT(*) FROM execution_entity;"
  # Anotar valor: _____________
  ```

- [ ] **0.4** Criar diretório de evidências na sessão local
  ```bash
  # Local
  mkdir -p docs/SESSIONS/2026-05-03/t034a-evidence
  ```

---

### **Fase 1: Coleta BEFORE (T-10min — 01h50 UTC)**

- [ ] **1.1** Coletar métricas BEFORE — CPU, latência p95, volume exec/min
  ```bash
  # Local (criar script se não existir)
  python3 src/collect_n8n_metrics_7d.py \
    --vm-url http://wfdb01:8428 \
    --output docs/SESSIONS/2026-05-03/t034a-evidence/before-metrics.json
  ```

  **Alternativa manual** (se script não disponível):
  ```bash
  # Anotar manualmente:
  # - CPU wf001: ____%
  # - Latência p95 últimos 30min: ____ms
  # - Volume exec/min: ____
  ```

- [ ] **1.2** Verificar tamanho execution_entity
  ```bash
  # Em wfdb02
  psql -h localhost -p 6432 -U n8n_user -d n8n_db <<SQL
  SELECT
    COUNT(*) as total_rows,
    pg_size_pretty(pg_total_relation_size('execution_entity')) as table_size,
    COUNT(*) FILTER (WHERE "finishedAt" < NOW() - INTERVAL '30 days') as rows_older_30d
  FROM execution_entity;
  SQL
  ```

  **Anotar valores**:
  - Total rows: _____________
  - Table size: _____________
  - Rows > 30d: _____________

- [ ] **1.3** Coletar lista de workflows ativos (baseline)
  ```bash
  # Em wf001
  curl -sf https://n8n.vya.digital/api/v1/workflows | jq '.data | length'
  # Total workflows: _____________
  ```

---

### **Fase 2: Rollback Anchor (T-5min — 01h55 UTC)**

- [ ] **2.1** Salvar hash da imagem Docker atual
  ```bash
  # Em wf001
  docker inspect n8n-n8n_editor-1 --format '{{.Image}}' | tee /tmp/t034a-rollback-anchor.txt
  ```

  **Anotar hash**: _____________________________________________

- [ ] **2.2** Backup do docker-compose.yml e .env atual
  ```bash
  # Em wf001
  cd /opt/docker_user/n8n
  cp docker-compose.yml docker-compose.yml.t034a-backup-$(date +%Y%m%d-%H%M%S)
  cp .env .env.t034a-backup-$(date +%Y%m%d-%H%M%S)

  # Se override existir, fazer backup também
  [ -f docker-compose.override.yml ] && \
    cp docker-compose.override.yml docker-compose.override.yml.t034a-backup-$(date +%Y%m%d-%H%M%S)

  ls -lh *.t034a-backup-*
  ```

- [ ] **2.3** Criar snapshot do estado PostgreSQL (opcional, se tempo permitir)
  ```bash
  # Em wfdb02 — apenas registrar contagem, backup completo já existe
  psql -h localhost -p 6432 -U n8n_user -d n8n_db \
    -c "SELECT COUNT(*), MIN(startedAt), MAX(finishedAt) FROM execution_entity;" \
    > /tmp/t034a-pg-state-before.txt
  ```

---

### **Fase 3: Backup PostgreSQL Obrigatório (T+0 — 02h00 UTC)**

- [ ] **3.1** Executar playbook — Play 2: Backup pg_dump (via Ansible)
  ```bash
  # Local
  ansible-playbook ansible/playbooks/t034a-promote-f16-f17-wf001.yml \
    -i ansible/inventory/ \
    --tags f17-backup \
    --check --diff  # dry-run primeiro
  ```

  **Validar output**:
  - ✅ `PLAY RECAP` mostra `failed=0`
  - ✅ Arquivo de backup criado em wfdb02

- [ ] **3.2** Aplicar backup (sem --check)
  ```bash
  ansible-playbook ansible/playbooks/t034a-promote-f16-f17-wf001.yml \
    -i ansible/inventory/ \
    --tags f17-backup
  ```

  **Tempo estimado**: 10-15 minutos

- [ ] **3.3** Validar integridade do backup
  ```bash
  # Em wfdb02
  ls -lh /tmp/n8n_db_backup_*.sql.gz
  # Tamanho > 100MB? _____ (sim/não)

  gunzip -t /tmp/n8n_db_backup_*.sql.gz && echo "BACKUP VÁLIDO"
  ```

---

### **Fase 4: Aplicação F16 — Queue Metrics (T+15min — 02h15 UTC)**

- [ ] **4.1** Executar playbook F16 em wf001 (dry-run)
  ```bash
  # Local
  ansible-playbook ansible/playbooks/t034a-promote-f16-f17-wf001.yml \
    -i ansible/inventory/ \
    --tags f16 \
    --check --diff
  ```

  **Validar output esperado**:
  - ✅ `TASK [n8n_env : template docker-compose.override.j2]` mostra diff com variáveis F16
  - ✅ Nenhum erro de sintaxe Ansible

- [ ] **4.2** Aplicar F16 (sem --check)
  ```bash
  ansible-playbook ansible/playbooks/t034a-promote-f16-f17-wf001.yml \
    -i ansible/inventory/ \
    --tags f16
  ```

  **Tempo estimado**: 3-5 minutos (inclui restart N8N)

- [ ] **4.3** Validar N8N reiniciou corretamente
  ```bash
  # Aguardar 30-90 segundos, depois:
  curl -sf https://n8n.vya.digital/healthz && echo "HEALTHY"
  curl -sf https://n8n.vya.digital/metrics | grep -E "^n8n_queue" | head -5
  ```

  **Critério de sucesso**:
  - ✅ `/healthz` retorna 200
  - ✅ Métricas `n8n_queue_*` visíveis em `/metrics`

---

### **Fase 5: Aplicação F17 — PostgreSQL Purgação (T+20min — 02h20 UTC)**

- [ ] **5.1** Executar playbook F17 Vetor A — EXECUTIONS_DATA_PRUNE (dry-run)
  ```bash
  ansible-playbook ansible/playbooks/t034a-promote-f16-f17-wf001.yml \
    -i ansible/inventory/ \
    --tags f17-prune \
    --check --diff
  ```

  **Validar output esperado**:
  - ✅ Variáveis `EXECUTIONS_DATA_PRUNE=true` no override
  - ✅ Diff mostra apenas adição de variáveis F17

- [ ] **5.2** Aplicar F17 Vetor A (sem --check)
  ```bash
  ansible-playbook ansible/playbooks/t034a-promote-f16-f17-wf001.yml \
    -i ansible/inventory/ \
    --tags f17-prune
  ```

  **Tempo estimado**: 3-5 minutos (inclui restart N8N)

- [ ] **5.3** Validar N8N reiniciou após F17
  ```bash
  curl -sf https://n8n.vya.digital/healthz && echo "HEALTHY"
  ```

- [ ] **5.4** Verificar se purgação automática está agendada
  ```bash
  # Em wf001
  docker logs n8n-n8n_editor-1 --tail 100 | grep -i "prune\|cleanup\|deletion"
  ```

  **Anotar se logs mostram**: _____________________________________________

---

### **Fase 6: Verificação AFTER (T+25min — 02h25 UTC)**

- [ ] **6.1** Smoke tests — healthz + métricas + API workflows
  ```bash
  # healthz
  curl -sf https://n8n.vya.digital/healthz && echo "✅ HEALTHY"

  # métricas
  curl -sf https://n8n.vya.digital/metrics | grep -c "^n8n_"
  # Total métricas N8N: _____ (esperado ≥ 20)

  # API workflows (deve retornar lista)
  curl -sf https://n8n.vya.digital/api/v1/workflows | jq '.data | length'
  # Total workflows: _____ (comparar com baseline Fase 1.3)
  ```

- [ ] **6.2** Verificar métricas de fila (F16)
  ```bash
  curl -sf https://n8n.vya.digital/metrics | grep -E "^n8n_queue"
  ```

  **Critério de sucesso**:
  - ✅ `n8n_queue_depth` presente
  - ✅ Valor numérico (pode ser 0.0 se fila vazia)

- [ ] **6.3** Verificar logs N8N — nenhum erro crítico
  ```bash
  # Em wf001
  docker logs n8n-n8n_editor-1 --tail 200 | grep -iE "error|fatal|exception" | wc -l
  # Total erros: _____ (esperado = 0)
  ```

- [ ] **6.4** Coletar métricas AFTER (comparar com BEFORE)
  ```bash
  # Local — coletar CPU, latência, volume
  # (usar mesmo método da Fase 1.1)
  ```

- [ ] **6.5** Testar execução de workflow teste (opcional, se disponível)
  ```bash
  # Disparar manualmente workflow de teste em https://n8n.vya.digital
  # Workflow ID: ___________
  # Resultado: SUCESSO / FALHA
  ```

---

### **Fase 7: Monitoramento Pós-Deploy (T+30min — 02h30 UTC)**

- [ ] **7.1** Configurar alerta temporário para n8n_queue_depth
  ```bash
  # Verificar se alerta foi criado automaticamente pelo playbook
  # (se houver acesso ao Prometheus, validar rule ativa)
  ```

- [ ] **7.2** Observar métricas por 15-20 minutos (até 02h50 UTC)
  - Fila N8N: `n8n_queue_depth` deve permanecer baixa (< 10)
  - CPU wf001: deve permanecer < 5% (fora do horário de pico)
  - Nenhum spike de latência anormal

- [ ] **7.3** Verificar se purgação PostgreSQL executou primeiro ciclo
  ```bash
  # Em wfdb02 — verificar se linhas antigas começaram a ser removidas
  # (pode levar 1-2 horas para primeiro ciclo)
  psql -h localhost -p 6432 -U n8n_user -d n8n_db \
    -c "SELECT COUNT(*) FROM execution_entity WHERE finishedAt < NOW() - INTERVAL '30 days';"
  # Rows > 30d: _____ (comparar com Fase 1.2)
  ```

---

### **Fase 8: Documentação e Encerramento (T+40min — 02h40 UTC)**

- [ ] **8.1** Coletar evidências finais
  ```bash
  # Local — consolidar todos os arquivos de evidência em um único relatório
  ls -lh docs/SESSIONS/2026-05-03/t034a-evidence/
  ```

- [ ] **8.2** Atualizar SESSION_REPORT_2026-05-03.md
  - Seção "T034a Execution Summary"
  - Métricas BEFORE vs AFTER
  - Status: SUCESSO / FALHA / ROLLBACK
  - Problemas encontrados (se houver)

- [ ] **8.3** Criar registro CHAT-YYYYMMDD-HHMMSS.md em docs/copilot/
  - Resumo da execução
  - Decisões tomadas durante a janela
  - Artefatos gerados

- [ ] **8.4** Commit + push das evidências
  ```bash
  # Local
  git add docs/SESSIONS/2026-05-03/
  git commit -F <(cat <<EOF
  feat(t034a): Promoção F16+F17 para wf001 (PRODUÇÃO)

  - F16: Queue metrics habilitadas
  - F17: PostgreSQL purgação ativada (Vetor A)
  - Backup wfdb02 validado
  - Smoke tests: PASS
  - Evidências: docs/SESSIONS/2026-05-03/t034a-evidence/

  Refs: T034a, ANA-001
  EOF
  )
  git push origin 001-001-tunning-instrumentacao
  ```

- [ ] **8.5** Comunicar conclusão ao Project Manager
  - Status da janela: CONCLUÍDA / PARCIAL / ROLLBACK
  - Próximos passos: Monitorar 121Labs pico (13h-22h UTC sábado)

---

## 🔴 Procedimento de Rollback (Se Necessário)

**Gatilhos de rollback**:
- ❌ N8N não reinicia após aplicação de F16 ou F17
- ❌ Healthz retorna erro por > 2 minutos
- ❌ Métricas `n8n_queue_*` não aparecem após 5 minutos
- ❌ Erros críticos em logs Docker (OOM, crash loop)
- ❌ API `/workflows` não responde

### **Rollback F17 (se aplicado)**

```bash
# Em wf001
cd /opt/docker_user/n8n

# Restaurar docker-compose.override.yml anterior
cp docker-compose.override.yml.t034a-backup-YYYYMMDD-HHMMSS docker-compose.override.yml

# Restart container
docker compose up -d n8n

# Verificar
curl -sf https://n8n.vya.digital/healthz
```

**Tempo estimado**: 5 minutos

### **Rollback F16 (se F17 não foi aplicado ainda)**

```bash
# Mesmo procedimento acima
cd /opt/docker_user/n8n
cp docker-compose.override.yml.t034a-backup-YYYYMMDD-HHMMSS docker-compose.override.yml
docker compose up -d n8n
```

### **Rollback PostgreSQL (CENÁRIO EXTREMO — corrupção de dados)**

```bash
# Em wfdb02
# ATENÇÃO: Procedimento destrutivo, usar apenas se confirmado corrupção

# 1. Parar N8N em wf001 (evitar writes)
# Em wf001:
docker compose stop n8n

# 2. Restaurar backup
# Em wfdb02:
gunzip -c /tmp/n8n_db_backup_YYYYMMDD-HHMMSS.sql.gz | \
  psql -h localhost -p 6432 -U n8n_user -d n8n_db

# 3. Reiniciar N8N
# Em wf001:
docker compose up -d n8n
```

**Tempo estimado**: 20-30 minutos

---

## 📊 Critérios de Sucesso (Definição de "DONE")

✅ **T034a é considerado BEM-SUCEDIDO se**:

1. ✅ F16: Métricas `n8n_queue_depth`, `n8n_queue_waiting`, `n8n_queue_active` visíveis em `/metrics`
2. ✅ F17: Variáveis `EXECUTIONS_DATA_PRUNE=true` presentes no container N8N
3. ✅ Healthz retorna 200 por ≥ 10 minutos consecutivos
4. ✅ API `/workflows` retorna lista completa de workflows (comparar com baseline)
5. ✅ Logs Docker sem erros críticos (ERROR/FATAL) nos primeiros 30 minutos
6. ✅ Backup PostgreSQL criado e validado (tamanho > 100MB, gunzip -t PASS)
7. ✅ Evidências documentadas em SESSION_REPORT

---

## 📞 Contatos de Emergência

| Papel | Nome | Contato | Disponibilidade |
|-------|------|---------|-----------------|
| Project Manager | TBD | TBD | On-call durante janela |
| DevOps Lead | TBD | TBD | Backup operator |
| Cliente 121Labs | TBD | TBD | Notificar apenas se rollback necessário |

---

## 📝 Notas e Observações

**Data de criação**: 2026-04-30
**Última atualização**: 2026-04-30
**Próxima revisão**: Antes da janela (2026-05-03 01h30 UTC)

**Observações importantes**:
- Janela escolhida (sábado 02h-04h UTC) evita pico 121Labs PABX (13h-22h UTC)
- Primeira purgação PostgreSQL pode levar 1-2h para executar (400K+ linhas)
- Monitoramento pós-deploy continua até segunda-feira 09h00 UTC (cobertura de 1 ciclo completo de pico)
- F17 Vetor B (pg_stat_statements em n8n_db prod) **NÃO faz parte de T034a** — será executado em janela separada

---

*Runbook gerado por GitHub Copilot em 2026-04-30T12:10Z*
*Baseado em: ansible/playbooks/t034a-promote-f16-f17-wf001.yml + specs/001-001-tunning-instrumentacao/tasks.md*

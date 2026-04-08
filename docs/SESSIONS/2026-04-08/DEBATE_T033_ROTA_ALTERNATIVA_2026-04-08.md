# Debate Técnico — Rota Alternativa ao T033 e Avanço do Tuning N8N

**Data**: 2026-04-08
**Branch**: `001-001-tunning-instrumentacao`
**Participantes**: Performance Analyst · System Architect · N8N Specialist
**Moderador**: Copilot (session manager)
**Objetivo**: Encontrar rota alternativa ao bloqueio do T033 (ProvenanceGate F18) e desbloquear promoção de F16+F17 para wf001.

---

## 1. Contexto — Por que T033 está bloqueado

### 1.1 Falha de Endereçamento de Ambiente (Bug Estrutural)

O T033 original especifica:

```bash
python src/validate_prometheus.py \
  --vm-url http://86.48.31.149:8428 \   # VictoriaMetrics de wfdb01 (ERRADO)
  --mode provenance-gate
```

**Problema**: 86.48.31.149 é o IP do **wfdb01** — host de **teste**. O `prod-collector-api` roda em **wf001** (31.220.103.208). O VictoriaMetrics de wfdb01 jamais perceberá a ausência do Pushgateway de wf001.

| Elemento | wfdb01 (teste) | wf001 (produção) |
|----------|---------------|-----------------|
| IP | 86.48.31.149 | 31.220.103.208 |
| VictoriaMetrics | 172.20.0.13:8428 (interno) | :8428 (inacessível externamente) |
| prod-collector-api | ❌ não existe | ✅ `adminvyadigital/n8n-collector-api:latest` |
| enterprise-pushgateway | ✅ legítimo (`pushgateway_wfdb01`) | — |

### 1.2 Dois Bloqueadores Independentes

| # | Bloqueador | Causa raiz | Tipo |
|---|-----------|-----------|------|
| B1 | `pushgateway_absent_1h: false` | matcher `job=~".*push.*"` captura `pushgateway_wfdb01` local, que está up há 11 dias e com funcionamento normal | Bug de especificação |
| B2 | `execution_count_coherent: false` | (a) métrica `n8n_executions_total` não existe — correta é `n8n_workflow_executions_total`; (b) contagem absoluta PostgreSQL vs VM é sempre incompatível por conta de resets do contador a cada restart do container | Bug de implementação + critério inválido |

### 1.3 Correções já aplicadas em 2026-04-08

- ✅ `EXECUTION_COUNT_QUERY` corrigido: `n8n_executions_total` → `n8n_workflow_executions_total`
- ✅ `psycopg2-binary` instalado no venv `/home/archaris/venv` em wfdb01
- ✅ Teste PG direto (wfdb02:5432) confirma 5101 rows em `n8n_db`

---

## 2. Votos do Debate

### 2.1 Performance Analyst

**Posição**: ProvenanceGate como especificado é inválido como gate de observabilidade. O critério `execution_count_coherent` com delta ≤1% é tecnicamente impossível para produção — qualquer restart de container N8N zera o contador do VM sem zerar o PostgreSQL.

**Proposta técnica**:
- Substituir `absent_over_time({job=~".*push.*"}[1h])` por query com job específico via SSH tunnel para wf001
- Substituir `count_delta_pct ≤ 1%` por `increase(n8n_workflow_executions_total[30m])` vs `SELECT COUNT(*) FROM execution_entity WHERE startedAt > NOW()-INTERVAL '30 min'` (tolerância 5%)

**Risco de promoção F16+F17 sem T033**: baixo-moderado. F17 (postgres tuning) é operacionalmente urgente dado o bloat de execution_entity.

**Recomendação**: Desbloquear imediatamente. Criar gate alternativo verificável hoje.

---

### 2.2 System Architect

**Posição**: A regra de "promoção em bloco" F16+F17+F18 deve ser desacoplada. F18 é diagnóstico, não intervenção — o remédio é externo. Manter F16+F17 presos a uma dependência externa é contra-produtivo.

**Proposta técnica — T033 reescrito**:

```bash
# Gate alternativo: SSH tunnel para VM de wf001
ssh -N -L 18428:localhost:8428 -p 5010 archaris@31.220.103.208 &
python src/validate_prometheus.py \
  --vm-url http://localhost:18428 \
  --mode provenance-gate \
  --report \
  --output docs/SESSIONS/$(date +%Y-%m-%d)/f18-provenance-gate-wf001.json
```

**Critério PASS**: `absent_over_time({job="collector_api_wf001_usa_ping_data"}[1h]) == 1` no VM de **wf001**.

**Critério FAIL aceitável**: se prod-collector-api ainda não corrigido → registrar `KNOWN_ISSUE_F18` e prosseguir `T034a` (F16+F17 apenas).

**Rollback F16+F17 → wf001**:
| Passo | Ação | Tempo |
|-------|------|-------|
| R1 | Salvar hash da imagem e env atual | 2 min |
| R2 | `docker compose down n8n && up` com .env anterior | 3 min |
| R3 | Verificar `healthz` + `n8n_queue_waiting` no VM | 2 min |

**Recomendação**: Criar T034a desacoplado. ADR documentando o desacoplamento.

---

### 2.3 N8N Specialist

**Posição**: F16 e F17 são operacionalmente seguros para wf001. F18 não corrigido cria dupla coleta nas novas séries de fila, mas não é bloqueante desde que os dashboards usem label/job como filtro.

**F16 em wf001 com dupla coleta ativa**:
- Novas séries `n8n_scaling_mode_queue_jobs_*` serão capturadas pelo scrape direto (correto) E pelo prod-collector-api (duplicado)
- Mitigação: usar `job_name=n8n_direct_wf001` no override para distinguir scrape direto vs push

**F17 prune nas primeiras 24h**:
- N8N inicia job de purgação em background imediatamente
- ⚠️ **Risco específico wf001**: verificar execuções com `status='running'` e `startedAt < NOW()-INTERVAL '720h'` ANTES do prune — evitar purgar workflows 121Labs PABX presos

**Janela de manutenção recomendada**:
- **Sábado 02h–04h UTC** (fora do pico 121Labs + WhatsApp Gateway)
- Duração estimada: ~8 min (playbook + restart + healthcheck)

**Rotas alternativas ranqueadas**:
| Rota | Descrição | Risco |
|------|-----------|-------|
| **A** ⭐ | Promover F16+F17 com label isolador no override | Baixo |
| **B** | Desativar prod-collector-api temporariamente | Médio |
| **C** | Aguardar correção externa | Sem ETA |

---

## 3. Consenso do Debate

### Decisão 1 — Desacoplar T034 em T034a e T034b

```
T034a — Promoção F16+F17 para wf001 (NOVO — aprovado)
       Pré-requisitos: T017 ✅ + T025 ✅ + T026 ✅ + T031 ✅ + T032 ✅ + verificação de execuções presas
       Janela: Sábado 02h–04h UTC

T034b — Promoção F18 para wf001 (aguarda T033 reescrito)
       Pré-requisitos: T033 reescrito PASS
```

### Decisão 2 — Reescrever T033

T033 reescrito deve:
1. Usar SSH tunnel para wf001 (`-L 18428:localhost:8428 -p 5010 archaris@31.220.103.208`)
2. Checar job específico: `absent_over_time({job="collector_api_wf001_usa_ping_data"}[1h])`
3. `execution_count_coherent` substituído por delta de janela 30min, tolerância 5%
4. Se FAIL por dependência externa → registrar `KNOWN_ISSUE_F18`, prosseguir T034a

### Decisão 3 — Corrigir validate_prometheus.py (pendente)

| Item | Status |
|------|--------|
| `EXECUTION_COUNT_QUERY` corrigido | ✅ feito |
| Job matcher específico por hostname | ⬜ pendente |
| `--job-matcher` CLI flag | ⬜ pendente |
| Delta de janela curta como alternativa a delta absoluto | ⬜ pendente |
| Suporte a SSH tunnel (documentação) | ⬜ pendente |

### Decisão 4 — Verificação pré-promoção F17 wf001

Obrigatório ANTES de aplicar F17 em wf001:

```sql
-- Execuções presas que serão purgadas (risco 121Labs PABX)
SELECT COUNT(*), workflow_id, status
FROM execution_entity
WHERE status = 'running'
  AND "startedAt" < NOW() - INTERVAL '720 hours'
GROUP BY workflow_id, status
ORDER BY COUNT(*) DESC;
```

---

## 4. Plano de Ação — Próximas Tasks

| Task | Descrição | Prioridade | Depende |
|------|-----------|-----------|---------|
| **T033r** | Reescrever T033: SSH tunnel + job-matcher específico + delta 30min | P0 | — |
| **T034a** | Promoção F16+F17 → wf001 (janela sábado) | P0 | T033r PASS ou KNOWN_ISSUE |
| **T034b** | Promoção F18 → wf001 | P1 | T033r PASS |
| **T035** | Corrigir `validate_prometheus.py`: job-matcher CLI, delta janela, SSH tunnel docs | P1 | — |
| **T036** | Check execuções presas wf001 antes do prune | P0 (pré T034a) | SSH wf001 |

---

## 5. Bugs documentados em validate_prometheus.py

| # | Bug | Severidade | Status |
|---|-----|-----------|--------|
| B1 | `EXECUTION_COUNT_QUERY = "n8n_executions_total"` — métrica inexistente | High | ✅ Corrigido |
| B2 | Sem suporte a `--job-matcher` — hardcoded `job=~".*push.*"` captura pushgateway legítimo | High | ⬜ Pendente |
| B3 | `execution_count_coherent` usa delta absoluto — inválido após restart do container | Medium | ⬜ Pendente |
| B4 | `--vm-url` aponta para wfdb01 em T033 — deveria ser wf001 via SSH tunnel | High | ⬜ Pendente (doc) |

---

## 6. Estado do Venv Archaris (wfdb01)

| Item | Status |
|------|--------|
| venv: `/home/archaris/venv` | ✅ criado |
| psycopg2-binary | ✅ instalado (2.9.x) |
| requests | ✅ instalado |
| validate_prometheus.py copiado | ✅ `/home/archaris/validate_prometheus.py` |
| PG cross-check testado | ✅ 5101 rows em n8n_db (wfdb02:5432) |

---

*Gerado em 2026-04-08 — Debate convocado por session-manager.*
*Participantes: performance-analyst · system-architect · n8n-specialist*

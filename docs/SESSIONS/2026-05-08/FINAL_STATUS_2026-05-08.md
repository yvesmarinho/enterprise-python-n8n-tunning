# 📊 Final Status — 2026-05-08

**Branch**: `001-001-tunning-instrumentacao`
**Sessão**: 2026-05-08 ~10:00 BRT → ~13:45 BRT
**Git HEAD ao encerrar**: ver `git log --oneline -1`

---

## IMPs Concluídos Esta Sessão

- ✅ **F16 revisado** — kbudde/rabbitmq-exporter v0.29.0 deployado e validado em wfdb01

---

## Estado Geral dos IMPs

| IMP | Título | Status |
|-----|--------|--------|
| F16 | Queue metrics (RabbitMQ Exporter) | ✅ Homologado em wfdb01 — pendente wf001 |
| F17 | PostgreSQL tuning (purgação execution_entity) | ✅ Homologado em wfdb01 — pendente T034a |
| F18 | Dual collection audit (ProvenanceGate) | 🔴 Bloqueado (prod-collector-api) |
| F19 | Upgrade incremental N8N | 🔵 Pendente (depende P1+P2 estável) |
| F20 | Probe sintético | 🔵 Pendente |
| T034a | Promoção F16+F17 para wf001 | 📅 Agendado 2026-05-10 02h-04h UTC |

---

## Próximas Ações (P0 para próxima sessão)

1. **⚠️ URGENTE — 256 execuções stuck em `waiting`** (hub-whatsapp-api-gateway-evolution-api)
   - Verificar se webhook de retorno está configurado
   - Considerar `EXECUTIONS_TIMEOUT` para evitar acúmulo
2. **🔥 Prometheus DOWN para wf001** — zero coleta de métricas N8N
   - Fix rápido: `ufw insert 1 allow from 86.48.31.149 to any port 5678` em wf001
3. **📅 T034a janela de manutenção 2026-05-10 02h-04h UTC**
   - Notificar stakeholders (121Labs PABX, WhatsApp Gateway) — deadline: 2026-05-09 02h UTC
   - Obter aprovação project-manager — deadline: 2026-05-09 02h UTC
   - Dry-run final 24h antes
4. **Incluir F16 revisado na promoção T034a** — playbook `f16-rabbitmq-exporter.yml` pronto

---

## Decisões Técnicas desta Sessão

| ID | Decisão | Justificativa |
|----|---------|---------------|
| D-20260508-01 | F16 migrado de Bull/Redis para kbudde/rabbitmq-exporter | N8N usa N8N_QUEUE_MODE=rabbitmq; Bull metrics endpoint removido |
| D-20260508-02 | Usuário RabbitMQ dedicado `dialer` com tag `monitoring` | Não usar credentials de admin para scraping; princípio least-privilege |
| D-20260508-03 | `ANSIBLE_CONFIG=ansible/ansible.cfg` obrigatório | `/etc/ansible/ansible.cfg` aponta para chave SSH inexistente `/etc/ansible/keys/archaris_key` |

---

## Contexto para Recuperação

### Infraestrutura wfdb01 — Estado após sessão
- **rabbitmq-exporter**: container UP em `/opt/docker_user/rabbitmq/`, porta 9419
- **Usuário RabbitMQ**: `dialer` com tag `monitoring` criado em wfdb01 (não existe em wf001!)
- **prometheus.yaml**: scrape job `rabbitmq-exporter` adicionado, Prometheus recarregado
- **Arquivo de vars**: `scripts/tmp/rabbitmq-exporter-vars.yml` — senha do user dialer (gitignored)

### Para replicar em wf001 (janela T034a)
```bash
ANSIBLE_CONFIG=ansible/ansible.cfg ansible-playbook \
  ansible/playbooks/f16-rabbitmq-exporter.yml \
  -i ansible/inventory/ \
  -e @scripts/tmp/rabbitmq-exporter-vars.yml \
  --limit wf001
```
> ⚠️ Atenção: wf001 usa RabbitMQ em `/opt/docker_user/rabbitmq/` — confirmar path antes

### SSH SPA
```bash
fwknop --rc-file ~/.fwknoprc -n wfdb01 && sleep 4 && \
  ssh -p 5010 -i ~/.ssh/id_rsa -o StrictHostKeyChecking=no archaris@86.48.31.149
```

### Comando Ansible sempre usar:
```bash
ANSIBLE_CONFIG=ansible/ansible.cfg ansible-playbook ...
```

---

## Riscos / Bloqueios

| Risco | Impacto | Mitigação |
|-------|---------|-----------|
| 256 execuções stuck | Saturação de DB + memória | Configurar EXECUTIONS_TIMEOUT |
| Prometheus sem métricas N8N | Gap de observabilidade total | UFW rule urgente em wf001 |
| T034a sem notificação de stakeholders | Falha de processo / interrupção não autorizada | Notificar antes de 2026-05-09 02h UTC |
| F18 bloqueado sem ETA | Sem correção de dupla coleta | Escalar para prod-collector-api team |

---

*Gerado em 2026-05-08 ao encerrar sessão — próxima sessão: preparação T034a*

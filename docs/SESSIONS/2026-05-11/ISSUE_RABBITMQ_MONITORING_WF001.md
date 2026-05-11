# Issue: Adicionar RabbitMQ Exporter ao Monitoramento wf001

**Projeto**: enterprise-observability
**Repositório**: git@github.com:admin-vya-digital/enterprise-observability.git
**Tipo**: Feature Request
**Prioridade**: P1 — Alta (dependência de F16)
**Labels**: monitoring, rabbitmq, prometheus, wf001

---

## 📋 Contexto

O servidor **wf001.vya.digital** (31.220.103.208) hospeda o N8N em produção com fila RabbitMQ (`N8N_QUEUE_MODE=rabbitmq`). Atualmente, **não há coleta de métricas de fila RabbitMQ** no stack de observabilidade.

**Projeto relacionado**: `enterprise-python-n8n-tunning` — Feature F16 (Queue Metrics)

---

## 🎯 Objetivo

Adicionar **kbudde/rabbitmq-exporter** ao monitoramento de wf001 para expor métricas de fila RabbitMQ no Prometheus/VictoriaMetrics.

---

## 📊 Justificativa

### Problema Atual

- **Gap crítico de observabilidade**: Hipótese de "fila saturada" identificada no relatório ANA-001 **não pode ser confirmada ou refutada** sem dados de fila
- **Workflows de alto volume**: 121Labs PABX (429K exec/90d, pico 8.4K/hora) podem saturar fila sem detecção
- **Zero visibilidade**: Sem métricas `rabbitmq_queue_*`, impossível criar alertas ou dashboards de fila

### Benefícios Esperados

- ✅ Métricas `rabbitmq_queue_messages`, `rabbitmq_queue_consumers`, `rabbitmq_queue_messages_ready` visíveis no VictoriaMetrics
- ✅ Alertas de fila saturada (threshold: profundidade > N mensagens)
- ✅ Dashboards Grafana com profundidade de fila, taxa de consumo e latência
- ✅ Validação de hipóteses de performance (fila vs. execução)

---

## 🛠️ Solução Proposta

### 1. Deploy RabbitMQ Exporter em wf001

**Container**: kbudde/rabbitmq-exporter:v0.29.0 ou superior
**Porta**: 9419 (padrão do exporter)
**Path no servidor**: `/opt/docker_user/rabbitmq/` (ajustar conforme estrutura do enterprise-observability)

**Configuração mínima**:
```yaml
services:
  rabbitmq-exporter:
    image: kbudde/rabbitmq-exporter:v0.29.0
    container_name: rabbitmq-exporter
    restart: unless-stopped
    ports:
      - "9419:9419"
    environment:
      RABBIT_URL: "http://rabbitmq:15672"  # API management do RabbitMQ
      RABBIT_USER: "${RABBITMQ_MONITOR_USER}"
      RABBIT_PASSWORD: "${RABBITMQ_MONITOR_PASSWORD}"
      RABBIT_CAPABILITIES: "bert,no_sort"
      PUBLISH_PORT: "9419"
    networks:
      - n8n_network  # Ou rede correspondente do RabbitMQ
```

### 2. Criar Usuário RabbitMQ Dedicado

**Motivo**: Princípio de least-privilege — não usar credenciais de admin para scraping

```bash
# Criar usuário 'dialer' com tag 'monitoring'
rabbitmqctl add_user dialer <senha_segura>
rabbitmqctl set_user_tags dialer monitoring
rabbitmqctl set_permissions -p / dialer "" "" ".*"
```

**Permissões**: read-only em todas as filas

### 3. Adicionar Scrape Job ao Prometheus

**Arquivo**: `prometheus.yml` (ou arquivo de configuração do enterprise-observability)

```yaml
scrape_configs:
  - job_name: 'rabbitmq-exporter'
    static_configs:
      - targets: ['wf001.vya.digital:9419']
    relabel_configs:
      - source_labels: [__address__]
        target_label: instance
        replacement: 'wf001'
```

### 4. Validação

**Queries para verificar**:
```promql
# Profundidade da fila
rabbitmq_queue_messages{instance="wf001"}

# Mensagens prontas para consumo
rabbitmq_queue_messages_ready{instance="wf001"}

# Consumidores ativos
rabbitmq_queue_consumers{instance="wf001"}

# Taxa de publicação
rate(rabbitmq_queue_messages_published_total{instance="wf001"}[5m])
```

**Critério de sucesso**: Todas as queries retornam dados válidos no VictoriaMetrics

---

## 📦 Artefatos de Referência

**Implementação de referência** (wfdb01 — ambiente de teste):
- Playbook Ansible: `enterprise-python-n8n-tunning/ansible/playbooks/f16-rabbitmq-exporter.yml`
- Role Ansible: `enterprise-python-n8n-tunning/ansible/roles/rabbitmq_exporter/`
- Decisão técnica: D-20260508-01 (Bull/Redis → RabbitMQ)

**Evidências em wfdb01**:
- ✅ Container UP em `/opt/docker_user/rabbitmq/`, porta 9419
- ✅ Usuário `dialer` com tag `monitoring` criado
- ✅ Métricas `rabbitmq_queue_*` confirmadas no Prometheus

---

## ⏱️ Estimativa

- **Deploy**: 20 minutos
- **Validação**: 10 minutos
- **Documentação**: 10 minutos
- **Total**: ~40 minutos

---

## 🚨 Impacto e Riscos

### Impacto

- **Baixo**: Exporter é read-only e não afeta RabbitMQ
- **Produção**: wf001 — requer janela de manutenção ou deploy sem downtime

### Riscos

- 🟡 **Credenciais expostas**: Mitigado por usuário dedicado com permissões mínimas
- 🟡 **Porta 9419 bloqueada**: Requer UFW rule se firewall ativo
- 🟢 **Rollback**: Remover container e scrape job (< 5 min)

---

## 📅 Dependências

- **Bloqueia**: T034a (promoção F16+F17 para wf001 — agendado 2026-05-17)
- **Depende de**: RabbitMQ ativo em wf001 (já existe — N8N_QUEUE_MODE=rabbitmq)

---

## 📝 Critérios de Aceite

- [ ] Container `rabbitmq-exporter` UP em wf001
- [ ] Usuário RabbitMQ `dialer` criado com tag `monitoring`
- [ ] Scrape job `rabbitmq-exporter` configurado no Prometheus
- [ ] Métricas `rabbitmq_queue_*` visíveis no VictoriaMetrics para instance=wf001
- [ ] Dashboard Grafana criado (opcional)
- [ ] Documentação atualizada em enterprise-observability

---

## 👥 Stakeholders

- **Solicitante**: enterprise-python-n8n-tunning (performance-analyst)
- **Owner**: enterprise-observability (devops-engineer)
- **Aprovador**: project-manager (dependência crítica T034a)

---

## 🔗 Referências

- ANA-001: Análise de Performance N8N (2026-01-01 a 2026-03-31)
- Feature F16: Habilitação de métricas de fila do N8N
- Debate Project Compliance: `enterprise-python-n8n-tunning/docs/SESSIONS/2026-05-11/DEBATE_PROJECT_COMPLIANCE_2026-05-11.md`

---

*Issue gerada em 2026-05-11 pelo projeto enterprise-python-n8n-tunning*
*Contato: performance-analyst | devops-engineer*

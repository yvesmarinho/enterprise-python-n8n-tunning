# 🐳 Docker Compose — Exporters para Monitoramento

**Gerado em**: 2026-05-14T10:30:00Z
**Revisado em**: 2026-05-14T10:35:00Z — Correção: Node Exporter já existe nos servidores
**Objetivo**: Snippets prontos para adicionar exporters ao docker-compose.yaml
**Contexto**: T034a — F16 Queue Metrics + Issues #1 e #2

---

## ⚠️ IMPORTANTE: Node Exporter JÁ EXISTE

**Todos os servidores (wf001, wfdb01, wfdb02) já possuem node-exporter instalado como serviço systemd na porta 9100.**

**NÃO adicione node-exporter ao docker-compose.yaml** — isso causaria conflito de porta.

---

## 📋 Índice

1. [Node Exporter (Validação)](#1-node-exporter-validação) — ✅ JÁ EXISTE nos servidores
2. [RabbitMQ Exporter](#2-rabbitmq-exporter) — ⚠️ ADICIONAR ao docker-compose (issue #1)
3. [Redis Exporter](#3-redis-exporter) — ⚠️ ADICIONAR ao docker-compose (opcional)

---

## 1. Node Exporter (Validação)

**Status**: ✅ **JÁ EXISTE** como serviço systemd em todos os servidores
**Função**: Coletar métricas de sistema (CPU, memória, disco, rede)
**Porta**: 9100
**Servidor**: wf001, wfdb01, wfdb02

### ⚠️ NÃO Adicionar ao Docker Compose

**Node Exporter JÁ está rodando como serviço systemd nos servidores.**

Adicionar ao docker-compose.yaml causaria **conflito de porta 9100**.

### ✅ Validar Node Exporter Existente

```bash
# Verificar se node-exporter está rodando (systemd)
systemctl status node_exporter

# OU verificar se está rodando (qualquer método)
sudo netstat -tlnp | grep :9100
# OU
sudo ss -tlnp | grep :9100

# Testar endpoint
curl -s http://localhost:9100/metrics | head -20

# Verificar métricas de memória (issue #2)
curl -s http://localhost:9100/metrics | grep node_memory_MemAvailable_bytes

# Se retornar valor → node-exporter OK
# Se retornar vazio → problema de coleta (diagnosticar)
```

### 📋 Se Node Exporter NÃO Existir (improvável)

**Apenas se o comando acima retornar que o serviço NÃO existe:**

```bash
# Instalar via apt (Debian/Ubuntu)
sudo apt update
sudo apt install prometheus-node-exporter -y

# Verificar se iniciou
systemctl status prometheus-node-exporter

# Habilitar no boot
sudo systemctl enable prometheus-node-exporter

# Testar
curl -s http://localhost:9100/metrics | head -10
```

### 🔍 Diagnóstico Issue #2 (Memory Metrics Vazias)

**Problema**: Métricas `node_memory_*{instance="wf001"}` retornam vazias no Prometheus

**Causa provável**: Label `instance` incorreto no relabeling do Prometheus

**Validação local** (executar em wf001):
```bash
# Verificar se node-exporter expõe métricas de memória LOCALMENTE
curl -s http://localhost:9100/metrics | grep -E "node_memory_(MemAvailable|MemTotal)_bytes"

# Resultado esperado (exemplo):
# node_memory_MemAvailable_bytes 8234567890
# node_memory_MemTotal_bytes 16000000000
```

**Se métricas aparecem localmente mas NÃO no Prometheus** → problema é no scrape config do Prometheus (issue #2)

### Scrape Config Prometheus

```yaml
scrape_configs:
  - job_name: 'node-exporter'
    static_configs:
      - targets:
          - 'wf001.vya.digital:9100'
          - 'wfdb01.vya.digital:9100'
          - 'wfdb02.vya.digital:9100'
    relabel_configs:
      - source_labels: [__address__]
        regex: '([^:]+):.*'
        target_label: instance
        replacement: '$1'
```

---

## 2. RabbitMQ Exporter

**Função**: Coletar métricas de fila RabbitMQ (profundidade, consumidores, taxa)
**Porta**: 9419
**Versão**: kbudde/rabbitmq-exporter:v0.29.0
**Servidor**: wf001 (onde N8N roda com RabbitMQ)
**Issue**: enterprise-observability #1

### Snippet Docker Compose

```yaml
  rabbitmq-exporter:
    image: kbudde/rabbitmq-exporter:v0.29.0
    container_name: rabbitmq-exporter
    restart: unless-stopped
    ports:
      - "9419:9419"
    environment:
      # URL da API de management do RabbitMQ (porta 15672)
      RABBIT_URL: "http://rabbitmq:15672"

      # Credenciais do usuário 'dialer' (criar antes)
      RABBIT_USER: "${RABBITMQ_MONITOR_USER:-dialer}"
      RABBIT_PASSWORD: "${RABBITMQ_MONITOR_PASSWORD}"

      # Capabilities (bert = binary protocol, no_sort = performance)
      RABBIT_CAPABILITIES: "bert,no_sort"

      # Porta do exporter
      PUBLISH_PORT: "9419"

      # Output format
      OUTPUT_FORMAT: "JSON"

      # Log level
      LOG_LEVEL: "info"

      # Include/exclude queues (opcional)
      # RABBIT_INCLUDE_QUEUES: ".*"
      # RABBIT_SKIP_QUEUES: "^amq.*"

      # Include vhost
      # RABBIT_INCLUDE_VHOST: "^/"

    networks:
      - n8n_network  # Mesma rede do RabbitMQ
    depends_on:
      - rabbitmq
```

### Variáveis de Ambiente (.env)

```bash
# Adicionar ao .env do docker-compose
RABBITMQ_MONITOR_USER=dialer
RABBITMQ_MONITOR_PASSWORD=senha_segura_aqui
```

### Pré-requisito: Criar Usuário 'dialer' no RabbitMQ

```bash
# Acessar container RabbitMQ
docker exec -it rabbitmq bash

# Criar usuário com tag 'monitoring' (read-only)
rabbitmqctl add_user dialer "senha_segura_aqui"
rabbitmqctl set_user_tags dialer monitoring
rabbitmqctl set_permissions -p / dialer "" "" ".*"

# Validar
rabbitmqctl list_users
# Esperado: dialer [monitoring]

# Sair do container
exit
```

### Validação

```bash
# Verificar se rabbitmq-exporter está UP
docker ps | grep rabbitmq-exporter

# Testar endpoint
curl -s http://localhost:9419/metrics | head -20

# Verificar métricas de fila
curl -s http://localhost:9419/metrics | grep rabbitmq_queue_messages
curl -s http://localhost:9419/metrics | grep rabbitmq_queue_consumers

# Métricas importantes
curl -s http://localhost:9419/metrics | grep -E "rabbitmq_queue_(messages|messages_ready|messages_unacknowledged|consumers)"
```

### Scrape Config Prometheus

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

### Métricas Principais Expostas

| Métrica | Descrição |
|---------|-----------|
| `rabbitmq_queue_messages` | Total de mensagens na fila |
| `rabbitmq_queue_messages_ready` | Mensagens prontas para consumo |
| `rabbitmq_queue_messages_unacknowledged` | Mensagens sendo processadas |
| `rabbitmq_queue_consumers` | Número de consumidores ativos |
| `rabbitmq_queue_messages_published_total` | Total de mensagens publicadas |
| `rabbitmq_queue_messages_delivered_total` | Total de mensagens entregues |
| `rabbitmq_queue_messages_ack_total` | Total de mensagens confirmadas |

---

## 3. Redis Exporter

**Função**: Coletar métricas de Redis (usado pelo N8N para Bull queue ou cache)
**Porta**: 9121
**Versão**: oliver006/redis_exporter:latest
**Servidor**: Onde Redis roda (normalmente mesmo servidor do N8N)

### Snippet Docker Compose

```yaml
  redis-exporter:
    image: oliver006/redis_exporter:v1.56.0
    container_name: redis-exporter
    restart: unless-stopped
    ports:
      - "9121:9121"
    environment:
      # URL de conexão ao Redis
      REDIS_ADDR: "redis:6379"

      # Senha do Redis (se configurada)
      # REDIS_PASSWORD: "${REDIS_PASSWORD}"

      # Namespace das métricas
      REDIS_EXPORTER_NAMESPACE: "redis"

      # Debug
      REDIS_EXPORTER_DEBUG: "false"

      # Check single keys (cuidado com performance)
      # REDIS_EXPORTER_CHECK_KEYS: "bull:*"

      # Log format
      REDIS_EXPORTER_LOG_FORMAT: "json"

    networks:
      - n8n_network  # Mesma rede do Redis
    depends_on:
      - redis
```

### Alternativa com Redis Protegido por Senha

```yaml
  redis-exporter:
    image: oliver006/redis_exporter:v1.56.0
    container_name: redis-exporter
    restart: unless-stopped
    ports:
      - "9121:9121"
    environment:
      REDIS_ADDR: "redis:6379"
      REDIS_PASSWORD: "${REDIS_PASSWORD}"
    networks:
      - n8n_network
    depends_on:
      - redis
```

### Alternativa com Múltiplas Instâncias Redis

```yaml
  redis-exporter:
    image: oliver006/redis_exporter:v1.56.0
    container_name: redis-exporter
    restart: unless-stopped
    ports:
      - "9121:9121"
    command:
      - '--redis.addr=redis://redis:6379'
      - '--redis.password=${REDIS_PASSWORD}'
    networks:
      - n8n_network
```

### Validação

```bash
# Verificar se redis-exporter está UP
docker ps | grep redis-exporter

# Testar endpoint
curl -s http://localhost:9121/metrics | head -20

# Verificar métricas principais
curl -s http://localhost:9121/metrics | grep redis_connected_clients
curl -s http://localhost:9121/metrics | grep redis_memory_used_bytes
curl -s http://localhost:9121/metrics | grep redis_commands_processed_total

# Métricas de Bull queue (se N8N usar Bull)
curl -s http://localhost:9121/metrics | grep -i bull
```

### Scrape Config Prometheus

```yaml
scrape_configs:
  - job_name: 'redis-exporter'
    static_configs:
      - targets: ['wf001.vya.digital:9121']
    relabel_configs:
      - source_labels: [__address__]
        target_label: instance
        replacement: 'wf001'
```

### Métricas Principais Expostas

| Métrica | Descrição |
|---------|-----------|
| `redis_connected_clients` | Clientes conectados |
| `redis_memory_used_bytes` | Memória usada pelo Redis |
| `redis_memory_max_bytes` | Memória máxima configurada |
| `redis_commands_processed_total` | Total de comandos processados |
| `redis_keyspace_hits_total` | Cache hits |
| `redis_keyspace_misses_total` | Cache misses |
| `redis_evicted_keys_total` | Keys evicted (LRU) |
| `redis_db_keys` | Total de keys por database |

---

## 📦 Exemplo Completo: docker-compose.yaml N8N + Exporters

**Nota**: Node Exporter NÃO incluído (já existe como serviço systemd)

```yaml
version: '3.8'

services:
  # N8N
  n8n:
    image: n8nio/n8n:2.19.5
    container_name: n8n
    restart: unless-stopped
    ports:
      - "5678:5678"
    environment:
      - N8N_HOST=${N8N_HOST}
      - N8N_PORT=5678
      - N8N_PROTOCOL=https
      - WEBHOOK_URL=${WEBHOOK_URL}
      - GENERIC_TIMEZONE=${GENERIC_TIMEZONE}
      - DB_TYPE=postgresdb
      - DB_POSTGRESDB_HOST=${DB_POSTGRESDB_HOST}
      - DB_POSTGRESDB_PORT=${DB_POSTGRESDB_PORT}
      - DB_POSTGRESDB_DATABASE=${DB_POSTGRESDB_DATABASE}
      - DB_POSTGRESDB_USER=${DB_POSTGRESDB_USER}
      - DB_POSTGRESDB_PASSWORD=${DB_POSTGRESDB_PASSWORD}
      - QUEUE_BULL_REDIS_HOST=redis
      - QUEUE_BULL_REDIS_PORT=6379
      - N8N_METRICS=true
      - N8N_METRICS_INCLUDE_QUEUE_METRICS=true  # F16
      - EXECUTIONS_DATA_PRUNE=true  # F17
      - EXECUTIONS_DATA_MAX_AGE=168  # F17 (7 dias)
    volumes:
      - n8n_data:/home/node/.n8n
    networks:
      - n8n_network
    depends_on:
      - redis

  # Redis (para Bull queue)
  redis:
    image: redis:7-alpine
    container_name: redis
    restart: unless-stopped
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - n8n_network

  # RabbitMQ (alternativa ao Bull)
  rabbitmq:
    image: rabbitmq:3-management-alpine
    container_name: rabbitmq
    restart: unless-stopped
    ports:
      - "5672:5672"   # AMQP
      - "15672:15672" # Management UI
    environment:
      RABBITMQ_DEFAULT_USER: ${RABBITMQ_USER}
      RABBITMQ_DEFAULT_PASS: ${RABBITMQ_PASS}
    volumes:
      - rabbitmq_data:/var/lib/rabbitmq
    networks:
      - n8n_network

  # ====================
  # EXPORTERS (APENAS RabbitMQ e Redis)
  # ====================
  # ⚠️ Node Exporter NÃO incluído — já existe como serviço systemd

  # RabbitMQ Exporter (métricas de fila) — ISSUE #1
  rabbitmq-exporter:
    image: kbudde/rabbitmq-exporter:v0.29.0
    container_name: rabbitmq-exporter
    restart: unless-stopped
    ports:
      - "9419:9419"
    environment:
      RABBIT_URL: "http://rabbitmq:15672"
      RABBIT_USER: "${RABBITMQ_MONITOR_USER:-dialer}"
      RABBIT_PASSWORD: "${RABBITMQ_MONITOR_PASSWORD}"
      RABBIT_CAPABILITIES: "bert,no_sort"
      PUBLISH_PORT: "9419"
      OUTPUT_FORMAT: "JSON"
      LOG_LEVEL: "info"
    networks:
      - n8n_network
    depends_on:
      - rabbitmq

  # Redis Exporter (métricas de cache/queue) — OPCIONAL
  redis-exporter:
    image: oliver006/redis_exporter:v1.56.0
    container_name: redis-exporter
    restart: unless-stopped
    ports:
      - "9121:9121"
    environment:
      REDIS_ADDR: "redis:6379"
      REDIS_EXPORTER_NAMESPACE: "redis"
      REDIS_EXPORTER_LOG_FORMAT: "json"
    networks:
      - n8n_network
    depends_on:
      - redis

networks:
  n8n_network:
    driver: bridge

volumes:
  n8n_data:
  redis_data:
  rabbitmq_data:
```

---

## 🔒 Segurança — UFW Rules

### Liberar Portas dos Exporters (Prometheus → Servidor)

```bash
# Node Exporter (9100)
sudo ufw insert 1 allow from 86.48.31.149 to any port 9100 comment "Prometheus → node-exporter"

# RabbitMQ Exporter (9419)
sudo ufw insert 1 allow from 86.48.31.149 to any port 9419 comment "Prometheus → rabbitmq-exporter"

# Redis Exporter (9121)
sudo ufw insert 1 allow from 86.48.31.149 to any port 9121 comment "Prometheus → redis-exporter"

# Verificar rules
sudo ufw status numbered
```

**Nota**: `86.48.31.149` = wfdb01 (onde Prometheus roda)

---

## 📊 Prometheus — Scrape Config Consolidado

```yaml
# /opt/prometheus/prometheus.yml
scrape_configs:
  # N8N Metrics
  - job_name: 'n8n'
    static_configs:
      - targets: ['wf001.vya.digital:5678']
    metrics_path: '/metrics'
    relabel_configs:
      - source_labels: [__address__]
        target_label: instance
        replacement: 'wf001'

  # Node Exporter (sistema)
  - job_name: 'node-exporter'
    static_configs:
      - targets:
          - 'wf001.vya.digital:9100'
          - 'wfdb01.vya.digital:9100'
          - 'wfdb02.vya.digital:9100'
    relabel_configs:
      - source_labels: [__address__]
        regex: '([^:]+):.*'
        target_label: instance
        replacement: '$1'

  # RabbitMQ Exporter (fila)
  - job_name: 'rabbitmq-exporter'
    static_configs:
      - targets: ['wf001.vya.digital:9419']
    relabel_configs:
      - source_labels: [__address__]
        target_label: instance
        replacement: 'wf001'

  # Redis Exporter (cache)
  - job_name: 'redis-exporter'
    static_configs:
      - targets: ['wf001.vya.digital:9121']
    relabel_configs:
      - source_labels: [__address__]
        target_label: instance
        replacement: 'wf001'
```

**Reload Prometheus após mudança**:
```bash
# Se systemd
sudo systemctl reload prometheus

# Se Docker
docker compose restart prometheus

# Validar targets
curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | {job, instance, health}'
```

---

## ✅ Checklist de Deploy

### wf001 (Produção)

**Pré-validação**:
- [ ] Validar node-exporter systemd OK: `systemctl status node_exporter`
- [ ] Validar node-exporter métricas locais: `curl localhost:9100/metrics | grep node_memory`

**Deploy Exporters Docker**:
- [ ] Criar usuário 'dialer' no RabbitMQ (issue #1)
- [ ] Adicionar RabbitMQ exporter ao docker-compose.yaml
- [ ] Adicionar Redis exporter ao docker-compose.yaml (opcional)
- [ ] Configurar variáveis de ambiente (.env): `RABBITMQ_MONITOR_USER`, `RABBITMQ_MONITOR_PASSWORD`
- [ ] `docker compose up -d` (deploy dos exporters)
- [ ] Validar endpoints Docker: `curl localhost:9419/metrics` (RabbitMQ), `curl localhost:9121/metrics` (Redis)
- [ ] Configurar UFW rules para Prometheus (9419, 9121)
- [ ] Adicionar targets ao Prometheus (apenas RabbitMQ e Redis)
- [ ] Reload Prometheus
- [ ] Validar targets UP no Prometheus UI

**Diagnóstico Issue #2 (Memory)**:
- [ ] Confirmar métricas locais OK: `curl localhost:9100/metrics | grep node_memory_MemAvailable_bytes`
- [ ] Verificar scrape config Prometheus para wf001 (relabeling)
- [ ] Testar query no Prometheus: `node_memory_MemAvailable_bytes{instance="wf001"}`

### wfdb01 (Observabilidade)

- [ ] Validar node-exporter systemd OK: `systemctl status node_exporter`
- [ ] Validar endpoint 9100: `curl localhost:9100/metrics | head`
- [ ] Adicionar scrape configs ao prometheus.yml (RabbitMQ + Redis de wf001)
- [ ] Reload Prometheus: `systemctl reload prometheus`
- [ ] Validar targets UP: Prometheus UI → Status → Targets

### wfdb02 (Database)

- [ ] Validar node-exporter systemd OK: `systemctl status node_exporter`
- [ ] Validar endpoint 9100: `curl localhost:9100/metrics | head`
- [ ] Nenhuma mudança necessária no wfdb02 (não roda RabbitMQ/Redis)

---

## 🎯 Queries de Validação Pós-Deploy

```promql
# Node Exporter — Memória disponível wf001 (JÁ EXISTE)
node_memory_MemAvailable_bytes{instance="wf001"}

# Node Exporter — Todos os servidores UP
up{job="node-exporter"}

# RabbitMQ — Profundidade de fila (NOVO — issue #1)
rabbitmq_queue_messages{instance="wf001"}

# RabbitMQ — Consumidores ativos
rabbitmq_queue_consumers{instance="wf001"}

# Redis — Clientes conectados (NOVO — opcional)
redis_connected_clients{instance="wf001"}

# Todos os targets UP
up{job=~"node-exporter|rabbitmq-exporter|redis-exporter"}
```

---

## 📝 Resumo de Mudanças

| Exporter | Status Anterior | Status Corrigido | Ação |
|----------|----------------|------------------|------|
| Node Exporter | ❌ Adicionar via Docker | ✅ JÁ EXISTE (systemd) | **Apenas validar** |
| RabbitMQ Exporter | ⚠️ Adicionar | ⚠️ Adicionar | **Adicionar ao docker-compose** (issue #1) |
| Redis Exporter | ⚠️ Adicionar | ⚠️ Adicionar (opcional) | **Adicionar ao docker-compose** |

---

## 🔍 Validação Rápida — Executar HOJE em wf001

```bash
# 1. Verificar node-exporter (deve existir)
systemctl status node_exporter
curl -s http://localhost:9100/metrics | grep node_memory_MemAvailable_bytes

# 2. Verificar se RabbitMQ exporter JÁ existe (não deve)
curl -s http://localhost:9419/metrics
# Esperado: Connection refused (OK — não existe)

# 3. Verificar se Redis exporter JÁ existe (não deve)
curl -s http://localhost:9121/metrics
# Esperado: Connection refused (OK — não existe)
```

**Se node-exporter retornar métricas localmente mas NÃO no Prometheus** → issue #2 confirmada (problema de scrape config)

---

**Gerado por**: GitHub Copilot (devops-engineer mode)
**Contexto**: T034a F16 Queue Metrics + Issues #1 e #2
**Sessão**: 2026-05-14
**Revisão**: Correção de conflito de porta node-exporter

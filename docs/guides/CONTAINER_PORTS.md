# 🐳 Mapeamento de Portas dos Containers Docker

**Servidor:** wfdb01.vya.digital  
**Data de Coleta:** 2026-05-05 12:04:48  
**Total de Containers:** 39  
**Containers Rodando:** 37

> Verificacao de consistencia (2026-05-20): este arquivo e um snapshot importado de outro projeto e deve ser tratado como historico de coleta. Para operacao atual, usar tambem `config/prometheus.yaml` e `docs/general/SERVERS_IP_PORTS_INVENTORY.md`.
>
> Nota: linhas de portas repetidas podem ocorrer por exportacao original (IPv4/IPv6) e nao representam servicos duplicados.

---

## 📋 Índice

- [📊 Monitoramento](#monitoring): 16 containers
- [🔀 Reverse Proxy / Load Balancer](#reverseproxy): 2 containers
- [🗄️ Bancos de Dados](#database): 2 containers
- [📨 Filas de Mensagens](#messagequeue): 1 containers
- [🤖 Automação](#automation): 4 containers
- [💬 Comunicação](#communication): 5 containers
- [🌐 Rede](#network): 1 containers
- [⚙️ Gerenciamento](#management): 2 containers
- [📱 Aplicações](#application): 6 containers

---

## 📊 Monitoramento

### ✅ enterprise-alertmanager

**Imagem:** `prom/alertmanager:v0.28.1`  
**Status:** Up About an hour  
**Portas:**

| Tipo | Porta Externa | Porta Interna | Protocolo | Uso |
|------|---------------|---------------|-----------|-----|
| 🌐 Exposta | `9093` | `9093` | tcp | Alertmanager UI |
| 🌐 Exposta | `9093` | `9093` | tcp | Alertmanager UI |

### ✅ enterprise-cadvisor

**Imagem:** `gcr.io/cadvisor/cadvisor:v0.47.0`  
**Status:** Up About an hour (healthy)  
**Portas:**

| Tipo | Porta Externa | Porta Interna | Protocolo | Uso |
|------|---------------|---------------|-----------|-----|
| 🌐 Exposta | `8080` | `8080` | tcp | cAdvisor/HTTP |
| 🌐 Exposta | `8080` | `8080` | tcp | cAdvisor/HTTP |

### ✅ enterprise-grafana

**Imagem:** `grafana/grafana:11.6.0`  
**Status:** Up About an hour  
**Portas:**

| Tipo | Porta Externa | Porta Interna | Protocolo | Uso |
|------|---------------|---------------|-----------|-----|
| 🌐 Exposta | `3002` | `3000` | tcp | Grafana UI |
| 🌐 Exposta | `3002` | `3000` | tcp | Grafana UI |

### ✅ enterprise-node-exporter-host

**Imagem:** `prom/node-exporter:v1.8.2`  
**Status:** Up About an hour  
**Portas:** Nenhuma porta mapeada (pode usar host network)

### ❌ enterprise-observability-init-1

**Imagem:** `grafana/loki:3.5.3`  
**Status:** Exited (0) About an hour ago  
**Portas:** Nenhuma porta mapeada (pode usar host network)

### ✅ enterprise-observability-loki-backend-1

**Imagem:** `grafana/loki:3.5.3`  
**Status:** Up About an hour  
**Portas:**

| Tipo | Porta Externa | Porta Interna | Protocolo | Uso |
|------|---------------|---------------|-----------|-----|
| 🔒 Interna | - | `3100` | tcp | Loki |

### ✅ enterprise-observability-loki-backend-2

**Imagem:** `grafana/loki:3.5.3`  
**Status:** Up About an hour  
**Portas:**

| Tipo | Porta Externa | Porta Interna | Protocolo | Uso |
|------|---------------|---------------|-----------|-----|
| 🔒 Interna | - | `3100` | tcp | Loki |

### ✅ enterprise-observability-loki-read-1

**Imagem:** `grafana/loki:3.5.3`  
**Status:** Up About an hour (healthy)  
**Portas:**

| Tipo | Porta Externa | Porta Interna | Protocolo | Uso |
|------|---------------|---------------|-----------|-----|
| 🔒 Interna | - | `3100` | tcp | Loki |

### ✅ enterprise-observability-loki-read-2

**Imagem:** `grafana/loki:3.5.3`  
**Status:** Up About an hour (healthy)  
**Portas:**

| Tipo | Porta Externa | Porta Interna | Protocolo | Uso |
|------|---------------|---------------|-----------|-----|
| 🔒 Interna | - | `3100` | tcp | Loki |

### ✅ enterprise-observability-loki-write-1

**Imagem:** `grafana/loki:3.5.3`  
**Status:** Up About an hour  
**Portas:**

| Tipo | Porta Externa | Porta Interna | Protocolo | Uso |
|------|---------------|---------------|-----------|-----|
| 🔒 Interna | - | `3100` | tcp | Loki |

### ✅ enterprise-observability-loki-write-2

**Imagem:** `grafana/loki:3.5.3`  
**Status:** Up About an hour  
**Portas:**

| Tipo | Porta Externa | Porta Interna | Protocolo | Uso |
|------|---------------|---------------|-----------|-----|
| 🔒 Interna | - | `3100` | tcp | Loki |

### ✅ enterprise-postgres-exporter

**Imagem:** `prometheuscommunity/postgres-exporter:v0.15.0`  
**Status:** Up About an hour  
**Portas:**

| Tipo | Porta Externa | Porta Interna | Protocolo | Uso |
|------|---------------|---------------|-----------|-----|
| 🔒 Interna | - | `9187` | tcp | PostgreSQL Exporter |

### ✅ enterprise-prometheus

**Imagem:** `prom/prometheus:v3.2.1`  
**Status:** Up About an hour  
**Portas:**

| Tipo | Porta Externa | Porta Interna | Protocolo | Uso |
|------|---------------|---------------|-----------|-----|
| 🌐 Exposta | `9091` | `9090` | tcp | Prometheus UI/API |
| 🌐 Exposta | `9091` | `9090` | tcp | Prometheus UI/API |

### ✅ enterprise-promtail

**Imagem:** `grafana/promtail:3.5.3`  
**Status:** Up About an hour  
**Portas:** Nenhuma porta mapeada (pode usar host network)

### ✅ enterprise-pushgateway

**Imagem:** `prom/pushgateway:v1.6.2`  
**Status:** Up About an hour (healthy)  
**Portas:**

| Tipo | Porta Externa | Porta Interna | Protocolo | Uso |
|------|---------------|---------------|-----------|-----|
| 🔒 Interna | - | `9091` | tcp | Prometheus UI |

### ✅ enterprise-victoriametrics

**Imagem:** `victoriametrics/victoria-metrics:v1.97.1`  
**Status:** Up About an hour  
**Portas:**

| Tipo | Porta Externa | Porta Interna | Protocolo | Uso |
|------|---------------|---------------|-----------|-----|
| 🔒 Interna | - | `8428` | tcp | VictoriaMetrics |

---

## 🔀 Reverse Proxy / Load Balancer

### ✅ traefik

**Imagem:** `traefik:latest`  
**Status:** Up 4 weeks  
**Portas:**

| Tipo | Porta Externa | Porta Interna | Protocolo | Uso |
|------|---------------|---------------|-----------|-----|
| 🌐 Exposta | `80` | `80` | tcp | HTTP |
| 🌐 Exposta | `80` | `80` | tcp | HTTP |
| 🌐 Exposta | `443` | `443` | tcp | HTTPS |
| 🌐 Exposta | `443` | `443` | tcp | HTTPS |
| 🌐 Exposta | `9090` | `9090` | tcp | Traefik Metrics |
| 🌐 Exposta | `9090` | `9090` | tcp | Traefik Metrics |

### ✅ traefik-wfdb01

**Imagem:** `traefik:v3`  
**Status:** Up 7 weeks (healthy)  
**Portas:**

| Tipo | Porta Externa | Porta Interna | Protocolo | Uso |
|------|---------------|---------------|-----------|-----|
| 🔒 Interna | - | `80` | tcp | HTTP |

---

## 🗄️ Bancos de Dados

### ✅ enterprise-postgres

**Imagem:** `postgres:16-alpine`  
**Status:** Up About an hour (healthy)  
**Portas:**

| Tipo | Porta Externa | Porta Interna | Protocolo | Uso |
|------|---------------|---------------|-----------|-----|
| 🔒 Interna | - | `5432` | tcp | PostgreSQL |

### ✅ redis

**Imagem:** `redis:alpine`  
**Status:** Up 7 weeks  
**Portas:**

| Tipo | Porta Externa | Porta Interna | Protocolo | Uso |
|------|---------------|---------------|-----------|-----|
| 🌐 Exposta | `6379` | `6379` | tcp | Redis |
| 🌐 Exposta | `6379` | `6379` | tcp | Redis |

---

## 📨 Filas de Mensagens

### ✅ rabbitmq

**Imagem:** `rabbitmq:3-management`  
**Status:** Up 7 weeks (healthy)  
**Portas:**

| Tipo | Porta Externa | Porta Interna | Protocolo | Uso |
|------|---------------|---------------|-----------|-----|
| 🔒 Interna | - | `4369` | tcp | - |
| 🔒 Interna | - | `5671` | tcp | - |
| 🔒 Interna | - | `15671` | tcp | - |
| 🔒 Interna | - | `15691-15692` | tcp | - |
| 🔒 Interna | - | `25672` | tcp | - |
| 🌐 Exposta | `5673` | `5672` | tcp | RabbitMQ AMQP (external) |
| 🌐 Exposta | `5673` | `5672` | tcp | RabbitMQ AMQP (external) |
| 🌐 Exposta | `15673` | `15672` | tcp | RabbitMQ Management (external) |
| 🌐 Exposta | `15673` | `15672` | tcp | RabbitMQ Management (external) |

---

## 🤖 Automação

### ✅ n8n-n8n_editor-1

**Imagem:** `n8nio/n8n:2.19.1`  
**Status:** Up 5 days  
**Portas:**

| Tipo | Porta Externa | Porta Interna | Protocolo | Uso |
|------|---------------|---------------|-----------|-----|
| 🔒 Interna | - | `5678` | tcp | n8n |

### ✅ n8n-n8n_mcp-1

**Imagem:** `n8nio/n8n:2.19.1`  
**Status:** Up 5 days  
**Portas:**

| Tipo | Porta Externa | Porta Interna | Protocolo | Uso |
|------|---------------|---------------|-----------|-----|
| 🔒 Interna | - | `5678` | tcp | n8n |

### ✅ n8n-n8n_webhook-1

**Imagem:** `n8nio/n8n:2.19.1`  
**Status:** Up 5 days  
**Portas:**

| Tipo | Porta Externa | Porta Interna | Protocolo | Uso |
|------|---------------|---------------|-----------|-----|
| 🔒 Interna | - | `5678` | tcp | n8n |

### ✅ n8n-n8n_worker-1

**Imagem:** `n8nio/n8n:2.19.1`  
**Status:** Up 5 days  
**Portas:**

| Tipo | Porta Externa | Porta Interna | Protocolo | Uso |
|------|---------------|---------------|-----------|-----|
| 🔒 Interna | - | `5678` | tcp | n8n |

---

## 💬 Comunicação

### ✅ chat-vya-digital

**Imagem:** `adminvyadigital/chatwoot:v3.12.71`  
**Status:** Up 6 days  
**Portas:**

| Tipo | Porta Externa | Porta Interna | Protocolo | Uso |
|------|---------------|---------------|-----------|-----|
| 🔒 Interna | - | `3000` | tcp | Grafana/Chatwoot UI |

### ✅ chat-vya-digital-sidekiq

**Imagem:** `adminvyadigital/chatwoot:v3.12.71`  
**Status:** Up 6 days  
**Portas:**

| Tipo | Porta Externa | Porta Interna | Protocolo | Uso |
|------|---------------|---------------|-----------|-----|
| 🔒 Interna | - | `3000` | tcp | Grafana/Chatwoot UI |

### ✅ chatSynesis

**Imagem:** `adminvyadigital/chatwoot:v3.12.7`  
**Status:** Up 7 weeks  
**Portas:**

| Tipo | Porta Externa | Porta Interna | Protocolo | Uso |
|------|---------------|---------------|-----------|-----|
| 🔒 Interna | - | `3000` | tcp | Grafana/Chatwoot UI |

### ✅ chatSynesisSidekiq

**Imagem:** `adminvyadigital/chatwoot:v3.12.7`  
**Status:** Up 7 weeks  
**Portas:**

| Tipo | Porta Externa | Porta Interna | Protocolo | Uso |
|------|---------------|---------------|-----------|-----|
| 🔒 Interna | - | `3000` | tcp | Grafana/Chatwoot UI |

### ❌ chatwoot-synesys-base-1

**Imagem:** `adminvyadigital/chatwoot:v3.12.7`  
**Status:** Restarting (0) 24 seconds ago  
**Portas:** Nenhuma porta mapeada (pode usar host network)

---

## 🌐 Rede

### ✅ cloudflared-wfdb01

**Imagem:** `cloudflare/cloudflared:latest`  
**Status:** Up 7 weeks (healthy)  
**Portas:** Nenhuma porta mapeada (pode usar host network)

---

## ⚙️ Gerenciamento

### ✅ dozzle

**Imagem:** `amir20/dozzle:latest`  
**Status:** Up 7 weeks  
**Portas:**

| Tipo | Porta Externa | Porta Interna | Protocolo | Uso |
|------|---------------|---------------|-----------|-----|
| 🌐 Exposta | `8081` | `8080` | tcp | Dozzle UI |
| 🌐 Exposta | `8081` | `8080` | tcp | Dozzle UI |

### ✅ portainer

**Imagem:** `9bde3c70195f`  
**Status:** Up About an hour  
**Portas:**

| Tipo | Porta Externa | Porta Interna | Protocolo | Uso |
|------|---------------|---------------|-----------|-----|
| 🔒 Interna | - | `8000` | tcp | API/Backend |
| 🔒 Interna | - | `9000` | tcp | - |
| 🔒 Interna | - | `9443` | tcp | - |

---

## 📱 Aplicações

### ✅ api-hub-auth-hub-auth-api-1

**Imagem:** `adminvyadigital/enterprise-hub-backend-auth:latest`  
**Status:** Up 4 weeks (healthy)  
**Portas:**

| Tipo | Porta Externa | Porta Interna | Protocolo | Uso |
|------|---------------|---------------|-----------|-----|
| 🌐 Exposta | `3901` | `3000` | tcp | Auth Hub API |
| 🌐 Exposta | `3901` | `3000` | tcp | Auth Hub API |

### ✅ idp-api-agent-idp-api-1

**Imagem:** `adminvyadigital/idp-agent-backend:latest`  
**Status:** Up 5 days (healthy)  
**Portas:**

| Tipo | Porta Externa | Porta Interna | Protocolo | Uso |
|------|---------------|---------------|-----------|-----|
| 🌐 Exposta | `8000` | `8000` | tcp | API/Backend |
| 🌐 Exposta | `8000` | `8000` | tcp | API/Backend |

### ✅ multiagent-backend-prod

**Imagem:** `adminvyadigital/enterprise-workforce-vertical-agent-backend:latest`  
**Status:** Up 7 weeks (healthy)  
**Portas:**

| Tipo | Porta Externa | Porta Interna | Protocolo | Uso |
|------|---------------|---------------|-----------|-----|
| 🌐 Exposta | `8083` | `8000` | tcp | Backend API |
| 🌐 Exposta | `8083` | `8000` | tcp | Backend API |

### ✅ multiagent-chromadb-prod

**Imagem:** `chromadb/chroma:latest`  
**Status:** Up 7 weeks  
**Portas:**

| Tipo | Porta Externa | Porta Interna | Protocolo | Uso |
|------|---------------|---------------|-----------|-----|
| 🌐 Exposta | `8001` | `8000` | tcp | ChromaDB API |
| 🌐 Exposta | `8001` | `8000` | tcp | ChromaDB API |

### ✅ multiagent-frontend-prod

**Imagem:** `adminvyadigital/enterprise-workforce-vertical-agent-frontend:latest`  
**Status:** Up 7 weeks  
**Portas:**

| Tipo | Porta Externa | Porta Interna | Protocolo | Uso |
|------|---------------|---------------|-----------|-----|
| 🌐 Exposta | `8084` | `80` | tcp | Frontend |
| 🌐 Exposta | `8084` | `80` | tcp | Frontend |

### ✅ synesis-test

**Imagem:** `rawmind/web-test:latest`  
**Status:** Up 7 weeks  
**Portas:**

| Tipo | Porta Externa | Porta Interna | Protocolo | Uso |
|------|---------------|---------------|-----------|-----|
| 🔒 Interna | - | `8080` | tcp | cAdvisor/HTTP |

---

## 📊 Resumo de Portas Expostas

Portas acessíveis externamente no wfdb01.vya.digital:

| Porta | Protocolo | Container | Serviço | URL de Acesso |
|-------|-----------|-----------|---------|---------------|
| `80` | tcp | traefik | HTTP | http://wfdb01.vya.digital |
| `80` | tcp | traefik | HTTP | http://wfdb01.vya.digital |
| `443` | tcp | traefik | HTTPS | https://wfdb01.vya.digital |
| `443` | tcp | traefik | HTTPS | https://wfdb01.vya.digital |
| `3002` | tcp | enterprise-grafana | Grafana UI | http://wfdb01.vya.digital:3002 |
| `3002` | tcp | enterprise-grafana | Grafana UI | http://wfdb01.vya.digital:3002 |
| `3901` | tcp | api-hub-auth-hub-auth-api-1 | Auth Hub API | http://wfdb01.vya.digital:3901 |
| `3901` | tcp | api-hub-auth-hub-auth-api-1 | Auth Hub API | http://wfdb01.vya.digital:3901 |
| `5673` | tcp | rabbitmq | RabbitMQ AMQP (external) | http://wfdb01.vya.digital:5673 |
| `5673` | tcp | rabbitmq | RabbitMQ AMQP (external) | http://wfdb01.vya.digital:5673 |
| `6379` | tcp | redis | Redis | http://wfdb01.vya.digital:6379 |
| `6379` | tcp | redis | Redis | http://wfdb01.vya.digital:6379 |
| `8000` | tcp | idp-api-agent-idp-api-1 | API/Backend | http://wfdb01.vya.digital:8000 |
| `8000` | tcp | idp-api-agent-idp-api-1 | API/Backend | http://wfdb01.vya.digital:8000 |
| `8001` | tcp | multiagent-chromadb-prod | ChromaDB API | http://wfdb01.vya.digital:8001 |
| `8001` | tcp | multiagent-chromadb-prod | ChromaDB API | http://wfdb01.vya.digital:8001 |
| `8080` | tcp | enterprise-cadvisor | cAdvisor/HTTP | http://wfdb01.vya.digital:8080 |
| `8080` | tcp | enterprise-cadvisor | cAdvisor/HTTP | http://wfdb01.vya.digital:8080 |
| `8081` | tcp | dozzle | Dozzle UI | http://wfdb01.vya.digital:8081 |
| `8081` | tcp | dozzle | Dozzle UI | http://wfdb01.vya.digital:8081 |
| `8083` | tcp | multiagent-backend-prod | Backend API | http://wfdb01.vya.digital:8083 |
| `8083` | tcp | multiagent-backend-prod | Backend API | http://wfdb01.vya.digital:8083 |
| `8084` | tcp | multiagent-frontend-prod | Frontend | http://wfdb01.vya.digital:8084 |
| `8084` | tcp | multiagent-frontend-prod | Frontend | http://wfdb01.vya.digital:8084 |
| `9090` | tcp | traefik | Traefik Metrics | http://wfdb01.vya.digital:9090 |
| `9090` | tcp | traefik | Traefik Metrics | http://wfdb01.vya.digital:9090 |
| `9091` | tcp | enterprise-prometheus | Prometheus UI/API | http://wfdb01.vya.digital:9091 |
| `9091` | tcp | enterprise-prometheus | Prometheus UI/API | http://wfdb01.vya.digital:9091 |
| `9093` | tcp | enterprise-alertmanager | Alertmanager UI | http://wfdb01.vya.digital:9093 |
| `9093` | tcp | enterprise-alertmanager | Alertmanager UI | http://wfdb01.vya.digital:9093 |
| `15673` | tcp | rabbitmq | RabbitMQ Management (external) | http://wfdb01.vya.digital:15673 |
| `15673` | tcp | rabbitmq | RabbitMQ Management (external) | http://wfdb01.vya.digital:15673 |

---

## 🎯 Exporters para Prometheus

Containers que exportam métricas para monitoramento:

| Exporter | Container | Porta | Target | Status |
|----------|-----------|-------|--------|--------|
| Node Exporter | `enterprise-node-exporter-host` | `9100` | `localhost:9100 (host network)` | ✅ Configurado |
| PostgreSQL Exporter | `enterprise-postgres-exporter` | `9187` | `postgres-exporter:9187` | ✅ Configurado |
| Prometheus | `enterprise-prometheus` | `9091` | `localhost:9091` | ✅ UP |
| Pushgateway | `enterprise-pushgateway` | `9091` | `pushgateway:9091` | ✅ Interno |
| Traefik (principal) | `traefik` | `9090` | `traefik:8080` | ℹ️ Estado atual em `config/prometheus.yaml` |
| cAdvisor | `enterprise-cadvisor` | `8080` | `localhost:8080` | ✅ Configurado |

### 📝 Notas para Configuração Prometheus:

1. **Traefik (estado atual):** job configurado para `traefik:8080` no `config/prometheus.yaml`.

   Para alterar para `traefik:9090`, validar primeiro em runtime qual endpoint responde metricas no container alvo.

   Exemplo de ajuste (somente se validado):
   ```yaml
   - job_name: 'traefik'
     static_configs:
       - targets: ['traefik:9090']
   ```

2. **MySQL Exporter:** Configurado em wfdb02.vya.digital:9104 (target externo)

3. **Pgbouncer Exporter:** Não instalado (necessário para dashboard publicado)

---

**Documentação gerada automaticamente em:** 2026-05-05 12:04:48

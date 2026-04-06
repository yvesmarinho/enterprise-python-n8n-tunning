# STACK FULL INVENTORY — 2026-04-06

## 1. Objetivo

Mapear portas, containers, redes e pontos de exposição do ambiente (wfdb01, wf001 e wfdb02), com foco no stack Prometheus/Victoria e visão completa incluindo Traefik e demais serviços.

## 2. Método de Inventário

- Coleta remota por SSH SPA (`ssh-wfdb01`, `ssh-wf001`, `ssh-wfdb02`)
- Runtime: `docker ps`, `docker inspect`, `docker network ls`
- Firewall: `ufw status numbered`
- Verificação externa de superfície: teste TCP a partir da estação de operação
- Descoberta de fontes: `docker-compose*.yml` em `/opt/docker_user`

## 3. Inventário do Stack Prometheus/Victoria

### 3.1 wfdb01 (Observabilidade)

Diretriz de banco neste host:

- O container `enterprise-postgres` em `wfdb01` pertence ao stack de observabilidade (Grafana/Loki/Prometheus stack metadata).
- Não há bases de dados de outras aplicacoes de negocio neste PostgreSQL local de `wfdb01`.
- O banco do N8N (DEV e PROD) nao reside em `wfdb01`; reside exclusivamente em `wfdb02`.

Serviços principais (runtime):

| Serviço | Container | Porta interna | Publicação host | Rede(s) |
| --- | --- | --- | --- | --- |
| Prometheus | enterprise-prometheus | 9090/tcp | 0.0.0.0:9091->9090 | app-network, enterprise-observability_loki |
| VictoriaMetrics | enterprise-victoriametrics | 8428/tcp | não publicado | app-network, enterprise-observability_loki |
| Pushgateway | enterprise-pushgateway | 9091/tcp | não publicado | app-network, enterprise-observability_loki |
| Grafana | enterprise-grafana | 3000/tcp | 0.0.0.0:3002->3000 | app-network, enterprise-observability_loki |
| cAdvisor | enterprise-cadvisor | 8080/tcp | 0.0.0.0:8080->8080 | bridge padrão |
| Traefik | traefik | 80/443/9090 | 0.0.0.0:80,443,9090 | app-network, app-network-dev, traefik-internal, web, websecure |

Resultado de exposição externa (teste TCP):

- 86.48.31.149:80 OPEN
- 86.48.31.149:443 OPEN
- 86.48.31.149:9090 OPEN
- 86.48.31.149:9091 OPEN
- 86.48.31.149:3002 OPEN

Observação crítica:

- VictoriaMetrics não está publicado no host (8428 interno), reduzindo risco de acesso anônimo direto.
- Prometheus (9091) e dashboard Traefik (9090) estão acessíveis externamente.

### 3.2 wf001 (Aplicação/Ingress)

Serviços relacionados a coleta e roteamento:

| Serviço | Container | Porta interna | Publicação host | Rede(s) |
| --- | --- | --- | --- | --- |
| Traefik | traefik | 80/443/9090 | 0.0.0.0:80,443,9090 | app-network, web, websecure |
| Collector API | prod-collector-api | 5000/tcp, 9102/tcp | 0.0.0.0:5001->5000, 0.0.0.0:9102->9102 | app-network |
| N8N editor | n8n-n8n_editor-1 | 5678/tcp | não publicado | app-network |
| N8N webhook | n8n-n8n_webhook-1 | 5678/tcp | não publicado | app-network |
| N8N worker | n8n-n8n_worker-1 | 5678/tcp | não publicado | app-network |

Resultado de exposição externa (teste TCP):

- 31.220.103.208:80 OPEN
- 31.220.103.208:443 OPEN
- 31.220.103.208:9090 OPEN
- 31.220.103.208:5001 OPEN
- 31.220.103.208:9102 CLOSED no teste externo

### 3.3 wfdb02 (Banco)

- UFW ativo com regras SPA e allow seletivo para 9100/tcp.
- Docker não disponível neste host (comando `docker` ausente no usuário atual), consistente com papel de banco gerenciado fora do stack de containers desta sessão.
- Escopo de banco do N8N: `wfdb02` e o servidor canônico para analise de performance de banco do projeto (`n8n_dev_db` para DEV gate e `n8n_db` para PROD).

## 4. Inventário de Traefik

### 4.1 Definições encontradas

- wfdb01: `/opt/docker_user/traefik/docker-compose.yaml`
- wf001: `/opt/docker_user/traefik/docker-compose.yaml`

### 4.2 Comportamento observado

- Ambos publicam 80/443/9090 no host.
- Em wf001, `--api.insecure=true` está presente na definição de compose do Traefik.
- Em wfdb01, o compose indica `--api.insecure=false`, porém runtime segue com 9090 publicado.

Implicação:

- Mesmo com API insecure desativada em um host, a publicação de 9090 mantém superfície de administração/diagnóstico exposta se não houver proteção adicional na camada de firewall/rede.

## 5. Inventário dos Demais Containers com Portas Publicadas

### 5.1 wfdb01 (principais publicações)

- api-hub-auth-hub-auth-api-1: 3901->3000
- redis-insight: 5540->5540
- idp-api-agent-idp-api-1: 8000->8000
- dozzle: 8081->8080
- enterprise-cadvisor: 8080->8080
- enterprise-prometheus: 9091->9090
- traefik: 80, 443, 9090
- rabbitmq: 5673->5672, 15673->15672
- redis: 6379->6379
- enterprise-grafana: 3002->3000
- multiagent-frontend-prod: 8084->80
- multiagent-backend-prod: 8083->8000
- multiagent-chromadb-prod: 8001->8000

### 5.2 wf001 (principais publicações)

- evolution_api_wea004: 8088->8080
- prod-collector-api: 5001->5000, 9102->9102
- synChat: 3008->3000
- kutt-link-vya-digital: 3003->3000
- dashboard (metabase): 3002->3000
- traefik: 80, 443, 9090
- api012.vyadigital: 3033->3033
- dashy: 8083->8080
- code_store: 5000->5000
- perfexcrm: 8001->80
- ajuda: 8002->80
- passbolt: 8090->80, 8091->443
- rabbitmq: 5673->5672, 15673->15672
- redis: 6379->6379
- portainer: 9000->9000

## 6. Fontes de Verdade (Compose) por Host

### 6.1 wfdb01

Principais arquivos encontrados:

- `/opt/docker_user/enterprise-observability/docker-compose.yaml`
- `/opt/docker_user/traefik/docker-compose.yaml`
- `/opt/docker_user/n8n/docker-compose.yaml`
- `/opt/docker_user/n8n/docker-compose.override.yml`

### 6.2 wf001

Principais arquivos encontrados:

- `/opt/docker_user/traefik/docker-compose.yaml`
- `/opt/docker_user/n8n/docker-compose.yaml`
- `/opt/docker_user/n8n-monitoring-local/docker-compose.yml`
- Demais stacks de aplicação em subpastas de `/opt/docker_user`

## 7. Análise de Segurança: UFW x Docker

Achado operacional importante:

- Existem portas abertas externamente que não aparecem como ALLOW explícito no UFW, comportamento típico de publicação Docker (`-p`) quando regras de NAT/forward permitem bypass parcial da política esperada.

Risco direto para observabilidade:

- Sem controle por usuário no Victoria, a proteção precisa ser por segmentação de rede/firewall.
- Mesmo com Victoria não publicado, Prometheus/Traefik publicados podem expor metadados, targets e topologia do ambiente.

## 8. Recomendações de Hardening (sem aplicar nesta etapa)

### 8.1 Priorização imediata (P0)

1. Restringir acesso externo ao dashboard Traefik (9090) em wfdb01 e wf001.
2. Restringir acesso externo ao Prometheus (9091) em wfdb01.
3. Restringir exposição externa do Redis (6379) em wf001 (ideal: somente rede interna).

### 8.2 Controles recomendados

1. UFW com allowlist por IP de administração para portas de observabilidade.
2. Regras na cadeia `DOCKER-USER` para garantir bloqueio mesmo com publish Docker.
3. Manter Victoria sem publish de porta host (estado atual já adequado).
4. Se dashboard Traefik precisar existir, expor somente por VPN/IP allowlist e autenticação.

### 8.3 Exemplo de política alvo (conceitual)

- Público: 80/443 apenas.
- Administração (allowlist): 5010 (via SPA), eventualmente 9090/9091/3002 se necessário.
- Interno apenas: 6379, 5673, 15673, 5001, 9102, 8080/8081.

## 9. Conclusão

- Inventário completo realizado para stack Prometheus/Victoria + Traefik + demais containers em wfdb01/wf001 e baseline de firewall em wfdb02.
- Fronteira de dados confirmada: PostgreSQL local de `wfdb01` e exclusivo da observabilidade; qualquer analise/performance do banco do N8N deve ser feita em `wfdb02`.
- A principal superfície sensível atual não é Victoria diretamente, e sim portas de administração/monitoramento expostas por publish Docker.
- Próximo passo recomendado: executar janela de hardening UFW + DOCKER-USER com plano de rollback e validação pós-aplicação.

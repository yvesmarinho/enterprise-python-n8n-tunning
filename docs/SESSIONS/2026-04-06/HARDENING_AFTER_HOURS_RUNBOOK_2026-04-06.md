# Hardening Pós-Expediente — Runbook Operacional

**Data**: 2026-04-06
**Escopo**: `wfdb01` (observabilidade) e `wf001` (produção)
**Objetivo**: reduzir superfície de ataque em portas de observabilidade/admin sem indisponibilizar tráfego de negócio.

## 0. Fronteira de Banco de Dados (N8N)

1. O PostgreSQL local de `wfdb01` e exclusivo do stack Prometheus/observabilidade.
2. Nao existem bases de dados de outras aplicacoes nesse PostgreSQL de `wfdb01`.
3. Toda analise de desempenho de banco do N8N deve ser executada em `wfdb02`:

- DEV: `n8n_dev_db`
- PROD: `n8n_db`

## 1. Janela e Pré-condições

1. Janela recomendada: após expediente, com baixa volumetria.
2. Responsáveis online: operador + aprovador de produção.
3. Acesso SPA validado para `wfdb01` e `wf001`.
4. Plano de rollback pronto antes de qualquer mudança.
5. Comunicação prévia de mudança em canal de operações.

## 2. Estratégia de Hardening

Motivação técnica:

- Publicações Docker (`-p`) podem expor serviços mesmo quando a política de UFW sugere restrição.
- O ponto de contenção efetivo é a cadeia `DOCKER-USER` (iptables), aplicada antes das regras de forwarding do Docker.

Meta de exposição:

1. Público: manter apenas `80/443`.
2. Administração: restringir `9090` (Traefik dashboard) e `9091` (Prometheus) por allowlist ou bloquear totalmente.
3. Evitar exposição direta de portas internas de serviço (`6379`, `5673`, `15673`, `5001`, `9102`, `8080`, `8081`) salvo necessidade explícita.

## 3. Execução — wfdb01

### 3.1 Backup lógico das regras atuais

```bash
~/.local/bin/ssh-wfdb01 'sudo iptables-save > /tmp/iptables-before-hardening-$(date +%Y%m%d-%H%M%S).rules && ls -lh /tmp/iptables-before-hardening-*.rules | tail -n 1'
```

### 3.2 Aplicar bloqueio de observabilidade externa

```bash
~/.local/bin/ssh-wfdb01 '
set -e
sudo iptables -C DOCKER-USER -i eth0 -p tcp --dport 9090 -j DROP 2>/dev/null || sudo iptables -I DOCKER-USER 1 -i eth0 -p tcp --dport 9090 -j DROP
sudo iptables -C DOCKER-USER -i eth0 -p tcp --dport 9091 -j DROP 2>/dev/null || sudo iptables -I DOCKER-USER 1 -i eth0 -p tcp --dport 9091 -j DROP
sudo iptables -S DOCKER-USER
'
```

### 3.3 Validação pós-mudança

```bash
# Da estação de operação
for p in 9090 9091 80 443; do
  if nc -z -w 2 86.48.31.149 "$p" >/dev/null 2>&1; then
    echo "86.48.31.149:$p OPEN"
  else
    echo "86.48.31.149:$p CLOSED"
  fi
done
```

Critério esperado:

- `9090` e `9091`: `CLOSED`
- `80` e `443`: `OPEN`

## 4. Execução — wf001 (produção)

### 4.1 Backup lógico das regras atuais

```bash
~/.local/bin/ssh-wf001 'sudo iptables-save > /tmp/iptables-before-hardening-$(date +%Y%m%d-%H%M%S).rules && ls -lh /tmp/iptables-before-hardening-*.rules | tail -n 1'
```

### 4.2 Aplicação recomendada por fases

Fase A (baixo risco):

- Bloquear `9090` (Traefik dashboard) em `DOCKER-USER`.

Fase B (avaliar dependências):

- Restringir `5001` e `9102` (collector-api) conforme dependência externa real.
- Restringir `6379` (Redis) para acesso interno apenas.

Exemplo para fase A:

```bash
~/.local/bin/ssh-wf001 '
set -e
sudo iptables -C DOCKER-USER -i eth0 -p tcp --dport 9090 -j DROP 2>/dev/null || sudo iptables -I DOCKER-USER 1 -i eth0 -p tcp --dport 9090 -j DROP
sudo iptables -S DOCKER-USER
'
```

### 4.3 Validação pós-mudança

```bash
# Da estação de operação
for p in 9090 80 443 5001; do
  if nc -z -w 2 31.220.103.208 "$p" >/dev/null 2>&1; then
    echo "31.220.103.208:$p OPEN"
  else
    echo "31.220.103.208:$p CLOSED"
  fi
done
```

## 5. Rollback (imediato)

### 5.1 Remover regras específicas

```bash
# wfdb01
~/.local/bin/ssh-wfdb01 '
sudo iptables -D DOCKER-USER -i eth0 -p tcp --dport 9091 -j DROP || true
sudo iptables -D DOCKER-USER -i eth0 -p tcp --dport 9090 -j DROP || true
sudo iptables -S DOCKER-USER
'

# wf001 (quando aplicado)
~/.local/bin/ssh-wf001 '
sudo iptables -D DOCKER-USER -i eth0 -p tcp --dport 9090 -j DROP || true
sudo iptables -S DOCKER-USER
'
```

### 5.2 Restore completo (se necessário)

```bash
# Exemplo com arquivo salvo em /tmp
sudo iptables-restore < /tmp/iptables-before-hardening-YYYYMMDD-HHMMSS.rules
```

## 6. Persistência (pós-estabilização)

Estado atual observado:

- `netfilter-persistent` ausente nos hosts avaliados.
- Regras atuais são runtime e podem se perder em reboot.

Ação recomendada:

1. Instalar mecanismo de persistência em janela dedicada.
2. Versionar automação Ansible para reconstituir regras em boot.
3. Documentar baseline final por host após estabilização.

## 7. Relação com T033 e T034

1. Hardening reduz exposição de superfície administrativa, mas não resolve sozinho a proveniência de métricas F18.
2. T033 depende de `pushgateway_absent_1h=true` e coerência de contagem para `PROVENANCE_OK`.
3. T034 só deve ser executado após T033 aprovado.

## 8. Checklist de Fechamento da Janela

1. Confirmar saúde HTTP `80/443` em ambos os hosts.
2. Confirmar fechamento das portas administrativas alvo.
3. Confirmar ausência de regressão nos serviços críticos (n8n/webhooks/coleta).
4. Registrar evidências em documento de sessão e relatório copilot.
5. Formalizar aprovação de encerramento da mudança.

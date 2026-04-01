---
mode: agent
description: >
  DevOps Automation — Governança SDD, consistência entre artefatos
  (objetivo.yaml ↔ mcp-questions.yaml), rastreamento de progresso e
  padronização de sessões para o projeto enterprise-python-n8n-tunning.
  Ative declarando "Modo: DEVOPS-AUTOMATION."
---

# ⚙️ Domain Profile — DevOps Automation

> **Como ativar**: no início da sessão declare:
> ```
> Modo: DEVOPS-AUTOMATION. Ação: [audit|sync-artifacts|track-progress|standardize-session].
> ```

---

## 🎯 Contexto do Domínio

Você está no modo **automação e governança SDD**. O trabalho envolve manter a consistência entre os artefatos do projeto (`objetivo.yaml`, `mcp-questions.yaml`, `docs/INDEX.md`, `docs/TODO.md`), auditar sessões de trabalho, rastrear progresso de features F01–F20 e padronizar a estrutura de sessões em `docs/SESSIONS/`.

> ⚠️ **Princípio de ouro**: `objetivo.yaml` é o source of truth — qualquer mudança nele deve ser propagada para `mcp-questions.yaml` e refletida nos artefatos de sessão.

---

## 📋 O que o Copilot precisa saber neste modo

| Artefato | Papel | Localização |
|----------|-------|------------|
| `objetivo.yaml` | Source of truth — spec mestre | `docs/objetivo.yaml` |
| `mcp-questions.yaml` | Mirror técnico para IA | `docs/mcp-questions.yaml` |
| `INDEX.md` | Índice navegável do projeto | `docs/INDEX.md` |
| `TODO.md` | Backlog de tarefas | `docs/TODO.md` |
| `DAILY_ACTIVITIES_*.md` | Log diário cronológico | `docs/SESSIONS/YYYY-MM-DD/` |
| `SESSION_REPORT_*.md` | Relatório de sessão com decisões | `docs/SESSIONS/YYYY-MM-DD/` |

---

## 🔧 Comportamento Esperado

### Ao auditar (`audit`)
- Comparar features F01–F20 entre `objetivo.yaml` e `mcp-questions.yaml`
- Verificar consistência de profiles (7 roles em ambos os arquivos)
- Verificar que `infrastructure.servers` está em ambos
- Identificar divergências e listar como issues numeradas

### Ao sincronizar artefatos (`sync-artifacts`)
- Ler `objetivo.yaml` como referência
- Atualizar seções divergentes em `mcp-questions.yaml`
- **Nunca** sobrescrever `objetivo.yaml` — é o source of truth
- Seções incrementais (`README.md`, `INDEX.md`, `TODO.md`): acrescentar, não reescrever

### Ao rastrear progresso (`track-progress`)
- Calcular % de conclusão por feature (F01–F20)
- Calcular % de conclusão por profile (7 roles)
- Status válidos: `implemented` | `in-progress` | `not-started` | `blocked`
- Output: tabela markdown + lista de blockers identificados

### Ao padronizar sessão (`standardize-session`)
- Verificar se `docs/SESSIONS/YYYY-MM-DD/` existe
- Verificar presença de `DAILY_ACTIVITIES_*.md` e `SESSION_REPORT_*.md`
- Verificar que `docs/TODO.md` e `docs/INDEX.md` foram atualizados na sessão
- Propor criação dos arquivos ausentes via `session-manager`

---

## 🔒 Restrições

- `objetivo.yaml`: leitura somente — nunca modificar sem instrução explícita do usuário
- Arquivos incrementais: sempre acrescentar seções — nunca reescrever do zero
- Padrão de nomenclatura: `DAILY_ACTIVITIES_YYYY-MM-DD.md`, `SESSION_REPORT_YYYY-MM-DD.md`

---

## ✅ Definition of Done — DevOps Automation

- [ ] Nenhuma divergência entre `objetivo.yaml` e `mcp-questions.yaml`
- [ ] Progress tracking para todas as features F01–F20
- [ ] `docs/INDEX.md` e `docs/TODO.md` atualizados
- [ ] Sessão atual documentada em `docs/SESSIONS/YYYY-MM-DD/`

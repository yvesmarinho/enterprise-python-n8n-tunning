---
applyTo: "**"
---

# GitHub Copilot — Instruções do Projeto

**Projeto**: `enterprise-python-n8n-tunning` — Enterprise Python N8n Tunning
**Domínio**: infrastructure | **Linguagem**: python
**Regras completas**: `.copilot-rules-enterprise-python-n8n-tunning.md`
**Rituais de sessão**: `.github/prompts/session-start.prompt.md` | `session-end.prompt.md`
**Domain Profile ativo**: `.github/prompts/domain/devops-infrastructure.prompt.md`

---

## 🤖 Agentes do Projeto

| Agente | Arquivo | Quando usar |
|--------|---------|-------------|
| `system-architect` | `.github/agents/system-architect.agent.md` | Arquitetura Docker, upgrade strategy, rollback design |
| `n8n-specialist` | `.github/agents/n8n-specialist.agent.md` | Compatibilidade N8N, validação de workflows, análise de filas |
| `devops-engineer` | `.github/agents/devops-engineer.agent.md` | Implementar F16–F20 via Ansible + Python |
| `devops-automation` | `.github/agents/devops-automation.agent.md` | Governança SDD, sinc objetivo.yaml ↔ mcp-questions.yaml |
| `project-manager` | `.github/agents/project-manager.agent.md` | Milestones, riscos, janelas de manutenção |
| `test-engineer` | `.github/agents/test-engineer.agent.md` | Matriz de testes, gates de promoção wfdb01 → wf001 |
| `databases-engineer` | `.github/agents/databases-engineer.agent.md` | PostgreSQL: purgação execution_entity, backup, pg_stat_statements |

## 🎭 Domain Profiles (Prompts)

| Prompt | Modo de ativação |
|--------|-----------------|
| `system-architect.prompt.md` | `Modo: SYSTEM-ARCHITECT.` |
| `n8n-specialist.prompt.md` | `Modo: N8N-SPECIALIST.` |
| `devops-engineer.prompt.md` | `Modo: DEVOPS-ENGINEER.` |
| `devops-automation.prompt.md` | `Modo: DEVOPS-AUTOMATION.` |
| `project-manager.prompt.md` | `Modo: PROJECT-MANAGER.` |
| `test-engineer.prompt.md` | `Modo: TEST-ENGINEER.` |
| `databases-engineer.prompt.md` | `Modo: DATABASES-ENGINEER.` |

---

## 🚨 Regras P0 — CRÍTICO (nunca violar)

### 1. Criar/editar arquivos — NUNCA via terminal

| Operação | ✅ Ferramenta obrigatória |
|----------|--------------------------|
| Criar arquivo novo | `create_file` |
| Editar arquivo existente | `replace_string_in_file` (mín. 3 linhas de contexto) |
| Múltiplas edições | `multi_replace_string_in_file` |

❌ **PROIBIDO**: `cat > heredoc`, `echo >> arquivo`, `echo | tee arquivo`

---

### 2. Ler/buscar/listar arquivos — NUNCA via terminal

| Operação | ✅ Ferramenta obrigatória |
|----------|--------------------------|
| Ler conteúdo | `read_file` |
| Buscar texto | `grep_search` |
| Encontrar arquivos | `file_search` |
| Listar diretório | `list_dir` |
| Busca semântica | `semantic_search` |
| Verificar erros | `get_errors` |

❌ **PROIBIDO via terminal**: `cat`, `grep`, `find`, `ls`
✅ **`run_in_terminal` apenas para**: `git`, `make`, `pytest`, `pip install`, `docker`, `systemctl`

---

### 3. Mover/copiar/excluir arquivos — SEMPRE Python stdlib

```python
import shutil, logging
from pathlib import Path

log = logging.getLogger(__name__)
src, dst = Path("origem/arq.md"), Path("destino/arq.md")
dst.parent.mkdir(parents=True, exist_ok=True)
if src.exists():
    shutil.move(str(src), str(dst))
    log.info("✅ %s → %s", src, dst)
```

❌ **PROIBIDO**: `mv`, `cp`, `rm`, `mkdir` via terminal

---

### 4. Git commits — SEMPRE via arquivo de mensagem

```bash
echo "feat(escopo): descrição" > /tmp/commit.txt
./scripts/git-commit-with-file.sh /tmp/commit.txt
```

❌ **PROIBIDO**: `git commit -m "..."` direto

---

## 📋 Regras P1 — Organização

### 5. Pastas corretas

| Tipo | Localização |
|------|-------------|
| Docs de sessão | `docs/SESSIONS/YYYY-MM-DD/` |
| Interações Copilot | `docs/copilot/` |
| Docs técnicos | `docs/` |
| Python source | `src/` |
| Scripts | `scripts/` |

❌ **NUNCA** arquivos de sessão/doc na raiz

---

### 5b. Registrar interações Copilot em `docs/copilot/`

Após toda interação que produza **decisão, implementação ou debate técnico**, criar:

```
docs/copilot/CHAT-YYYYMMDD-HHMMSS.md
```

Estrutura mínima obrigatória: Resumo · Decisões Tomadas · Ações Realizadas · Artefatos · Pendências.
Regra completa: `.copilot-rules-enterprise-python-n8n-tunning.md` → seção "Documentação de Interações Copilot".

---

### 6. Documentos incrementais — nunca sobrescrever

`README.md`, `docs/INDEX.md`, `docs/TODO.md`, `docs/SESSIONS/*/DAILY_ACTIVITIES_*.md`,
`docs/SESSIONS/*/SESSION_REPORT_*.md`, `docs/SESSIONS/*/FINAL_STATUS_*.md` →
sempre **acrescentar**, nunca reescrever do zero.

---

### 7. Nomenclatura

| Tipo | Padrão |
|------|--------|
| Python | `snake_case.py` |
| Markdown | `SCREAMING_SNAKE.md` |
| JSON | `kebab-case.json` |
| Shell | `kebab-case.sh` |

---

## 🔒 Segurança

- Credenciais/tokens: NUNCA em arquivos versionados
- `mcp.json`: usar `${env:VAR_NAME}` ou `.secrets/.env`
- `.secrets/` está no `.gitignore` ✅

---

## ⚠️ Enforcement

```
❌ REGRA [N] violada: [nome]
Motivo: [explicação]
Correto: [alternativa válida]
```

*Gerado por scaffold.py em 2026-04-01T13:38:39Z — Projeto: enterprise-python-n8n-tunning*

## Recent Changes
- 001-p1-tunning-instrumentacao: Added Python 3.11+ (reStructuredText docstrings, Doctest, Fabric pattern) + Ansible 2.15+, ansible-lint, Fabric/Paramiko, psycopg2, prometheus-client
- 001-p1-tunning-instrumentacao: Added [if applicable, e.g., PostgreSQL, CoreData, files or N/A]

## Active Technologies
- Python 3.11+ (reStructuredText docstrings, Doctest, Fabric pattern) + Ansible 2.15+, ansible-lint, Fabric/Paramiko, psycopg2, prometheus-client (001-p1-tunning-instrumentacao)
- PostgreSQL (N8N backend — `execution_entity` 429K+ rows), VictoriaMetrics (métricas) (001-p1-tunning-instrumentacao)

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

❌ **PROIBIDO**: `cat > heredoc`, `echo >> arquivo`, `echo | tee arquivo`, qualquer variação de `cat <<EOF`

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
✅ **`run_in_terminal` apenas para**: `git`, `make`, `pytest`, `pip install`, `docker`, `systemctl`, `ansible-playbook`, `ssh`, `curl`, `nc`

---

### 3. Mover/copiar/excluir arquivos — SEMPRE Python stdlib

**1–2 arquivos:** `run_in_terminal mv` é aceitável.
**3+ arquivos:** OBRIGATÓRIO Python + JSON (nunca `mv` repetido ou loop shell):

```python
import shutil, logging
from pathlib import Path

log = logging.getLogger(__name__)
root = Path("/home/yves_marinho/Documentos/DevOps/Vya-Jobs/enterprise-python-n8n-tunning")
ops = [
    {"name": "arquivo.md", "from": "origem/", "to": "destino/"},
]
for op in ops:
    src = root / op["from"] / op["name"]
    dst = root / op["to"]  / op["name"]
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.exists():
        shutil.move(str(src), str(dst))
        log.info("✅ %s → %s", op["from"], op["to"])
```

❌ **PROIBIDO**: `mv`, `cp`, `rm`, `mkdir` em série via terminal para lotes

---

### 4. Git commits — SEMPRE via arquivo de mensagem

```bash
# Criar mensagem com create_file, depois:
./scripts/git-commit-with-file.sh /tmp/commit.txt
```

❌ **PROIBIDO**: `git commit -m "..."` direto
❌ **PROIBIDO**: heredoc ou textos ≥ 6 linhas no terminal

**Regra de tamanho:** ≤ 5 linhas → `echo "msg" > /tmp/commit.txt` OK | ≥ 6 linhas → `create_file` + script

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
| Scripts temporários | `scripts/tmp/` (gitignored) — **NUNCA `/tmp/` do sistema** |
| Especificações Speckit | `specs/` |
| Playbooks Ansible | `ansible/` |

❌ **NUNCA** arquivos de sessão/doc na raiz
❌ **NUNCA** criar arquivos em `.specify/` (exclusivo SpecKit)

### 5c. Limpeza de `tmp/` no end-session

`tmp/` deve ser **esvaziada ao final de cada sessão** como parte da rotina `session-end.prompt.md`:

```bash
# Durante o ritual de encerramento:
rm -f tmp/*          # apaga conteúdo
git checkout -- tmp/ # restaura .gitkeep se necessário
```

❌ **NUNCA** commitar conteúdo de `tmp/` — apenas o `.gitkeep`

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
*Atualizado em 2026-04-02 — SSH SPA, Ansible SPA pattern, N8N Tunning rules, feature sequence F16–F25*

## 🔑 SSH SPA — Acesso aos Servidores

**Todos os servidores VPS utilizam SSH SPA (fwknop) — porta SSH 5010, porta knock UDP 62201.**

| Servidor | IP | Função |
|----------|----|--------|
| wf001.vya.digital | 31.220.103.208 | N8N produção |
| wf008.vya.digital | 31.220.103.208 | Journey System |
| wfdb01.vya.digital | 86.48.31.149 | Observability + N8N teste |
| wfdb02.vya.digital | 82.197.64.145 | PostgreSQL/MySQL produção |

```bash
make ssh-spa-knock-one HOST=wfdb01     # knock manual antes de SSH
~/.local/bin/ssh-wfdb01 'docker ps'   # wfdb01: knock automático
```

**Janela de acesso**: 30s | **fwknop**: usar `$IP`/`$SRC` — NUNCA `%IP%`/`%SRC%`
**UFW**: `ufw insert 1 allow from $IP to any port 5010` (primeiro match ganha)

---

## 🏗️ Ansible — Padrão com SPA

Todo playbook que acessa VPS deve ter Play 1 para knock SPA:

```yaml
- name: SPA Knock
  hosts: localhost
  connection: local
  tasks:
    - command: fwknop --rc-file ~/.fwknoprc -n {{ inventory_hostname }}
    - pause: {seconds: 3}
    - wait_for: {host: "{{ ansible_host }}", port: 5010, timeout: 30}

- name: Deploy
  hosts: <host>
  become: false
  tasks:
    - command: docker compose up -d n8n
      args: {chdir: /opt/docker_user/n8n}
      become: true
      become_user: docker_user
```

**Paths VPS**: N8N em `/opt/docker_user/n8n` (wf001 e wfdb01)

---

## 📊 Regras de Projeto — Tunning N8N

- **P0**: Operações em `wf001` → janela de manutenção + backup validado obrigatórios
- **P0**: Toda mudança em `wf001` → evidências métricas antes/depois no `SESSION_REPORT`
- **P0**: Alterações em workflows de clientes (121Labs PABX, WhatsApp Gateway) → aprovação do `project-manager`

### Sequência de features (ANA-001)

| Fase | Features | Observação |
|------|----------|------------|
| P1 | F16, F17, F18 | Paralelas em wfdb01 → promover em bloco para wf001 |
| P2 | F23, F20, F22, F24 | Depende de P1 estável em wf001 |
| P3 | F19, F21, F25 | Depende de P1+P2; F21/F25 requer cliente 121Labs |

---

## Recent Changes
- 001-001-tunning-instrumentacao: Added Python 3.11 (uv, Fabric pattern, reStructuredText docstrings, Doctest) + Ansible 2.15+, ansible-lint, Fabric/Paramiko, psycopg2-binary, prometheus-client
- 001-p1-tunning-instrumentacao: Added Python 3.11+ (reStructuredText docstrings, Doctest, Fabric pattern) + Ansible 2.15+, ansible-lint, Fabric/Paramiko, psycopg2, prometheus-client
- 001-p1-tunning-instrumentacao: Added [if applicable, e.g., PostgreSQL, CoreData, files or N/A]

## Active Technologies
- Python 3.11 (uv, Fabric pattern, reStructuredText docstrings, Doctest) + Ansible 2.15+, ansible-lint, Fabric/Paramiko, psycopg2-binary, prometheus-client (001-001-tunning-instrumentacao)
- PostgreSQL 16 (wfdb02 — 82.197.64.145:6432; Pgbouncer pooler :5432); N8N Docker volumes em `/opt/docker_user/n8n` (001-001-tunning-instrumentacao)

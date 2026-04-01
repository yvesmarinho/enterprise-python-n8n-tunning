# 📝 TODO — Enterprise Python N8n Tunning

**Last Updated**: 2026-04-01 — Sessão de infraestrutura wfdb02 + limpeza Speckit ✅ Concluído

---

## 🟠 Em Progresso

*(nenhum)*

## 🔴 P0 — Próxima Sessão (executar na ordem)

- [ ] **Revisar `docs/mcp-questions.yaml`** — sincronizar com as atualizações do `objetivo.yaml` (wfdb02 adicionado, constitution v2.1.0)
- [ ] **Refazer fluxo Speckit completo** — `speckit.specify → clarify → plan → checklist → tasks → analyze → implement` com `SPECIFY_FEATURE="001-p1-tunning-instrumentacao"` (artefatos de specs/ foram removidos e precisam ser regerados do zero)
- [ ] **Atualizar `.copilot-rules-enterprise-python-n8n-tunning.md`** — baseado em `.github/copilot-instructions.md` (regras defasadas)

## 🔵 P1 — Pendente

- [ ] **Revisar constitution** — verificar se todos os perfis (system_architect, N8N_specialist, test_engineer) em `objetivo.yaml` estão alinhados com constitution v2.1.0 (escopo de tunning, não upgrade)
- [ ] Configurar estrutura inicial do projeto (`src/`, `ansible/`, `tests/`) — gerada pelo speckit.implement
- [ ] Adicionar testes unitários
- [ ] Documentar APIs

## ✅ Concluído

- [x] Scaffold inicial gerado (2026-04-01T13:38:39Z)
- [x] Fluxo Speckit completo executado — speckit.clarify, plan, checklist, tasks, analyze (sessão anterior)
- [x] Servidor wfdb02 adicionado à infraestrutura — `objetivo.yaml`, `constitution.md` v2.1.0, `mcp-questions.yaml`, `plan-template.md` (2026-04-01)
- [x] Constitution atualizada para v2.1.0 — três servidores, Princípio III expandido (2026-04-01)
- [x] Artefatos Speckit removidos para regeração limpa — `specs/001-p1-tunning-instrumentacao/` (2026-04-01)

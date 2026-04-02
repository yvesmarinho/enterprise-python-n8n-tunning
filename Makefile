# Makefile — Enterprise Python N8n Tunning
# Gerado por scaffold.py em 2026-04-01T13:38:39Z

.PHONY: help init dev build test lint format clean

## Mostra esta ajuda
help:
	@grep -E '^## ' Makefile | sed 's/## //'

## [DEPRECATED] — use: uv run scripts/scaffold.py
init:
	@echo ""
	@echo " ⚠️  Para criar/configurar o projeto, use diretamente:"
	@echo "      uv run scripts/scaffold.py"
	@echo "      python scripts/scaffold.py"
	@echo ""

## Instala dependências
install-deps:
	@echo "Instalando dependências..."

## Inicia servidor de desenvolvimento
dev:
	@echo "Iniciando desenvolvimento..."

## Build de produção
build:
	@echo "Buildando..."

## Executa testes
test:
	@echo "Executando testes..."

## Lint do código
lint:
	@echo "Linting..."

## Formata código
format:
	@echo "Formatando..."

## Remove arquivos gerados
clean:
	@rm -rf dist/ build/ __pycache__/ .pytest_cache/ *.egg-info/ .coverage htmlcov/
## Carrega variáveis MCP do .secrets/.env e orienta a abrir o VS Code
mcp:
	@bash scripts/load-mcp.sh

## Executa playbook F16 (métricas de fila) em wfdb01
f16:
	ansible-playbook ansible/playbooks/f16-queue-metrics.yml \
	  -i ansible/inventory/ -l wfdb01

## Executa playbook F17 (purgação + pg_stat_statements) em wfdb01
f17:
	ansible-playbook ansible/playbooks/f17-postgres-tuning.yml \
	  -i ansible/inventory/ -l wfdb01

## Executa playbook F18 (auditoria dupla coleta — somente leitura) em wfdb01
f18:
	ansible-playbook ansible/playbooks/f18-dual-collection-audit.yml \
	  -i ansible/inventory/ -l wfdb01

## Executa ansible-lint em todos os playbooks F16/F17/F18
lint-playbooks:
	ansible-lint ansible/playbooks/f16-queue-metrics.yml \
	  ansible/playbooks/f17-postgres-tuning.yml \
	  ansible/playbooks/f18-dual-collection-audit.yml

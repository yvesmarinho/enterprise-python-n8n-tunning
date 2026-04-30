#!/usr/bin/env python3
"""
Verifica tamanho atual da tabela execution_entity no PostgreSQL do N8N.

Conecta ao banco n8n_db em wfdb02 e consulta:
- Tamanho total da tabela execution_entity
- Número de linhas
- Top 10 workflows por volume de execuções armazenadas
- Distribuição temporal (últimos 30/60/90 dias)

Saída: JSON em docs/SESSIONS/YYYY-MM-DD/postgres-execution-entity-YYYYMMDD-HHMMSS.json

NOTA: Este script é um template para execução REMOTA em wfdb02.
      Requer psycopg2 e acesso ao PostgreSQL em wfdb02.

Exemplos
--------
>>> # Executar via SSH em wfdb02:
>>> ssh wfdb02 'python3 /tmp/check_execution_entity.py'
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


# SQL Queries
QUERY_TABLE_SIZE = """
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as total_size,
    pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
FROM pg_tables
WHERE schemaname = 'public' AND tablename = 'execution_entity'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
"""

QUERY_ROW_COUNT = """
SELECT COUNT(*) as total_rows FROM execution_entity;
"""

QUERY_ROWS_BY_PERIOD = """
SELECT
    COUNT(*) FILTER (WHERE "startedAt" >= NOW() - INTERVAL '30 days') as last_30d,
    COUNT(*) FILTER (WHERE "startedAt" >= NOW() - INTERVAL '60 days') as last_60d,
    COUNT(*) FILTER (WHERE "startedAt" >= NOW() - INTERVAL '90 days') as last_90d,
    COUNT(*) FILTER (WHERE "startedAt" >= NOW() - INTERVAL '180 days') as last_180d,
    COUNT(*) as total
FROM execution_entity;
"""

QUERY_TOP_WORKFLOWS = """
SELECT
    "workflowId",
    COUNT(*) as exec_count,
    MIN("startedAt") as first_exec,
    MAX("startedAt") as last_exec
FROM execution_entity
WHERE "startedAt" >= NOW() - INTERVAL '90 days'
GROUP BY "workflowId"
ORDER BY exec_count DESC
LIMIT 10;
"""


def check_psycopg2() -> bool:
    """
    Verifica se psycopg2 está disponível.

    Returns
    -------
    bool
        True se psycopg2 importável, False caso contrário
    """
    try:
        import psycopg2  # noqa: F401
        return True
    except ImportError:
        return False


def get_db_connection():
    """
    Conecta ao PostgreSQL n8n_db em wfdb02.

    Returns
    -------
    psycopg2.connection
        Conexão ao banco de dados

    Notes
    -----
    Credenciais devem estar em variáveis de ambiente ou .pgpass
    """
    import psycopg2

    # Configuração do banco (ajustar conforme ambiente)
    conn_params = {
        "host": "localhost",  # wfdb02
        "port": 6432,          # PostgreSQL (não Pgbouncer 5432)
        "database": "n8n_db",
        "user": "postgres",    # ou usuário com permissão de leitura
    }

    log.info(f"Conectando a {conn_params['database']} em {conn_params['host']}:{conn_params['port']}...")
    conn = psycopg2.connect(**conn_params)
    return conn


def execute_query(conn, query: str) -> list[tuple]:
    """
    Executa query SQL e retorna resultados.

    Parameters
    ----------
    conn : psycopg2.connection
        Conexão ao banco
    query : str
        Query SQL

    Returns
    -------
    list[tuple]
        Resultados da query
    """
    with conn.cursor() as cur:
        cur.execute(query)
        return cur.fetchall()


def main() -> None:
    """
    Verifica estado atual da execution_entity em n8n_db (prod).
    """
    log.info("=== Verificação PostgreSQL — execution_entity (n8n_db) ===")

    if not check_psycopg2():
        log.error("❌ psycopg2 não disponível. Instale com: pip install psycopg2-binary")
        sys.exit(1)

    try:
        conn = get_db_connection()

        # 1. Tamanho da tabela
        log.info("Consultando tamanho da tabela...")
        size_result = execute_query(conn, QUERY_TABLE_SIZE)
        table_size = {
            "schema": size_result[0][0] if size_result else None,
            "table": size_result[0][1] if size_result else None,
            "size_pretty": size_result[0][2] if size_result else None,
            "size_bytes": size_result[0][3] if size_result else None,
        }

        # 2. Contagem total de linhas
        log.info("Contando linhas...")
        row_count_result = execute_query(conn, QUERY_ROW_COUNT)
        total_rows = row_count_result[0][0] if row_count_result else 0

        # 3. Distribuição temporal
        log.info("Analisando distribuição temporal...")
        period_result = execute_query(conn, QUERY_ROWS_BY_PERIOD)
        period_distribution = {
            "last_30d": period_result[0][0] if period_result else 0,
            "last_60d": period_result[0][1] if period_result else 0,
            "last_90d": period_result[0][2] if period_result else 0,
            "last_180d": period_result[0][3] if period_result else 0,
            "total": period_result[0][4] if period_result else 0,
        }

        # 4. Top workflows
        log.info("Identificando top workflows...")
        top_workflows_result = execute_query(conn, QUERY_TOP_WORKFLOWS)
        top_workflows = [
            {
                "workflow_id": row[0],
                "exec_count_90d": row[1],
                "first_exec": row[2].isoformat() if row[2] else None,
                "last_exec": row[3].isoformat() if row[3] else None,
            }
            for row in top_workflows_result
        ]

        conn.close()

        # Consolidar resultado
        result = {
            "metadata": {
                "check_id": "POSTGRES-EXEC-ENTITY-2026-04-30",
                "checked_at": datetime.utcnow().isoformat() + "Z",
                "database": "n8n_db",
                "server": "wfdb02 (82.197.64.145:6432)",
            },
            "table_size": table_size,
            "row_count": {
                "total": total_rows,
                "vs_ana001_mar2026": {
                    "ana001_count": 429000,  # aproximado do ANA-001
                    "current_count": total_rows,
                    "growth": total_rows - 429000,
                    "growth_percent": round(((total_rows - 429000) / 429000) * 100, 1) if total_rows > 0 else 0,
                },
            },
            "distribution": period_distribution,
            "top_workflows_90d": top_workflows,
            "analysis": {
                "purgation_needed": total_rows > 500000,
                "growth_since_ana001": total_rows > 429000,
                "retention_policy_active": period_distribution["last_30d"] < period_distribution["total"] * 0.5,
            },
        }

        # Salvar JSON
        today = datetime.now().strftime("%Y-%m-%d")
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        session_dir = Path(f"docs/SESSIONS/{today}")
        session_dir.mkdir(parents=True, exist_ok=True)

        output_file = session_dir / f"postgres-execution-entity-{timestamp}.json"

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        log.info(f"✅ Verificação salva em: {output_file}")
        print(f"\n📊 Resultado: {output_file}")

        # Exibir resumo
        print("\n" + "=" * 80)
        print("RESUMO — execution_entity (n8n_db)")
        print("=" * 80)
        print(f"Total de linhas: {total_rows:,}")
        print(f"Tamanho total: {table_size['size_pretty']}")
        print(f"Últimos 30 dias: {period_distribution['last_30d']:,} linhas")
        print(f"Últimos 90 dias: {period_distribution['last_90d']:,} linhas")
        print(f"\nCrescimento desde ANA-001 (mar/2026):")
        print(f"  ANA-001: ~429.000 linhas")
        print(f"  Atual: {total_rows:,} linhas")
        print(f"  Crescimento: +{result['row_count']['vs_ana001_mar2026']['growth']:,} ({result['row_count']['vs_ana001_mar2026']['growth_percent']}%)")
        print(f"\n⚠️  Purgação necessária? {result['analysis']['purgation_needed']}")

    except Exception as e:
        log.error(f"Erro ao verificar PostgreSQL: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log.warning("Interrompido pelo usuário")
        sys.exit(1)

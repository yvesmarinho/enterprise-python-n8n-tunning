"""purge_execution_entity.py — Diagnóstico e purgação da tabela execution_entity do N8N.

Conecta ao PostgreSQL via psycopg2 e relata ou purga registros antigos da
tabela `execution_entity`. Usado como gate de validação para F17 (Vetor A).

Usage::

    # Apenas diagnóstico (não purga)
    python src/purge_execution_entity.py \\
        --db-host 82.197.64.145 --db-port 6432 --db-name n8n_db --check-only

    # Purgar registros mais antigos que 30 dias
    python src/purge_execution_entity.py \\
        --db-host 82.197.64.145 --db-port 6432 --db-name n8n_db \\
        --prune-older-than-days 30

Credenciais via variáveis de ambiente (NUNCA args):
    PG_USER, PG_PASSWORD

Exit codes:
    0 — sucesso
    1 — erro de conexão
    2 — erro de query

:author: enterprise-python-n8n-tunning
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone

log = logging.getLogger(__name__)

TABLE_NAME = "execution_entity"
SIZE_QUERY = (
    "SELECT pg_size_pretty(pg_total_relation_size(%s::regclass)), "
    "pg_total_relation_size(%s::regclass) / 1024.0 / 1024.0 AS size_mb"
)
COUNT_QUERY = f"SELECT COUNT(*) AS cnt FROM {TABLE_NAME}"  # noqa: S608
DELETE_QUERY = (
    f'DELETE FROM {TABLE_NAME} WHERE "startedAt" < NOW() - INTERVAL %s'  # noqa: S608
)


def _import_psycopg2():
    """Importa psycopg2 sob demanda.

    :returns: Módulo psycopg2.
    :raises SystemExit: Com código 1 se a dependência não estiver instalada.
    """
    try:
        import psycopg2  # noqa: PLC0415
    except ImportError:
        log.error("psycopg2-binary não instalado. Execute: pip install psycopg2-binary")
        sys.exit(1)

    return psycopg2


def get_connection(host: str, port: int, dbname: str):  # type: ignore[return]
    """Cria conexão psycopg2 usando credenciais de variáveis de ambiente.

    :param host: Host PostgreSQL.
    :param port: Porta PostgreSQL.
    :param dbname: Nome da database.
    :returns: Objeto de conexão psycopg2.
    :raises SystemExit: Com código 1 se psycopg2 não instalado ou conexão falha.

    >>> callable(get_connection)
    True
    """
    psycopg2 = _import_psycopg2()

    pg_user = os.environ.get("PG_USER", "n8n")
    pg_password = os.environ.get("PG_PASSWORD", "")

    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            dbname=dbname,
            user=pg_user,
            password=pg_password,
            connect_timeout=10,
        )
        conn.autocommit = False
        return conn
    except psycopg2.Error as exc:
        log.error("Erro ao conectar ao PostgreSQL: %s", exc)
        sys.exit(1)


def get_table_size_mb(cur, table: str) -> float:
    """Retorna o tamanho total da tabela em MB.

    :param cur: Cursor psycopg2.
    :param table: Nome da tabela.
    :returns: Tamanho em megabytes (float).
    """
    cur.execute(SIZE_QUERY, (table, table))
    row = cur.fetchone()
    return float(row[1]) if row else 0.0


def get_row_count(cur) -> int:
    """Retorna a contagem de linhas da tabela execution_entity.

    :param cur: Cursor psycopg2.
    :returns: Número de linhas.
    """
    cur.execute(COUNT_QUERY)
    row = cur.fetchone()
    return int(row[0]) if row else 0


def run_purge(cur, prune_days: int) -> int:
    """Executa DELETE das execuções mais antigas que prune_days.

    :param cur: Cursor psycopg2 (transação aberta).
    :param prune_days: Número de dias de retenção.
    :returns: Número de linhas deletadas.
    :raises SystemExit: Com código 2 em caso de erro de query.
    """
    psycopg2 = _import_psycopg2()

    try:
        cur.execute(DELETE_QUERY, (f"{prune_days} days",))
        return cur.rowcount
    except psycopg2.Error as exc:
        log.error("Erro na query de purgação: %s", exc)
        sys.exit(2)


def build_parser() -> argparse.ArgumentParser:
    """Constrói o parser CLI.

    :returns: ArgumentParser configurado.
    """
    p = argparse.ArgumentParser(
        description="Diagnóstico e purgação da tabela execution_entity do N8N."
    )
    p.add_argument(
        "--db-host", required=True, help="Host PostgreSQL (ex: 82.197.64.145)"
    )
    p.add_argument(
        "--db-port", type=int, default=6432, help="Porta PostgreSQL (default: 6432)"
    )
    p.add_argument("--db-name", required=True, help="Nome da database (ex: n8n_db)")
    p.add_argument(
        "--check-only",
        action="store_true",
        help="Apenas relata contagem e tamanho; não purga",
    )
    p.add_argument(
        "--prune-older-than-days",
        type=int,
        default=30,
        dest="prune_days",
        help="Purgar registros mais antigos que N dias (default: 30)",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    """Ponto de entrada principal.

    :param argv: Lista de argumentos (default: sys.argv[1:]).
    :returns: Código de saída (0, 1 ou 2).
    """
    logging.basicConfig(
        stream=sys.stderr, level=logging.INFO, format="%(levelname)s %(message)s"
    )
    args = build_parser().parse_args(argv)
    psycopg2 = _import_psycopg2()

    conn = get_connection(args.db_host, args.db_port, args.db_name)

    try:
        with conn.cursor() as cur:
            row_count_before = get_row_count(cur)
            size_before_mb = get_table_size_mb(cur, TABLE_NAME)

            rows_deleted = None
            row_count_after = None
            size_after_mb = None

            if not args.check_only:
                log.info(
                    "Purgando registros mais antigos que %d dias...", args.prune_days
                )
                rows_deleted = run_purge(cur, args.prune_days)
                conn.commit()
                row_count_after = get_row_count(cur)
                size_after_mb = get_table_size_mb(cur, TABLE_NAME)
                log.info("Purgação concluída — deletadas: %d linhas", rows_deleted)
            else:
                log.info(
                    "Modo check-only — contagem atual: %d linhas (%.1f MB)",
                    row_count_before,
                    size_before_mb,
                )

    except (psycopg2.Error, ValueError, TypeError) as exc:
        log.error("Erro inesperado: %s", exc)
        conn.rollback()
        sys.exit(2)
    finally:
        conn.close()

    result = {
        "table": TABLE_NAME,
        "row_count_before": row_count_before,
        "row_count_after": row_count_after,
        "rows_deleted": rows_deleted,
        "table_size_before_mb": round(size_before_mb, 2),
        "table_size_after_mb": (
            round(size_after_mb, 2) if size_after_mb is not None else None
        ),
        "checked_at": datetime.now(tz=timezone.utc).isoformat(),
        "check_only": args.check_only,
        "error": None,
    }

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())

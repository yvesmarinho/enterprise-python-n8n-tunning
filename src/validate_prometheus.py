"""validate_prometheus.py — Valida dupla coleta Prometheus e ProvenanceGate.

Conecta ao VictoriaMetrics e verifica se existe dupla coleta de métricas
(scrape direto + Pushgateway) para diagnóstico F18. Também suporta modo
``provenance-gate`` para confirmar que a correção foi aplicada.

Usage::

    # Detectar dupla coleta (padrão)
    python src/validate_prometheus.py \\
        --vm-url http://172.20.0.13:8428 \\
        --mode dual-collection \\
        --report \\
        --output docs/SESSIONS/2026-04-08/f18-dual-collection-report.json

    # ProvenanceGate via SSH tunnel para wf001 (T033r)
    # Abrir tunnel antes: ssh -N -L 18428:localhost:8428 -p 5010 archaris@31.220.103.208 &
    python src/validate_prometheus.py \\
        --vm-url http://localhost:18428 \\
        --mode provenance-gate \\
        --job-matcher 'collector_api_wf001_usa_ping_data' \\
        --db-host 82.197.64.145 --db-port 5432 --db-name n8n_db \\
        --report \\
        --output docs/SESSIONS/2026-04-08/f18-provenance-gate-wf001.json

Exit codes:
    0 — single scrape confirmado (dual-collection) ou ProvenanceGate PASS
    1 — dupla coleta ainda ativa ou ProvenanceGate FAIL
    2 — VictoriaMetrics inacessível

:author: enterprise-python-n8n-tunning
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

log = logging.getLogger(__name__)

# PromQL para detectar jobs distintos que exportam métricas n8n_*.
N8N_METRIC_JOBS_QUERY = 'count by (job)({__name__=~"n8n_.*"})'

# Matcher padrão — genérico para dual-collection em wfdb01.
# Para ProvenanceGate em wf001, usar --job-matcher 'collector_api_wf001_usa_ping_data'.
DEFAULT_PUSHGATEWAY_JOB_MATCHER = 'job=~".*pushgateway.*|.*push.*"'

EXECUTION_COUNT_QUERY = "n8n_workflow_executions_total"
# Janela para cross-check de delta execuções (PG vs VM)
EXECUTION_DELTA_WINDOW = "30m"
EXECUTION_DELTA_TOLERANCE_PCT = 5.0


def vm_query(vm_url: str, promql: str, timeout: int = 15) -> dict:
    """Executa uma query instantânea no VictoriaMetrics.

    :param vm_url: URL base do VictoriaMetrics.
    :param promql: Expressão PromQL.
    :param timeout: Timeout HTTP em segundos.
    :returns: Dict com ``result`` e ``resultType`` ou ``{"error": ...}``.

    >>> callable(vm_query)
    True
    """
    endpoint = f"{vm_url.rstrip('/')}/api/v1/query"
    params = urllib.parse.urlencode({"query": promql})
    url = f"{endpoint}?{params}"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:  # noqa: S310
            data = json.loads(resp.read())
            return data.get("data", {})
    except TimeoutError:
        return {"error": "timeout"}
    except urllib.error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        return {"error": f"HTTP {exc.code}: {details}"}
    except urllib.error.URLError as exc:
        return {"error": str(exc)}


def detect_dual_collection(vm_url: str, lookback: str) -> dict:
    """Detecta dupla coleta via presença de séries Pushgateway.

    :param vm_url: URL do VictoriaMetrics.
    :param lookback: Janela de lookback (ex: ``1h``).
    :returns: Dict com resultado da detecção.

    >>> callable(detect_dual_collection)
    True
    """
    del lookback

    data = vm_query(vm_url, N8N_METRIC_JOBS_QUERY)

    if "error" in data:
        return {
            "vm_accessible": False,
            "pushgateway_series_found": [],
            "n8n_metric_jobs_found": [],
            "direct_scrape_series_count": 0,
            "dual_collection_active": False,
            "verdict": "NO_DATA",
            "error": data["error"],
        }

    series = data.get("result", [])
    n8n_metric_jobs = []
    for item in series:
        metric = item.get("metric", {})
        try:
            series_count = int(float(item["value"][1]))
        except (KeyError, IndexError, TypeError, ValueError):
            series_count = 0
        n8n_metric_jobs.append(
            {"job": metric.get("job", ""), "series_count": series_count}
        )

    _push_query = f"count by (job)({{{DEFAULT_PUSHGATEWAY_JOB_MATCHER}}})"
    push_data = vm_query(vm_url, _push_query)
    pushgateway_labels = []
    if "result" in push_data:
        pushgateway_labels = [s.get("metric", {}) for s in push_data["result"]]

    # Contar séries de scrape direto
    direct_data = vm_query(vm_url, 'count({job!="pushgateway"})')
    direct_count = 0
    if "result" in direct_data and direct_data["result"]:
        try:
            direct_count = int(float(direct_data["result"][0]["value"][1]))
        except (KeyError, IndexError, ValueError):
            pass

    dual_active = len(n8n_metric_jobs) > 1
    verdict = "DUAL_COLLECTION" if dual_active else "SINGLE_SCRAPE"

    return {
        "vm_accessible": True,
        "pushgateway_series_found": pushgateway_labels,
        "n8n_metric_jobs_found": n8n_metric_jobs,
        "direct_scrape_series_count": direct_count,
        "dual_collection_active": dual_active,
        "verdict": verdict,
        "error": None,
    }


def run_provenance_gate(
    vm_url: str,
    db_host: str,
    db_port: int,
    db_name: str,
    job_matcher: str | None = None,
) -> dict:
    """Valida que a correção foi aplicada (ProvenanceGate).

    Verifica:
    1. Job Pushgateway/collector ausente por ≥1h (``absent_over_time``).
    2. Delta de execuções na janela de 30min entre PostgreSQL e VM ≤5%.

    :param vm_url: URL do VictoriaMetrics (pode ser localhost via SSH tunnel).
    :param db_host: Host PostgreSQL.
    :param db_port: Porta PostgreSQL.
    :param db_name: Nome da database.
    :param job_matcher: Label matcher PromQL para identificar o job a verificar.
        Usar valor específico (ex: ``collector_api_wf001_usa_ping_data``) para
        wf001. Se None, usa ``DEFAULT_PUSHGATEWAY_JOB_MATCHER``.
    :returns: Dict com resultado do ProvenanceGate.
    """
    matcher = job_matcher or DEFAULT_PUSHGATEWAY_JOB_MATCHER
    # Distinguir entre matcher exato (sem =~) e regex
    if "=~" in matcher or "!=" in matcher:
        absent_query = f"absent_over_time({{{matcher}}}[1h])"
    else:
        absent_query = f'absent_over_time({{job="{matcher}"}}[1h])'

    # 1. Job ausente por 1h
    absent_data = vm_query(vm_url, absent_query)
    if "error" in absent_data:
        return {
            "verdict": "PROVENANCE_FAIL",
            "provenance_gate": {
                "pushgateway_absent_1h": False,
                "execution_count_coherent": False,
                "count_delta_pct": None,
            },
            "job_matcher_used": matcher,
            "error": absent_data["error"],
        }

    absent_result = absent_data.get("result", [])
    pushgateway_absent_1h = len(absent_result) > 0

    # 2. Cross-check PostgreSQL via delta de janela curta (30min)
    pg_count = _get_pg_execution_count_window(db_host, db_port, db_name, window_minutes=30)
    vm_count = _get_vm_execution_count_window(vm_url, window=EXECUTION_DELTA_WINDOW)

    coherent = False
    delta_pct = None
    if pg_count is not None and vm_count is not None and pg_count > 0:
        delta_pct = abs(pg_count - vm_count) / pg_count * 100.0
        coherent = delta_pct <= EXECUTION_DELTA_TOLERANCE_PCT
    elif pg_count is not None and vm_count is None:
        # VM sem dados na janela (N8N idle) — considerar coerente
        coherent = pg_count == 0

    gate_pass = pushgateway_absent_1h and coherent
    verdict = "PROVENANCE_OK" if gate_pass else "PROVENANCE_FAIL"

    return {
        "verdict": verdict,
        "provenance_gate": {
            "pushgateway_absent_1h": pushgateway_absent_1h,
            "execution_count_coherent": coherent,
            "count_delta_pct": round(delta_pct, 4) if delta_pct is not None else None,
            "delta_window": EXECUTION_DELTA_WINDOW,
            "delta_tolerance_pct": EXECUTION_DELTA_TOLERANCE_PCT,
        },
        "job_matcher_used": matcher,
        "error": None,
    }


def _pg_connect(host: str, port: int, dbname: str):
    """Retorna conexão psycopg2 ou None se psycopg2 não instalado.

    :param host: Host PostgreSQL.
    :param port: Porta PostgreSQL.
    :param dbname: Nome da database.
    :returns: Conexão psycopg2 ou None.
    """
    try:
        import psycopg2  # noqa: PLC0415
    except ImportError:
        log.warning("psycopg2 não instalado — cross-check PostgreSQL ignorado")
        return None

    pg_user = os.environ.get("PG_USER", "n8n")
    pg_password = os.environ.get("PG_PASSWORD", "")
    try:
        import psycopg2  # noqa: PLC0415
        return psycopg2.connect(
            host=host,
            port=port,
            dbname=dbname,
            user=pg_user,
            password=pg_password,
            connect_timeout=10,
        )
    except Exception as exc:  # noqa: BLE001
        log.warning("Erro ao conectar ao PostgreSQL: %s", exc)
        return None


def _get_pg_execution_count(host: str, port: int, dbname: str) -> int | None:
    """Consulta contagem total de execution_entity no PostgreSQL.

    :param host: Host PostgreSQL.
    :param port: Porta PostgreSQL.
    :param dbname: Nome da database.
    :returns: Contagem ou None em caso de falha.
    """
    conn = _pg_connect(host, port, dbname)
    if conn is None:
        return None
    try:
        import psycopg2  # noqa: PLC0415
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM execution_entity")  # noqa: S608
            row = cur.fetchone()
            return int(row[0]) if row else None
    except (psycopg2.Error, TypeError, ValueError) as exc:
        log.warning("Erro ao consultar PostgreSQL: %s", exc)
        return None
    finally:
        conn.close()


def _get_pg_execution_count_window(
    host: str, port: int, dbname: str, window_minutes: int = 30
) -> int | None:
    """Conta execuções iniciadas na janela recente (delta cross-check).

    Usa janela curta para evitar divergência por resets do contador do VM.

    :param host: Host PostgreSQL.
    :param port: Porta PostgreSQL.
    :param dbname: Nome da database.
    :param window_minutes: Janela em minutos (default: 30).
    :returns: Contagem ou None em caso de falha.
    """
    conn = _pg_connect(host, port, dbname)
    if conn is None:
        return None
    try:
        import psycopg2  # noqa: PLC0415
        with conn.cursor() as cur:
            cur.execute(  # noqa: S608
                "SELECT COUNT(*) FROM execution_entity "
                "WHERE \"startedAt\" > NOW() - INTERVAL '%s minutes'",
                (window_minutes,),
            )
            row = cur.fetchone()
            return int(row[0]) if row else None
    except (psycopg2.Error, TypeError, ValueError) as exc:
        log.warning("Erro ao consultar PostgreSQL (janela): %s", exc)
        return None
    finally:
        conn.close()


def _get_vm_execution_count(vm_url: str) -> int | None:
    """Obtém contagem total de execuções do VictoriaMetrics (valor instantâneo).

    :param vm_url: URL do VictoriaMetrics.
    :returns: Valor inteiro ou None se não disponível.
    """
    data = vm_query(vm_url, EXECUTION_COUNT_QUERY)
    if "result" not in data or not data["result"]:
        return None
    try:
        return int(float(data["result"][0]["value"][1]))
    except (KeyError, IndexError, ValueError):
        return None


def _get_vm_execution_count_window(vm_url: str, window: str = "30m") -> int | None:
    """Soma incrementos de execuções do VictoriaMetrics na janela recente.

    Usa ``increase()`` para evitar divergência por resets do contador.

    :param vm_url: URL do VictoriaMetrics.
    :param window: Janela PromQL (default: ``30m``).
    :returns: Valor inteiro ou None se não disponível.
    """
    query = f"sum(increase({EXECUTION_COUNT_QUERY}[{window}]))"
    data = vm_query(vm_url, query)
    if "result" not in data or not data["result"]:
        return None
    try:
        val = float(data["result"][0]["value"][1])
        return max(0, int(val))
    except (KeyError, IndexError, ValueError):
        return None


def build_parser() -> argparse.ArgumentParser:
    """Constrói o parser CLI.

    :returns: ArgumentParser configurado.
    """
    p = argparse.ArgumentParser(
        description="Valida dupla coleta Prometheus (F18) e ProvenanceGate."
    )
    p.add_argument(
        "--vm-url",
        required=True,
        help="URL base do VictoriaMetrics (ex: http://86.48.31.149:8428)",
    )
    p.add_argument(
        "--lookback",
        default="1h",
        help="Janela de lookback PromQL (default: 1h)",
    )
    p.add_argument(
        "--report",
        action="store_true",
        help="Gerar relatório JSON completo (default: apenas verdict)",
    )
    p.add_argument(
        "--output",
        help="Arquivo de saída para relatório JSON (default: stdout)",
    )
    p.add_argument(
        "--mode",
        choices=["dual-collection", "provenance-gate"],
        default="dual-collection",
        help="Modo de validação (default: dual-collection)",
    )
    p.add_argument(
        "--db-host", help="Host PostgreSQL (necessário no modo provenance-gate)"
    )
    p.add_argument(
        "--db-port", type=int, default=6432, help="Porta PostgreSQL (default: 6432)"
    )
    p.add_argument(
        "--db-name", help="Nome da database (necessário no modo provenance-gate)"
    )
    p.add_argument(
        "--job-matcher",
        default=None,
        help=(
            "Label matcher PromQL para identificar o job Pushgateway/collector. "
            "Sem operador (ex: 'collector_api_wf001_usa_ping_data') = match exato. "
            "Com operador (ex: 'job=~\".*push.*\"') = expressão completa. "
            "Default: '" + DEFAULT_PUSHGATEWAY_JOB_MATCHER + "'"
        ),
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

    if args.mode == "provenance-gate" and not (args.db_host and args.db_name):
        log.error("--db-host e --db-name são obrigatórios no modo provenance-gate")
        return 1

    log.info("Modo: %s | vm-url: %s", args.mode, args.vm_url)

    if args.mode == "dual-collection":
        result_data = detect_dual_collection(args.vm_url, args.lookback)
        if result_data.get("error") == "timeout" or not result_data.get(
            "vm_accessible", True
        ):
            log.error("VictoriaMetrics inacessível: %s", result_data.get("error"))
            return 2
    else:
        result_data = run_provenance_gate(
            args.vm_url,
            args.db_host,  # type: ignore[arg-type]
            args.db_port,
            args.db_name,  # type: ignore[arg-type]
            job_matcher=args.job_matcher,
        )
        if (
            result_data.get("error")
            and "inacess" in str(result_data.get("error", "")).lower()
        ):
            return 2

    payload: dict = {
        "mode": args.mode,
        "checked_at": datetime.now(tz=timezone.utc).isoformat(),
        **result_data,
    }

    output = json.dumps(payload, indent=2, ensure_ascii=False)
    print(output)

    if args.output:
        from pathlib import Path  # noqa: PLC0415

        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(output, encoding="utf-8")
        log.info("Relatório salvo em: %s", args.output)

    verdict = payload.get("verdict", "")
    if verdict in ("SINGLE_SCRAPE", "PROVENANCE_OK"):
        log.info("✓ %s", verdict)
        return 0

    log.warning("✗ %s", verdict)
    return 1


if __name__ == "__main__":
    sys.exit(main())

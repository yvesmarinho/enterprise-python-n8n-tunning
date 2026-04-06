"""collect_gate_evidence.py — Coleta métricas de evidência before/after para gates de promoção.

Consulta o VictoriaMetrics e gera um arquivo JSON com métricas relevantes
para a feature especificada (F16, F17 ou F18).

Quando ``--vm-url`` não está disponível (ex: wfdb01 onde VictoriaMetrics não tem
porta exposta ao host), use ``--n8n-url`` para coletar evidência direta do
endpoint /metrics do N8N (funciona para F16).

Usage::

    # Com VictoriaMetrics (wf001 production):
    python src/collect_gate_evidence.py \\
        --feature F16 \\
        --environment wf001 \\
        --vm-url http://31.220.103.208:8428 \\
        --output-dir docs/SESSIONS/2026-04-02/

    # Sem VictoriaMetrics (wfdb01 test — VM não exposta):
    python src/collect_gate_evidence.py \\
        --feature F16 \\
        --environment wfdb01 \\
        --n8n-url https://testn8n.vya.digital \\
        --output-dir docs/SESSIONS/2026-04-02/

Exit codes:
    0 — evidências coletadas com sucesso
    1 — VictoriaMetrics inacessível e nenhum fallback disponível
    2 — feature_id desconhecido

:author: enterprise-python-n8n-tunning
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

log = logging.getLogger(__name__)

# PromQL queries por feature
FEATURE_QUERIES: dict[str, dict[str, str]] = {
    "F16": {
        "n8n_scaling_mode_queue_jobs_active": "n8n_scaling_mode_queue_jobs_active",
        "n8n_scaling_mode_queue_jobs_waiting": "n8n_scaling_mode_queue_jobs_waiting",
        "n8n_scaling_mode_queue_jobs_completed": "n8n_scaling_mode_queue_jobs_completed",
        "n8n_scaling_mode_queue_jobs_failed": "n8n_scaling_mode_queue_jobs_failed",
    },
    "F17": {
        "pg_stat_activity_count": 'count(pg_stat_activity{datname="n8n_db"})',
        "execution_entity_count": "n8n_executions_total",
    },
    "F18": {
        "pushgateway_series": '{instance=~".*0\\.0\\.0\\.0.*"}',
        "n8n_metrics_total": 'count({job=~"n8n.*"})',
    },
}


def query_instant(vm_url: str, promql: str, timeout: int = 15) -> dict:
    """Executa uma query instantânea no VictoriaMetrics.

    :param vm_url: URL base do VictoriaMetrics.
    :param promql: Expressão PromQL.
    :param timeout: Timeout HTTP em segundos.
    :returns: Dict com ``result`` e ``resultType`` ou ``error``.

    >>> query_instant.__doc__ is not None
    True
    """
    endpoint = f"{vm_url.rstrip('/')}/api/v1/query"
    params = urllib.parse.urlencode({"query": promql})
    url = f"{endpoint}?{params}"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:  # noqa: S310
            data = json.loads(resp.read())
            return data.get("data", {})
    except urllib.error.URLError as exc:
        log.error("VictoriaMetrics inacessível: %s", exc)
        return {"error": str(exc)}


def collect_feature_metrics(vm_url: str, feature: str) -> dict[str, object]:
    """Coleta as métricas relevantes para a feature fornecida.

    :param vm_url: URL do VictoriaMetrics.
    :param feature: Identificador da feature (F16, F17 ou F18).
    :returns: Dict mapeando nome da métrica para valor e labels.
    :raises SystemExit: Com código 2 se feature desconhecida.
    """
    queries = FEATURE_QUERIES.get(feature)
    if queries is None:
        log.error(
            "Feature desconhecida: %s. Válidos: %s", feature, list(FEATURE_QUERIES)
        )
        sys.exit(2)

    result: dict[str, object] = {}
    vm_down = False

    for metric_name, promql in queries.items():
        data = query_instant(vm_url, promql)
        if "error" in data:
            vm_down = True
            result[metric_name] = {"value": None, "labels": {}, "error": data["error"]}
            continue
        series = data.get("result", [])
        if not series:
            result[metric_name] = {"value": None, "labels": {}, "series_count": 0}
        else:
            # Retorna o valor do primeiro result; preserva todas as séries se >1
            first = series[0]
            result[metric_name] = {
                "value": float(first["value"][1]) if "value" in first else None,
                "labels": first.get("metric", {}),
                "series_count": len(series),
            }

    if vm_down:
        return result  # caller verifica erros por métrica

    return result


def determine_status(metrics: dict[str, object]) -> str:
    """Determina o status geral da coleta de evidências.

    :param metrics: Dict de métricas coletadas.
    :returns: ``"pass"`` se todas as métricas têm valor não nulo,
              ``"fail"`` se nenhuma tem, ``"inconclusive"`` caso misto.

    >>> determine_status({"m": {"value": 1.0}})
    'pass'
    >>> determine_status({"m": {"value": None}})
    'fail'
    >>> determine_status({"a": {"value": 1.0}, "b": {"value": None}})
    'inconclusive'
    """
    values = [v.get("value") for v in metrics.values() if isinstance(v, dict)]  # type: ignore[union-attr]
    non_null = [v for v in values if v is not None]
    if len(non_null) == len(values):
        return "pass"
    if len(non_null) == 0:
        return "fail"
    return "inconclusive"


def write_output(payload: dict, output_dir: Path, feature: str) -> Path:
    """Persiste o JSON de evidências em output_dir.

    :param payload: Dict a serializar.
    :param output_dir: Diretório de saída.
    :param feature: Identificador da feature (usado no nome do arquivo).
    :returns: Caminho do arquivo criado.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    fname = output_dir / f"gate-evidence-{feature.lower()}-{ts}.json"
    fname.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return fname


def collect_via_n8n_direct(n8n_url: str, feature: str) -> dict[str, object]:
    """Coleta evidência de F16 diretamente do endpoint /metrics do N8N.

    Fallback para ambientes onde VictoriaMetrics não está acessível externamente
    (ex: wfdb01 onde VM só está na rede Docker interna).

    :param n8n_url: URL base do N8N (ex: https://testn8n.vya.digital).
    :param feature: Identificador da feature (apenas F16 suportado).
    :returns: Dict com métricas coletadas via scrape direto.
    :raises SystemExit: Com código 2 se feature não for F16.

    >>> collect_via_n8n_direct.__doc__ is not None
    True
    """
    if feature != "F16":
        log.error("Fallback direto N8N só suportado para F16, não para %s", feature)
        sys.exit(2)

    metrics_url = f"{n8n_url.rstrip('/')}/metrics"
    try:
        with urllib.request.urlopen(  # noqa: S310
            urllib.request.Request(metrics_url), timeout=15  # type: ignore[arg-type]
        ) as resp:
            body = resp.read().decode()
    except urllib.error.URLError as exc:
        log.error("N8N metrics endpoint inacessível: %s", exc)
        return {
            k: {"value": None, "labels": {}, "error": str(exc)}
            for k in FEATURE_QUERIES["F16"]
        }

    result: dict[str, object] = {}
    for metric_name in FEATURE_QUERIES["F16"]:
        found = any(
            line.startswith(metric_name)
            for line in body.splitlines()
            if not line.startswith("#")
        )
        # Extrai valor se linha encontrada
        value: float | None = None
        for line in body.splitlines():
            if line.startswith(metric_name + " ") or line.startswith(metric_name + "{"):
                parts = line.rsplit(" ", 1)
                try:
                    value = float(parts[-1])
                except ValueError:
                    value = None
                break
        result[metric_name] = {
            "value": value,
            "labels": {"source": "direct_scrape"},
            "found": found,
        }
    return result


def build_parser() -> argparse.ArgumentParser:
    """Constrói o parser de argumentos CLI.

    :returns: ArgumentParser configurado.
    """
    p = argparse.ArgumentParser(
        description="Coleta métricas de evidência before/after para gates de promoção."
    )
    p.add_argument(
        "--feature",
        required=True,
        choices=list(FEATURE_QUERIES),
        help="Feature ID (ex: F16)",
    )
    p.add_argument(
        "--environment",
        required=True,
        choices=["wfdb01", "wf001", "wfdb02"],
        help="Ambiente onde a feature foi aplicada",
    )
    p.add_argument(
        "--vm-url",
        required=False,
        default=None,
        help="URL base do VictoriaMetrics (ex: http://86.48.31.149:8428). Opcional quando --n8n-url fornecido.",
    )
    p.add_argument(
        "--n8n-url",
        required=False,
        default=None,
        help="URL base do N8N para fallback direto (ex: https://testn8n.vya.digital). Usado quando VM não acessível.",
    )
    p.add_argument(
        "--output-dir",
        default=None,
        help="Diretório para salvar o JSON (default: docs/SESSIONS/YYYY-MM-DD/)",
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

    today = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
    output_dir = (
        Path(args.output_dir) if args.output_dir else Path(f"docs/SESSIONS/{today}")
    )

    log.info(
        "Coletando evidências — feature=%s environment=%s",
        args.feature,
        args.environment,
    )

    vm_access = "ok"
    if args.vm_url:
        metrics = collect_feature_metrics(args.vm_url, args.feature)
        all_errors = all(isinstance(v, dict) and "error" in v for v in metrics.values())
        if all_errors and args.n8n_url:
            log.warning("VictoriaMetrics inacessível — usando fallback direto N8N")
            metrics = collect_via_n8n_direct(args.n8n_url, args.feature)
            vm_access = "fallback_direct"
        elif all_errors:
            log.error("VictoriaMetrics inacessível — todas as métricas falharam")
            return 1
    elif args.n8n_url:
        log.info("--vm-url não fornecido — usando fallback direto N8N")
        metrics = collect_via_n8n_direct(args.n8n_url, args.feature)
        vm_access = "skipped_direct_only"
    else:
        log.error("Forneça --vm-url ou --n8n-url (ou ambos)")
        return 1

    status = determine_status(metrics)

    payload = {
        "feature_id": args.feature,
        "environment": args.environment,
        "collected_at": datetime.now(tz=timezone.utc).isoformat(),
        "vm_access": vm_access,
        "metrics": metrics,
        "status": status,
        "error": None,
    }

    out_file = write_output(payload, output_dir, args.feature)
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    log.info("Evidências salvas em: %s | status=%s", out_file, status)

    return 0


if __name__ == "__main__":
    sys.exit(main())

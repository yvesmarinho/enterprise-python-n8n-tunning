"""check_n8n_metrics.py — Verifica presença de métricas N8N no endpoint /metrics.

Conecta-se ao endpoint HTTPS `/metrics` do N8N (via Traefik) e valida quais
métricas de fila estão presentes. Usado como gate de validação pós-execução
do playbook F16.

Usage::

    python src/check_n8n_metrics.py --metrics-url https://testn8n.vya.digital
    python src/check_n8n_metrics.py --metrics-url https://testn8n.vya.digital --timeout 30

Exit codes:
    0 — todas as métricas esperadas presentes
    1 — métricas ausentes ou endpoint inacessível
    2 — timeout

:author: enterprise-python-n8n-tunning
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

log = logging.getLogger(__name__)

# Métricas de fila esperadas após F16 (N8N 2.x queue mode — nomes reais)
EXPECTED_QUEUE_METRICS: list[str] = [
    "n8n_scaling_mode_queue_jobs_active",
    "n8n_scaling_mode_queue_jobs_waiting",
    "n8n_scaling_mode_queue_jobs_completed",
    "n8n_scaling_mode_queue_jobs_failed",
]


def fetch_metrics(base_url: str, timeout: int) -> tuple[str | None, str | None]:
    """Busca o conteúdo do endpoint /metrics do N8N.

    :param base_url: URL base do servidor N8N (ex: https://testn8n.vya.digital).
    :param timeout: Timeout HTTP em segundos.
    :returns: Tupla ``(body, error)``. Exatamente um dos dois é None.

    >>> # Sem rede: apenas valida a assinatura
    >>> callable(fetch_metrics)
    True
    """
    url = f"{base_url.rstrip('/')}/metrics"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:  # noqa: S310
            return resp.read().decode("utf-8"), None
    except TimeoutError:
        return None, "timeout"
    except urllib.error.URLError as exc:
        if "timed out" in str(exc).lower():
            return None, "timeout"
        return None, str(exc)


def parse_metric_names(body: str) -> list[str]:
    """Extrai nomes de métricas (linhas que não são comentários) do formato Prometheus.

    :param body: Corpo do endpoint /metrics em formato text/plain.
    :returns: Lista de nomes de métricas encontradas.

    >>> parse_metric_names("# HELP n8n_queue_depth queue depth\\n# TYPE n8n_queue_depth gauge\\nn8n_queue_depth 0\\n")
    ['n8n_queue_depth']
    >>> parse_metric_names("")
    []
    """
    names: set[str] = set()
    for line in body.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        name = line.split("{")[0].split(" ")[0]
        if name:
            names.add(name)
    return sorted(names)


def check_metrics(url: str, timeout: int) -> dict:
    """Verifica quais métricas de fila esperadas estão presentes.

    :param url: URL base do servidor N8N (ex: https://testn8n.vya.digital).
    :param timeout: Timeout HTTP em segundos.
    :returns: Dict com resultado da verificação.
    """
    body, err = fetch_metrics(url, timeout)
    if err == "timeout":
        return {
            "url": url,
            "status": "fail",
            "metrics_found": [],
            "metrics_missing": EXPECTED_QUEUE_METRICS,
            "raw_count": 0,
            "checked_at": datetime.now(tz=timezone.utc).isoformat(),
            "error": "timeout",
        }
    if err:
        return {
            "url": url,
            "status": "fail",
            "metrics_found": [],
            "metrics_missing": EXPECTED_QUEUE_METRICS,
            "raw_count": 0,
            "checked_at": datetime.now(tz=timezone.utc).isoformat(),
            "error": err,
        }

    all_names = parse_metric_names(body)
    found = [m for m in EXPECTED_QUEUE_METRICS if m in all_names]
    missing = [m for m in EXPECTED_QUEUE_METRICS if m not in all_names]

    return {
        "url": url,
        "status": "pass" if not missing else "fail",
        "metrics_found": found,
        "metrics_missing": missing,
        "raw_count": len(all_names),
        "checked_at": datetime.now(tz=timezone.utc).isoformat(),
        "error": None,
    }


def build_parser() -> argparse.ArgumentParser:
    """Constrói o parser CLI.

    :returns: ArgumentParser configurado.
    """
    p = argparse.ArgumentParser(
        description="Verifica métricas de fila N8N no endpoint /metrics."
    )
    p.add_argument(
        "--metrics-url",
        required=True,
        dest="metrics_url",
        help="URL base do servidor N8N (ex: https://testn8n.vya.digital)",
    )
    p.add_argument(
        "--timeout", type=int, default=10, help="Timeout HTTP em segundos (default: 10)"
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

    log.info("Verificando métricas em %s", args.metrics_url)
    result = check_metrics(args.metrics_url, args.timeout)

    print(json.dumps(result, indent=2, ensure_ascii=False))

    if result["error"] == "timeout":
        return 2
    if result["status"] == "fail":
        if result["error"]:
            log.error("Endpoint inacessível: %s", result["error"])
        else:
            log.warning("Métricas ausentes: %s", result["metrics_missing"])
        return 1

    log.info("Todas as métricas encontradas: %s", result["metrics_found"])
    return 0


if __name__ == "__main__":
    sys.exit(main())

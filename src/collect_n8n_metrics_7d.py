#!/usr/bin/env python3
"""
Coleta de métricas N8N via VictoriaMetrics — últimos 7 dias.

Consulta VictoriaMetrics em wfdb01 para coletar:
- Volume de execuções por workflow (n8n_workflow_executions_total)
- Latência de execução por workflow (n8n_workflow_execution_duration_seconds)
- Cruzamento: workflows ofensores por duração × volume

Saída: JSON em docs/SESSIONS/YYYY-MM-DD/n8n-metrics-7d-YYYYMMDD-HHMMSS.json

Exemplos
--------
>>> # Executar coleta
>>> python src/collect_n8n_metrics_7d.py
>>> # Ou via uv:
>>> uv run python src/collect_n8n_metrics_7d.py
"""

import json
import logging
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


def query_victoriametrics(vm_url: str, query: str, start: str, end: str, step: str = "5m") -> dict[str, Any]:
    """
    Consulta VictoriaMetrics via API range_query.

    Parameters
    ----------
    vm_url : str
        URL base do VictoriaMetrics (ex: http://172.20.0.13:8428)
    query : str
        PromQL query
    start : str
        Timestamp início (ISO 8601 ou Unix)
    end : str
        Timestamp fim (ISO 8601 ou Unix)
    step : str, optional
        Intervalo de agregação (padrão: 5m)

    Returns
    -------
    dict
        Resposta JSON do VictoriaMetrics

    Examples
    --------
    >>> query_victoriametrics("http://172.20.0.13:8428", "up", "2026-04-23T00:00:00Z", "2026-04-30T00:00:00Z")
    {'status': 'success', 'data': {...}}
    """
    import urllib.parse
    import urllib.request

    params = {
        "query": query,
        "start": start,
        "end": end,
        "step": step,
    }
    url = f"{vm_url}/api/v1/query_range?{urllib.parse.urlencode(params)}"

    log.info(f"Query VictoriaMetrics: {query[:80]}...")

    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            data = json.loads(response.read().decode())
            if data.get("status") != "success":
                log.error(f"VictoriaMetrics query failed: {data}")
                return {"status": "error", "data": {}}
            return data
    except Exception as e:
        log.error(f"Failed to query VictoriaMetrics: {e}")
        return {"status": "error", "data": {}, "error": str(e)}


def collect_workflow_volume(vm_url: str, start: str, end: str) -> list[dict]:
    """
    Coleta volume de execuções por workflow (últimos 7 dias).

    Query: increase(n8n_workflow_executions_total{instance='wf001'}[7d])

    Returns
    -------
    list[dict]
        Lista de workflows com volume total de execuções
    """
    query = 'increase(n8n_workflow_executions_total{instance="wf001"}[7d])'
    result = query_victoriametrics(vm_url, query, start, end, step="7d")

    workflows = []
    if result.get("status") == "success":
        for series in result.get("data", {}).get("result", []):
            metric = series.get("metric", {})
            values = series.get("values", [])

            if values:
                # Pegar o último valor (total do período)
                total_executions = float(values[-1][1]) if len(values[-1]) > 1 else 0.0

                workflows.append({
                    "workflow_name": metric.get("workflow_name", "unknown"),
                    "workflow_id": metric.get("workflow_id", "unknown"),
                    "instance": metric.get("instance", "unknown"),
                    "total_executions_7d": int(total_executions),
                })

    # Ordenar por volume decrescente
    workflows.sort(key=lambda x: x["total_executions_7d"], reverse=True)
    return workflows


def collect_workflow_latency(vm_url: str, start: str, end: str) -> list[dict]:
    """
    Coleta latência média de execução por workflow (últimos 7 dias).

    Query:
    - rate(n8n_workflow_execution_duration_seconds_sum[7d])
    / rate(n8n_workflow_execution_duration_seconds_count[7d])

    Returns
    -------
    list[dict]
        Lista de workflows com latência média em segundos
    """
    query = '''
    rate(n8n_workflow_execution_duration_seconds_sum{instance="wf001"}[7d])
    /
    rate(n8n_workflow_execution_duration_seconds_count{instance="wf001"}[7d])
    '''
    result = query_victoriametrics(vm_url, query, start, end, step="7d")

    latencies = []
    if result.get("status") == "success":
        for series in result.get("data", {}).get("result", []):
            metric = series.get("metric", {})
            values = series.get("values", [])

            if values:
                avg_latency = float(values[-1][1]) if len(values[-1]) > 1 else 0.0

                latencies.append({
                    "workflow_name": metric.get("workflow_name", "unknown"),
                    "workflow_id": metric.get("workflow_id", "unknown"),
                    "instance": metric.get("instance", "unknown"),
                    "avg_latency_seconds": round(avg_latency, 3),
                })

    # Ordenar por latência decrescente
    latencies.sort(key=lambda x: x["avg_latency_seconds"], reverse=True)
    return latencies


def merge_workflow_metrics(volume: list[dict], latency: list[dict]) -> list[dict]:
    """
    Cruza volume × latência para identificar workflows ofensores.

    Calcula impacto = total_executions × avg_latency (tempo total gasto)

    Parameters
    ----------
    volume : list[dict]
        Workflows com volume de execuções
    latency : list[dict]
        Workflows com latência média

    Returns
    -------
    list[dict]
        Workflows com volume, latência e impacto calculado
    """
    # Indexar latências por workflow_id
    latency_map = {item["workflow_id"]: item for item in latency}

    merged = []
    for vol in volume:
        wf_id = vol["workflow_id"]
        lat = latency_map.get(wf_id, {})

        avg_lat = lat.get("avg_latency_seconds", 0.0)
        total_exec = vol["total_executions_7d"]

        # Impacto = tempo total gasto (execuções × latência média)
        impact = total_exec * avg_lat

        merged.append({
            "workflow_name": vol["workflow_name"],
            "workflow_id": wf_id,
            "instance": vol["instance"],
            "total_executions_7d": total_exec,
            "avg_latency_seconds": avg_lat,
            "total_impact_seconds": round(impact, 2),
        })

    # Ordenar por impacto decrescente
    merged.sort(key=lambda x: x["total_impact_seconds"], reverse=True)
    return merged


def main() -> None:
    """
    Coleta métricas N8N dos últimos 7 dias e salva em JSON.

    Conecta ao VictoriaMetrics em wfdb01 (via IP interno Docker 172.20.0.13:8428)
    e coleta volume, latência e impacto por workflow.

    Saída salva em: docs/SESSIONS/YYYY-MM-DD/n8n-metrics-7d-YYYYMMDD-HHMMSS.json
    """
    log.info("=== Coleta de Métricas N8N — Últimos 7 Dias ===")

    # Configuração VictoriaMetrics
    # NOTA: IP interno Docker wfdb01 — acessível via SSH tunnel ou dentro da rede Docker
    vm_url = "http://172.20.0.13:8428"

    # Janela temporal: últimos 7 dias
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=7)

    start_iso = start_time.strftime("%Y-%m-%dT%H:%M:%SZ")
    end_iso = end_time.strftime("%Y-%m-%dT%H:%M:%SZ")

    log.info(f"Período: {start_iso} → {end_iso}")
    log.info(f"VictoriaMetrics URL: {vm_url}")

    # Coletar volume de execuções
    log.info("Coletando volume de execuções por workflow...")
    volume = collect_workflow_volume(vm_url, start_iso, end_iso)
    log.info(f"  → {len(volume)} workflows com dados de volume")

    # Coletar latência média
    log.info("Coletando latência média por workflow...")
    latency = collect_workflow_latency(vm_url, start_iso, end_iso)
    log.info(f"  → {len(latency)} workflows com dados de latência")

    # Cruzar volume × latência
    log.info("Calculando impacto (volume × latência)...")
    merged = merge_workflow_metrics(volume, latency)

    # Preparar resultado final
    result = {
        "metadata": {
            "collected_at": datetime.utcnow().isoformat() + "Z",
            "period_start": start_iso,
            "period_end": end_iso,
            "period_days": 7,
            "vm_url": vm_url,
            "instance": "wf001",
        },
        "summary": {
            "total_workflows": len(merged),
            "total_executions_7d": sum(w["total_executions_7d"] for w in merged),
            "top_10_by_volume": [
                {"name": w["workflow_name"], "executions": w["total_executions_7d"]}
                for w in sorted(merged, key=lambda x: x["total_executions_7d"], reverse=True)[:10]
            ],
            "top_10_by_latency": [
                {"name": w["workflow_name"], "latency_sec": w["avg_latency_seconds"]}
                for w in sorted(merged, key=lambda x: x["avg_latency_seconds"], reverse=True)[:10]
            ],
            "top_10_by_impact": [
                {"name": w["workflow_name"], "impact_sec": w["total_impact_seconds"]}
                for w in merged[:10]
            ],
        },
        "workflows": merged,
    }

    # Salvar em JSON
    today = datetime.now().strftime("%Y-%m-%d")
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    session_dir = Path(f"docs/SESSIONS/{today}")
    session_dir.mkdir(parents=True, exist_ok=True)

    output_file = session_dir / f"n8n-metrics-7d-{timestamp}.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    log.info(f"✅ Métricas salvas em: {output_file}")
    print(f"\n📊 Resultado: {output_file}")

    # Exibir resumo
    print("\n=== RESUMO ===")
    print(f"Total de workflows: {result['summary']['total_workflows']}")
    print(f"Total de execuções (7d): {result['summary']['total_executions_7d']:,}")
    print("\nTop 5 por IMPACTO (volume × latência):")
    for i, wf in enumerate(result['summary']['top_10_by_impact'][:5], 1):
        print(f"  {i}. {wf['name']}: {wf['impact_sec']:,.0f}s total")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log.warning("Interrompido pelo usuário")
        sys.exit(1)
    except Exception as e:
        log.error(f"Erro fatal: {e}", exc_info=True)
        sys.exit(1)

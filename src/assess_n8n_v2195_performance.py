#!/usr/bin/env python3
"""
Avaliacao de desempenho N8N v2.19.5 — comparacao com baseline ANA-001.

Coleta metricas do VictoriaMetrics (wfdb01) para o periodo pos-upgrade do N8N
de 2.6.4 para 2.19.5, com tratamento de gaps de coleta do Prometheus.

Funcionalidades:
- Deteccao automatica de gaps de coleta (periodos sem dados no VM)
- Coleta apenas dos periodos com dados disponveis
- Verificacao de versao N8N e mudancas de nomes de metricas
- Comparacao com baseline ANA-001 (jan-mar 2026, N8N 2.6.4)
- Relatorio de nomes de metricas: compatibilidade 2.6.4 vs 2.19.5

Saida: JSON em docs/SESSIONS/YYYY-MM-DD/n8n-v2195-assessment-YYYYMMDD-HHMMSS.json

Uso::

    # Via SSH tunnel (wfdb01 VM):
    ssh -N -L 18428:172.20.0.13:8428 -p 5010 archaris@86.48.31.149 &
    uv run python src/assess_n8n_v2195_performance.py --vm-url http://localhost:18428

    # Com N8N URL para verificar versao:
    uv run python src/assess_n8n_v2195_performance.py \\
        --vm-url http://localhost:18428 \\
        --n8n-url https://n8n.vya.digital \\
        --lookback-days 30

    # Somente analise local (sem conectividade):
    uv run python src/assess_n8n_v2195_performance.py --dry-run

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
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Baseline ANA-001 (jan-mar 2026, N8N 2.6.4) — referencia para comparacao
# ---------------------------------------------------------------------------
BASELINE_ANA001: dict[str, Any] = {
    "report_id": "ANA-001",
    "period": "2026-01-01 to 2026-03-31",
    "n8n_version": "2.6.4",
    "total_executions_90d_scrape": 148058,
    "total_executions_90d_pushgateway": 366303,
    "active_workflows": 23,
    "p95_latency_all_workflows_seconds": 0.095,
    "workflows_exceeding_1s": 0,
    "top_workflow": "121Labs PABX call-analytics",
    "top_workflow_executions_90d": 429786,
    "top_workflow_pct": 57,
    "peak_exec_per_hour": 8416,
    "peak_date": "2026-03-27T20:00:00Z",
    "cpu_bottleneck": False,
    "queue_metrics_enabled": False,
    "dual_collection_confirmed": True,
}

# ---------------------------------------------------------------------------
# Nomes de metricas por versao
# ---------------------------------------------------------------------------
# N8N 2.6.x — nomes legados
METRICS_V26X: dict[str, str] = {
    "executions_total": "n8n_workflow_executions_total",
    "execution_duration_sum": "n8n_workflow_execution_duration_seconds_sum",
    "execution_duration_count": "n8n_workflow_execution_duration_seconds_count",
    "execution_duration_bucket": "n8n_workflow_execution_duration_seconds_bucket",
    "queue_active": "n8n_scaling_mode_queue_jobs_active",
    "queue_waiting": "n8n_scaling_mode_queue_jobs_waiting",
    "queue_completed": "n8n_scaling_mode_queue_jobs_completed",
    "queue_failed": "n8n_scaling_mode_queue_jobs_failed",
    "version_info": "n8n_version_info",
}

# N8N 2.19.x — nomes possivelmente atualizados (verificar breaking changes)
# Referencia: https://github.com/n8nio/n8n/blob/master/CHANGELOG.md
METRICS_V219X: dict[str, str] = {
    "executions_total": "n8n_workflow_executions_total",
    "execution_duration_sum": "n8n_workflow_execution_duration_seconds_sum",
    "execution_duration_count": "n8n_workflow_execution_duration_seconds_count",
    "execution_duration_bucket": "n8n_workflow_execution_duration_seconds_bucket",
    # Queue metrics — nomes alternativos encontrados em versoes recentes
    "queue_active": "n8n_scaling_mode_queue_jobs_active",
    "queue_waiting": "n8n_scaling_mode_queue_jobs_waiting",
    "queue_completed": "n8n_scaling_mode_queue_jobs_completed",
    "queue_failed": "n8n_scaling_mode_queue_jobs_failed",
    # Alternativas pos-2.14 (alguns builds usam nomes simplificados)
    "queue_active_alt": "n8n_queue_jobs_active",
    "queue_waiting_alt": "n8n_queue_jobs_waiting",
    "executions_failed": "n8n_workflow_executions_failed_total",
    "version_info": "n8n_version_info",
}


# ---------------------------------------------------------------------------
# Utilitarios de acesso ao VictoriaMetrics
# ---------------------------------------------------------------------------

def vm_query_instant(vm_url: str, promql: str, timeout: int = 15) -> dict[str, Any]:
    """Executa query instantanea no VictoriaMetrics.

    :param vm_url: URL base do VictoriaMetrics.
    :param promql: Expressao PromQL.
    :param timeout: Timeout HTTP em segundos.
    :returns: Dict ``{"result": [...], "resultType": "..."}`` ou ``{"error": "..."}``.

    >>> callable(vm_query_instant)
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
    except urllib.error.URLError as exc:
        return {"error": str(exc)}
    except Exception as exc:
        return {"error": str(exc)}


def vm_query_range(
    vm_url: str,
    promql: str,
    start: str,
    end: str,
    step: str = "1h",
    timeout: int = 30,
) -> dict[str, Any]:
    """Executa query range no VictoriaMetrics.

    :param vm_url: URL base do VictoriaMetrics.
    :param promql: Expressao PromQL.
    :param start: Timestamp ISO 8601 de inicio.
    :param end: Timestamp ISO 8601 de fim.
    :param step: Intervalo de amostragem (ex: '1h', '6h', '1d').
    :param timeout: Timeout HTTP em segundos.
    :returns: Dict com ``result`` (lista de series) ou ``{"error": "..."}``.

    >>> callable(vm_query_range)
    True
    """
    endpoint = f"{vm_url.rstrip('/')}/api/v1/query_range"
    params = urllib.parse.urlencode({"query": promql, "start": start, "end": end, "step": step})
    url = f"{endpoint}?{params}"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:  # noqa: S310
            data = json.loads(resp.read())
            if data.get("status") != "success":
                return {"error": f"VM returned status={data.get('status')}", "result": []}
            return data.get("data", {"result": []})
    except TimeoutError:
        return {"error": "timeout", "result": []}
    except urllib.error.URLError as exc:
        return {"error": str(exc), "result": []}
    except Exception as exc:
        return {"error": str(exc), "result": []}


def vm_is_reachable(vm_url: str, timeout: int = 5) -> bool:
    """Verifica se o VictoriaMetrics esta acessivel.

    :param vm_url: URL base do VictoriaMetrics.
    :param timeout: Timeout em segundos.
    :returns: True se acessivel.

    >>> vm_is_reachable.__doc__ is not None
    True
    """
    try:
        url = f"{vm_url.rstrip('/')}/api/v1/query?query=1"
        with urllib.request.urlopen(url, timeout=timeout) as resp:  # noqa: S310
            return resp.status == 200
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Deteccao de gaps de coleta
# ---------------------------------------------------------------------------

def detect_collection_gaps(
    vm_url: str,
    start: str,
    end: str,
    metric: str = "n8n_workflow_executions_total",
) -> dict[str, Any]:
    """Detecta periodos sem dados de coleta no VictoriaMetrics.

    Usa ``count_over_time`` horario para mapear quais horas tem dados.
    Gaps sao horas consecutivas sem nenhum ponto coletado.

    :param vm_url: URL base do VictoriaMetrics.
    :param start: Inicio do periodo (ISO 8601).
    :param end: Fim do periodo (ISO 8601).
    :param metric: Metrica de referencia para deteccao de gaps.
    :returns: Dict com lista de gaps, cobertura percentual e periodo total.

    >>> callable(detect_collection_gaps)
    True
    """
    log.info("Detectando gaps de coleta no periodo %s -> %s", start, end)

    # Conta amostras por hora para toda a serie
    promql = f'count_over_time({metric}[1h])'
    result = vm_query_range(vm_url, promql, start, end, step="1h")

    if "error" in result and not result.get("result"):
        log.warning("Falha ao detectar gaps: %s", result.get("error"))
        return {
            "error": result.get("error"),
            "gaps": [],
            "coverage_pct": 0.0,
            "total_hours": 0,
            "hours_with_data": 0,
        }

    series_list = result.get("result", [])

    # Coletar todos os timestamps que tem pelo menos uma serie com dado
    timestamps_with_data: set[int] = set()
    for series in series_list:
        for ts, val in series.get("values", []):
            if val and val != "0":
                timestamps_with_data.add(int(ts))

    # Calcular periodo total em horas
    try:
        start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
        end_dt = datetime.fromisoformat(end.replace("Z", "+00:00"))
    except ValueError:
        start_dt = datetime.utcnow() - timedelta(days=30)
        end_dt = datetime.utcnow()
        start_dt = start_dt.replace(tzinfo=timezone.utc)
        end_dt = end_dt.replace(tzinfo=timezone.utc)

    total_hours = max(1, int((end_dt - start_dt).total_seconds() / 3600))

    # Mapear horas esperadas (1 por hora)
    expected_timestamps = set()
    cursor = start_dt
    while cursor <= end_dt:
        expected_timestamps.add(int(cursor.timestamp()))
        cursor += timedelta(hours=1)

    missing_timestamps = sorted(expected_timestamps - timestamps_with_data)
    hours_with_data = len(timestamps_with_data)
    coverage_pct = round(100.0 * hours_with_data / total_hours, 1) if total_hours > 0 else 0.0

    # Agrupar timestamps faltantes em gaps consecutivos
    gaps = []
    if missing_timestamps:
        gap_start_ts = missing_timestamps[0]
        gap_end_ts = missing_timestamps[0]
        for ts in missing_timestamps[1:]:
            if ts - gap_end_ts <= 3600 + 60:  # tolerancia de 1 minuto
                gap_end_ts = ts
            else:
                gaps.append({
                    "start": datetime.utcfromtimestamp(gap_start_ts).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "end": datetime.utcfromtimestamp(gap_end_ts).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "duration_hours": round((gap_end_ts - gap_start_ts) / 3600, 1),
                })
                gap_start_ts = ts
                gap_end_ts = ts
        gaps.append({
            "start": datetime.utcfromtimestamp(gap_start_ts).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "end": datetime.utcfromtimestamp(gap_end_ts).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "duration_hours": round((gap_end_ts - gap_start_ts) / 3600, 1),
        })

    log.info(
        "Gaps detectados: %d gap(s), cobertura %.1f%% (%d/%d horas)",
        len(gaps), coverage_pct, hours_with_data, total_hours,
    )

    return {
        "total_hours": total_hours,
        "hours_with_data": hours_with_data,
        "hours_missing": total_hours - hours_with_data,
        "coverage_pct": coverage_pct,
        "gaps_count": len(gaps),
        "gaps": gaps,
        "note": "Gaps baseados na metrica: " + metric,
    }


# ---------------------------------------------------------------------------
# Verificacao de versao N8N e metricas disponiveis
# ---------------------------------------------------------------------------

def check_n8n_version(n8n_url: str, timeout: int = 10) -> dict[str, Any]:
    """Verifica versao do N8N via endpoint /healthz ou /metrics.

    :param n8n_url: URL base do N8N (ex: https://n8n.vya.digital).
    :param timeout: Timeout HTTP em segundos.
    :returns: Dict com versao detectada e status.

    >>> callable(check_n8n_version)
    True
    """
    result: dict[str, Any] = {"version": "unknown", "method": "none", "status": "fail"}

    # Tentar /healthz (disponivel em versoes recentes)
    for path in ["/healthz", "/health"]:
        try:
            url = f"{n8n_url.rstrip('/')}{path}"
            with urllib.request.urlopen(url, timeout=timeout) as resp:  # noqa: S310
                body = json.loads(resp.read())
                if isinstance(body, dict):
                    result["version"] = body.get("version", body.get("n8nVersion", "unknown"))
                    result["status"] = body.get("status", "ok")
                    result["method"] = f"GET {path}"
                    return result
        except Exception:
            continue

    # Tentar /metrics — procurar n8n_version_info
    try:
        url = f"{n8n_url.rstrip('/')}/metrics"
        with urllib.request.urlopen(url, timeout=timeout) as resp:  # noqa: S310
            body = resp.read().decode("utf-8")
            for line in body.splitlines():
                if "n8n_version_info" in line and not line.startswith("#"):
                    # Formato: n8n_version_info{version="2.19.5",...} 1
                    import re
                    m = re.search(r'version="([^"]+)"', line)
                    if m:
                        result["version"] = m.group(1)
                        result["method"] = "GET /metrics (n8n_version_info)"
                        result["status"] = "ok"
                        return result
    except Exception as exc:
        result["error"] = str(exc)

    return result


def discover_available_metrics(vm_url: str) -> dict[str, Any]:
    """Descobre quais metricas n8n_* estao disponiveis no VictoriaMetrics.

    Compara metricas encontradas com os nomes esperados para v2.6.x e v2.19.x.

    :param vm_url: URL base do VictoriaMetrics.
    :returns: Dict com metricas encontradas e analise de compatibilidade.

    >>> callable(discover_available_metrics)
    True
    """
    log.info("Descobrindo metricas n8n_* disponiveis no VictoriaMetrics...")

    result = vm_query_instant(vm_url, 'count by (__name__)({__name__=~"n8n_.*"})')
    if "error" in result:
        log.warning("Falha ao descobrir metricas: %s", result.get("error"))
        return {"error": result.get("error"), "found": [], "v26x_compat": {}, "v219x_compat": {}}

    found_names: list[str] = sorted(
        series.get("metric", {}).get("__name__", "")
        for series in result.get("result", [])
        if series.get("metric", {}).get("__name__")
    )

    # Compatibilidade com v2.6.x
    v26x_compat: dict[str, bool] = {
        key: name in found_names for key, name in METRICS_V26X.items()
    }
    # Compatibilidade com v2.19.x
    v219x_compat: dict[str, bool] = {
        key: name in found_names for key, name in METRICS_V219X.items()
    }

    queue_metrics_active = any(
        name in found_names for name in [
            "n8n_scaling_mode_queue_jobs_active",
            "n8n_queue_jobs_active",
        ]
    )

    log.info("Metricas n8n_* encontradas: %d", len(found_names))
    log.info("Queue metrics ativas: %s", queue_metrics_active)

    return {
        "total_metrics_found": len(found_names),
        "metric_names": found_names,
        "queue_metrics_active": queue_metrics_active,
        "v26x_compatibility": v26x_compat,
        "v219x_compatibility": v219x_compat,
        "breaking_changes_detected": [
            key for key, present in v26x_compat.items() if not present
        ],
    }


# ---------------------------------------------------------------------------
# Coleta de metricas de execucao
# ---------------------------------------------------------------------------

def collect_execution_metrics(
    vm_url: str,
    start: str,
    end: str,
    available_metrics: dict[str, Any],
) -> dict[str, Any]:
    """Coleta metricas de execucao por workflow no periodo disponivel.

    Usa o nome de metrica correto conforme o que esta disponivel no VM.

    :param vm_url: URL base do VictoriaMetrics.
    :param start: Inicio do periodo (ISO 8601).
    :param end: Fim do periodo (ISO 8601).
    :param available_metrics: Resultado de discover_available_metrics().
    :returns: Dict com volumes, latencias e ofensores.

    >>> callable(collect_execution_metrics)
    True
    """
    found_names = set(available_metrics.get("metric_names", []))
    exec_metric = "n8n_workflow_executions_total"
    if exec_metric not in found_names:
        log.warning("Metrica de execucoes nao encontrada: %s", exec_metric)
        return {"error": f"metrica ausente: {exec_metric}", "workflows": []}

    log.info("Coletando volume de execucoes por workflow...")

    # Volume total no periodo
    days_lookback = max(1, int(
        (datetime.fromisoformat(end.replace("Z", "+00:00")) -
         datetime.fromisoformat(start.replace("Z", "+00:00"))).total_seconds() / 86400
    ))
    lookback_window = f"{days_lookback}d"

    volume_query = f'increase({exec_metric}{{instance="wf001"}}[{lookback_window}])'
    volume_result = vm_query_range(vm_url, volume_query, start, end, step=lookback_window)

    workflows: list[dict[str, Any]] = []
    for series in volume_result.get("result", []):
        metric = series.get("metric", {})
        values = series.get("values", [])
        if not values:
            continue
        total = sum(float(v[1]) for v in values if v[1] not in ("NaN", "Inf", "-Inf"))
        workflows.append({
            "workflow_name": metric.get("workflow_name", "unknown"),
            "workflow_id": metric.get("workflow_id", "unknown"),
            "instance": metric.get("instance", "unknown"),
            "total_executions": int(total),
        })

    workflows.sort(key=lambda x: x["total_executions"], reverse=True)

    # Latencia media
    log.info("Coletando latencia media por workflow...")
    lat_metric_sum = "n8n_workflow_execution_duration_seconds_sum"
    lat_metric_count = "n8n_workflow_execution_duration_seconds_count"

    latency_by_wf: dict[str, float] = {}
    if lat_metric_sum in found_names and lat_metric_count in found_names:
        lat_query = (
            f'rate({lat_metric_sum}{{instance="wf001"}}[{lookback_window}])'
            f' / rate({lat_metric_count}{{instance="wf001"}}[{lookback_window}])'
        )
        lat_result = vm_query_range(vm_url, lat_query, start, end, step=lookback_window)
        for series in lat_result.get("result", []):
            wf_id = series.get("metric", {}).get("workflow_id", "unknown")
            values = series.get("values", [])
            if values:
                valid = [float(v[1]) for v in values if v[1] not in ("NaN", "Inf", "-Inf")]
                if valid:
                    latency_by_wf[wf_id] = round(sum(valid) / len(valid), 4)

    # Merging volume + latencia
    for wf in workflows:
        wf["avg_latency_seconds"] = latency_by_wf.get(wf["workflow_id"], None)
        if wf["avg_latency_seconds"] is not None:
            wf["total_impact_seconds"] = round(wf["total_executions"] * wf["avg_latency_seconds"], 2)
        else:
            wf["total_impact_seconds"] = None

    total_executions = sum(w["total_executions"] for w in workflows)
    log.info(
        "Total execucoes coletadas: %d em %d workflows",
        total_executions, len(workflows),
    )

    return {
        "period_start": start,
        "period_end": end,
        "lookback_window": lookback_window,
        "total_executions": total_executions,
        "active_workflows": len(workflows),
        "workflows": workflows,
    }


def collect_queue_metrics(vm_url: str) -> dict[str, Any]:
    """Coleta estado atual das metricas de fila (instantaneo).

    Tenta ambos os nomes: legado (v2.6.x) e alternativo (v2.19.x).

    :param vm_url: URL base do VictoriaMetrics.
    :returns: Dict com metricas de fila ou indicacao de ausencia.

    >>> callable(collect_queue_metrics)
    True
    """
    queue_candidates = [
        ("n8n_scaling_mode_queue_jobs_active", "active"),
        ("n8n_scaling_mode_queue_jobs_waiting", "waiting"),
        ("n8n_scaling_mode_queue_jobs_completed", "completed"),
        ("n8n_scaling_mode_queue_jobs_failed", "failed"),
        ("n8n_queue_jobs_active", "active_alt"),
        ("n8n_queue_jobs_waiting", "waiting_alt"),
    ]

    found: dict[str, Any] = {}
    for metric_name, key in queue_candidates:
        result = vm_query_instant(vm_url, metric_name)
        series = result.get("result", [])
        if series:
            val = series[0].get("value", [None, "0"])[1]
            found[key] = float(val) if val not in ("NaN", "Inf", "-Inf") else None
            found[f"{key}_metric_name"] = metric_name

    queue_enabled = bool(found)
    log.info("Queue metrics disponiveis: %s (%d metricas)", queue_enabled, len(found) // 2)

    return {
        "queue_metrics_enabled": queue_enabled,
        "current_values": found,
        "note": "F16 habilitado" if queue_enabled else "F16 nao detectado ou queue nao ativa",
    }


def collect_failure_rate(
    vm_url: str,
    start: str,
    end: str,
) -> dict[str, Any]:
    """Coleta taxa de falha de execucoes no periodo.

    :param vm_url: URL base do VictoriaMetrics.
    :param start: Inicio do periodo (ISO 8601).
    :param end: Fim do periodo (ISO 8601).
    :returns: Dict com taxa de falha total e por workflow.

    >>> callable(collect_failure_rate)
    True
    """
    log.info("Coletando taxa de falha de execucoes...")

    days = max(1, int(
        (datetime.fromisoformat(end.replace("Z", "+00:00")) -
         datetime.fromisoformat(start.replace("Z", "+00:00"))).total_seconds() / 86400
    ))
    window = f"{days}d"

    # Tentativa com metrica de falha (pode nao existir em todas as versoes)
    fail_queries = [
        f'increase(n8n_workflow_executions_total{{instance="wf001",status="failed"}}[{window}])',
        f'increase(n8n_workflow_executions_failed_total{{instance="wf001"}}[{window}])',
    ]

    for query in fail_queries:
        result = vm_query_range(vm_url, query, start, end, step=window)
        series = result.get("result", [])
        if series:
            by_workflow: list[dict] = []
            total_failures = 0
            for s in series:
                vals = s.get("values", [])
                if not vals:
                    continue
                count = int(sum(
                    float(v[1]) for v in vals if v[1] not in ("NaN", "Inf", "-Inf")
                ))
                if count > 0:
                    total_failures += count
                    by_workflow.append({
                        "workflow_name": s.get("metric", {}).get("workflow_name", "unknown"),
                        "workflow_id": s.get("metric", {}).get("workflow_id", "unknown"),
                        "failures": count,
                    })
            by_workflow.sort(key=lambda x: x["failures"], reverse=True)
            return {
                "total_failures": total_failures,
                "query_used": query,
                "by_workflow": by_workflow,
            }

    return {
        "total_failures": None,
        "note": "Metrica de falha nao disponivel (status label pode nao existir nesta versao)",
    }


# ---------------------------------------------------------------------------
# Comparacao com baseline ANA-001
# ---------------------------------------------------------------------------

def compare_with_baseline(
    current_metrics: dict[str, Any],
    coverage_pct: float,
    days_collected: int,
) -> dict[str, Any]:
    """Compara metricas atuais com baseline ANA-001.

    Normaliza metricas para 30 dias para comparacao justa,
    considerando a cobertura de coleta disponivel.

    :param current_metrics: Resultado de collect_execution_metrics().
    :param coverage_pct: Percentual de cobertura de coleta.
    :param days_collected: Numero de dias no periodo de coleta.
    :returns: Dict com comparacao e analise de tendencias.

    >>> callable(compare_with_baseline)
    True
    """
    baseline = BASELINE_ANA001
    current_total = current_metrics.get("total_executions", 0)
    current_workflows = current_metrics.get("active_workflows", 0)
    current_wf_list = current_metrics.get("workflows", [])

    # Normalizar para 30 dias
    baseline_per_day = baseline["total_executions_90d_scrape"] / 90
    baseline_per_30d = int(baseline_per_day * 30)

    # Ajustar current para 30 dias proporcional
    if days_collected > 0:
        current_per_day = current_total / days_collected
        current_per_30d_est = int(current_per_day * 30)
    else:
        current_per_30d_est = 0

    # Ajuste por cobertura (se 70% de dados, multiplicar por 1/0.7 para estimar total real)
    if coverage_pct > 0:
        current_per_30d_adjusted = int(current_per_30d_est / (coverage_pct / 100))
    else:
        current_per_30d_adjusted = current_per_30d_est

    # Delta percentual
    if baseline_per_30d > 0:
        delta_pct = round(100.0 * (current_per_30d_adjusted - baseline_per_30d) / baseline_per_30d, 1)
    else:
        delta_pct = 0.0

    # Top workflow comparacao
    top_wf_current = current_wf_list[0] if current_wf_list else {}
    top_wf_changed = (
        top_wf_current.get("workflow_name", "") != baseline["top_workflow"]
    )

    # Latencia comparacao
    latencies = [
        w["avg_latency_seconds"]
        for w in current_wf_list
        if w.get("avg_latency_seconds") is not None
    ]
    avg_latency_current = round(sum(latencies) / len(latencies), 4) if latencies else None

    assessment = "ESTAVEL"
    if delta_pct > 50:
        assessment = "CRESCIMENTO ALTO — investigar"
    elif delta_pct > 20:
        assessment = "CRESCIMENTO MODERADO"
    elif delta_pct < -30:
        assessment = "REDUCAO SIGNIFICATIVA — verificar gaps"

    return {
        "baseline_period": baseline["period"],
        "baseline_n8n_version": baseline["n8n_version"],
        "baseline_executions_30d_est": baseline_per_30d,
        "current_executions_collected": current_total,
        "current_executions_30d_est": current_per_30d_est,
        "current_executions_30d_adjusted_for_gaps": current_per_30d_adjusted,
        "coverage_pct": coverage_pct,
        "delta_vs_baseline_pct": delta_pct,
        "baseline_avg_latency_seconds": baseline["p95_latency_all_workflows_seconds"],
        "current_avg_latency_seconds": avg_latency_current,
        "baseline_active_workflows": baseline["active_workflows"],
        "current_active_workflows": current_workflows,
        "top_workflow_changed": top_wf_changed,
        "top_workflow_current": top_wf_current.get("workflow_name", "N/A"),
        "top_workflow_baseline": baseline["top_workflow"],
        "assessment": assessment,
        "caveat": (
            f"Dados com {coverage_pct:.1f}% de cobertura devido a gaps Prometheus. "
            "Valores estimados para 30d sao aproximacoes."
        ) if coverage_pct < 90 else None,
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def build_args() -> argparse.Namespace:
    """Constroi os argumentos CLI.

    :returns: Namespace com argumentos parseados.
    """
    parser = argparse.ArgumentParser(
        description="Avaliacao de desempenho N8N v2.19.5 vs baseline ANA-001",
    )
    parser.add_argument(
        "--vm-url",
        default="http://172.20.0.13:8428",
        help="URL base do VictoriaMetrics (default: http://172.20.0.13:8428)",
    )
    parser.add_argument(
        "--n8n-url",
        default=None,
        help="URL base do N8N para verificar versao (ex: https://n8n.vya.digital)",
    )
    parser.add_argument(
        "--lookback-days",
        type=int,
        default=30,
        help="Numero de dias para retroagir na coleta (default: 30)",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Diretorio de saida do JSON (default: docs/SESSIONS/YYYY-MM-DD/)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Nao conectar ao VM — apenas validar estrutura do script",
    )
    parser.add_argument(
        "--n8n-version",
        default="2.19.5",
        help="Versao conhecida do N8N (usado quando healthz nao esta disponivel)",
    )
    return parser.parse_args()


def main() -> None:
    """Executa avaliacao completa de desempenho N8N v2.19.5.

    Conecta ao VictoriaMetrics, detecta gaps, coleta metricas disponíveis,
    compara com baseline ANA-001 e salva resultado em JSON.
    """
    args = build_args()

    log.info("=== Avaliacao de Desempenho N8N v%s ===", args.n8n_version)
    log.info("VM URL: %s | Lookback: %d dias", args.vm_url, args.lookback_days)

    now = datetime.now(tz=timezone.utc)
    end_time = now
    start_time = now - timedelta(days=args.lookback_days)
    start_iso = start_time.strftime("%Y-%m-%dT%H:%M:%SZ")
    end_iso = end_time.strftime("%Y-%m-%dT%H:%M:%SZ")

    report: dict[str, Any] = {
        "report_id": f"PERF-2195-{now.strftime('%Y%m%d')}",
        "generated_at": now.isoformat(),
        "n8n_version_assessed": args.n8n_version,
        "baseline_ref": "ANA-001",
        "period_start": start_iso,
        "period_end": end_iso,
        "lookback_days": args.lookback_days,
        "vm_url": args.vm_url,
    }

    # --- Dry-run: apenas valida estrutura ---
    if args.dry_run:
        log.info("[DRY-RUN] Validacao de estrutura do script — sem conexao VM")
        report["mode"] = "dry_run"
        report["baseline"] = BASELINE_ANA001
        report["note"] = "Dry-run: nenhuma conexao ao VictoriaMetrics foi feita"
        _save_report(report, args.output_dir, now)
        log.info("[DRY-RUN] Script validado com sucesso")
        sys.exit(0)

    # --- Verificar acessibilidade do VM ---
    log.info("Verificando acessibilidade do VictoriaMetrics...")
    vm_ok = vm_is_reachable(args.vm_url)
    report["vm_reachable"] = vm_ok

    if not vm_ok:
        log.error(
            "VictoriaMetrics nao acessivel em %s. "
            "Abrir SSH tunnel: ssh -N -L 18428:172.20.0.13:8428 -p 5010 archaris@86.48.31.149 &"
            " e usar --vm-url http://localhost:18428",
            args.vm_url,
        )
        report["error"] = "VictoriaMetrics inacessivel"
        report["baseline"] = BASELINE_ANA001
        _save_report(report, args.output_dir, now)
        sys.exit(1)

    # --- Versao N8N ---
    if args.n8n_url:
        log.info("Verificando versao N8N em %s...", args.n8n_url)
        version_info = check_n8n_version(args.n8n_url)
        report["n8n_version_detected"] = version_info
        if version_info.get("version") not in ("unknown", None):
            args.n8n_version = version_info["version"]
            report["n8n_version_assessed"] = args.n8n_version
    else:
        report["n8n_version_detected"] = {
            "version": args.n8n_version,
            "method": "cli-argument (--n8n-version)",
            "status": "assumed",
        }

    # --- Descoberta de metricas ---
    log.info("Descobrindo metricas n8n_* no VictoriaMetrics...")
    available = discover_available_metrics(args.vm_url)
    report["available_metrics"] = available

    if available.get("breaking_changes_detected"):
        log.warning(
            "Possiveis breaking changes detectados: metricas ausentes: %s",
            available["breaking_changes_detected"],
        )

    # --- Deteccao de gaps ---
    log.info("Detectando gaps de coleta Prometheus no periodo...")
    gaps_info = detect_collection_gaps(args.vm_url, start_iso, end_iso)
    report["collection_gaps"] = gaps_info

    if gaps_info.get("gaps_count", 0) > 0:
        log.warning(
            "ATENCAO: %d gap(s) de coleta detectados — cobertura %.1f%%",
            gaps_info["gaps_count"],
            gaps_info.get("coverage_pct", 0),
        )
        for i, gap in enumerate(gaps_info.get("gaps", []), 1):
            log.warning(
                "  Gap %d: %s -> %s (%.1fh sem dados)",
                i, gap["start"], gap["end"], gap["duration_hours"],
            )

    # --- Metricas de execucao ---
    log.info("Coletando metricas de execucao...")
    exec_metrics = collect_execution_metrics(args.vm_url, start_iso, end_iso, available)
    report["execution_metrics"] = exec_metrics

    # --- Metricas de fila (F16) ---
    log.info("Verificando metricas de fila (F16)...")
    queue = collect_queue_metrics(args.vm_url)
    report["queue_metrics"] = queue

    # --- Taxa de falha ---
    log.info("Coletando taxa de falha...")
    failures = collect_failure_rate(args.vm_url, start_iso, end_iso)
    report["failure_rate"] = failures

    # --- Comparacao com baseline ---
    log.info("Comparando com baseline ANA-001...")
    comparison = compare_with_baseline(
        exec_metrics,
        gaps_info.get("coverage_pct", 100.0),
        args.lookback_days,
    )
    report["comparison_vs_baseline"] = comparison
    report["baseline_ref_data"] = BASELINE_ANA001

    # --- Sumario ---
    report["summary"] = {
        "n8n_version": args.n8n_version,
        "period": f"{start_iso} -> {end_iso}",
        "total_executions_collected": exec_metrics.get("total_executions", 0),
        "active_workflows": exec_metrics.get("active_workflows", 0),
        "collection_coverage_pct": gaps_info.get("coverage_pct", 100.0),
        "gaps_count": gaps_info.get("gaps_count", 0),
        "queue_metrics_active": available.get("queue_metrics_active", False),
        "assessment": comparison.get("assessment", "N/A"),
        "delta_vs_baseline_pct": comparison.get("delta_vs_baseline_pct", 0),
        "breaking_changes": available.get("breaking_changes_detected", []),
        "top_3_workflows": [
            {"name": w["workflow_name"], "executions": w["total_executions"]}
            for w in exec_metrics.get("workflows", [])[:3]
        ],
    }

    # --- Salvar resultado ---
    output_path = _save_report(report, args.output_dir, now)

    log.info("=== Avaliacao Concluida ===")
    log.info("Assessment: %s", report["summary"]["assessment"])
    log.info("Cobertura de coleta: %.1f%%", gaps_info.get("coverage_pct", 100.0))
    log.info("Delta vs baseline: %+.1f%%", comparison.get("delta_vs_baseline_pct", 0))
    log.info("Resultado salvo em: %s", output_path)


def _save_report(report: dict[str, Any], output_dir: str | None, now: datetime) -> Path:
    """Salva o relatorio JSON no diretorio de sessao.

    :param report: Dict com todos os dados coletados.
    :param output_dir: Diretorio de saida (None = auto-detectar).
    :param now: Datetime atual para gerar timestamp no nome do arquivo.
    :returns: Path do arquivo salvo.
    """
    if output_dir:
        out_dir = Path(output_dir)
    else:
        # Auto-detectar: docs/SESSIONS/YYYY-MM-DD/
        script_dir = Path(__file__).resolve().parent.parent
        out_dir = script_dir / "docs" / "SESSIONS" / now.strftime("%Y-%m-%d")

    out_dir.mkdir(parents=True, exist_ok=True)
    filename = f"n8n-v2195-assessment-{now.strftime('%Y%m%d-%H%M%S')}.json"
    out_path = out_dir / filename

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str, ensure_ascii=False)

    print(f"\nRelatorio salvo em: {out_path}")
    return out_path


if __name__ == "__main__":
    main()

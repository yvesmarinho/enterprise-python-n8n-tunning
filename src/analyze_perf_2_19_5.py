"""
analyze_perf_2_19_5.py
=======================
Analisa snapshot de desempenho N8N 2.19.5 coletado via collect_perf_2_19_5.py
ou usa dados inline coletados manualmente via SSH.

Gera:
  - tmp/perf_analysis_2_19_5_YYYYMMDD_HHMMSS.json
  - Imprime sumario no stdout

Uso:
    uv run python src/analyze_perf_2_19_5.py [path/to/snapshot.json]
    uv run python src/analyze_perf_2_19_5.py   # usa dados inline
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
TMP = ROOT / "tmp"
TMP.mkdir(exist_ok=True)

TS = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
OUTPUT = TMP / f"perf_analysis_2_19_5_{TS}.json"

# ---------------------------------------------------------------------------
# Dados coletados manualmente via SSH em 2026-05-08T11:30-11:50 UTC-3
# ---------------------------------------------------------------------------
SNAPSHOT = {
    "collected_at": "2026-05-08T14:46:00Z",
    "n8n_version": "2.19.5",
    "previous_version": "2.19.1",
    "host": "wf001.vya.digital",
    "queue_mode": "rabbitmq",
    "containers_uptime_hours": 13,

    # docker stats (dois snapshots: T0=11:37 e T1=11:46 UTC-3)
    "docker_stats_t0": [
        {"name": "n8n-n8n_webhook-2", "cpu_pct": 0.00, "mem_mib": 279.7},
        {"name": "n8n-n8n_worker-1",  "cpu_pct": 11.36, "mem_mib": 507.7},
        {"name": "n8n-n8n_webhook-3", "cpu_pct": 0.07, "mem_mib": 249.1},
        {"name": "n8n-n8n_worker-2",  "cpu_pct": 55.69, "mem_mib": 490.5},
        {"name": "n8n-n8n_webhook-1", "cpu_pct": 0.49, "mem_mib": 273.1},
        {"name": "n8n-n8n_mcp-1",     "cpu_pct": 0.00, "mem_mib": 167.9},
        {"name": "n8n-n8n_worker-3",  "cpu_pct": 13.96, "mem_mib": 553.9},
        {"name": "n8n-n8n_editor-1",  "cpu_pct": 10.23, "mem_mib": 511.0},
    ],
    "docker_stats_t1": [
        {"name": "n8n-n8n_webhook-2", "cpu_pct": 0.07, "mem_mib": 265.6},
        {"name": "n8n-n8n_worker-1",  "cpu_pct": 2.87, "mem_mib": 496.6},
        {"name": "n8n-n8n_webhook-3", "cpu_pct": 1.22, "mem_mib": 251.6},
        {"name": "n8n-n8n_worker-2",  "cpu_pct": 3.36, "mem_mib": 492.4},
        {"name": "n8n-n8n_webhook-1", "cpu_pct": 0.31, "mem_mib": 257.9},
        {"name": "n8n-n8n_mcp-1",     "cpu_pct": 0.00, "mem_mib": 167.9},
        {"name": "n8n-n8n_worker-3",  "cpu_pct": 123.02, "mem_mib": 393.7},
        {"name": "n8n-n8n_editor-1",  "cpu_pct": 13.12, "mem_mib": 333.3},
    ],

    # N8N /metrics (editor, uptime ~13h)
    "n8n_metrics_editor": {
        "version": "v2.19.5",
        "active_workflow_count": 76,
        "instance_role_leader": True,
        "process_resident_memory_bytes": 568131584,
        "process_cpu_seconds_total": 3246.83,
        "process_start_time_seconds": 1778203618,
        "nodejs_eventloop_lag_p50_seconds": 0.010272767,
        "nodejs_eventloop_lag_p90_seconds": 0.013352959,
        "nodejs_eventloop_lag_p99_seconds": 0.047316991,
        "nodejs_eventloop_lag_max_seconds": 2.522873855,
        "nodejs_heap_size_used_bytes": 245614088,
        "nodejs_heap_size_total_bytes": 256180224,
        "workflow_execution_duration_seconds": {
            "trigger": {
                "success": {"count": 191, "sum_seconds": 1088.99},
                "failed":  {"count": 31,  "sum_seconds": 112.15},
            },
            "webhook": {
                "failed": {"count": 1, "sum_seconds": 4804.76},
            },
        },
    },

    # Event loop P99 por container
    "eventloop_p99_seconds": {
        "n8n-n8n_editor-1": 0.056721407,
        "n8n-n8n_worker-1": 0.074448895,
        "n8n-n8n_worker-2": 0.060817407,
        "n8n-n8n_worker-3": 0.076939263,
    },

    # RabbitMQ
    "rabbitmq_queues": [
        {"name": "externally_configured_queue", "messages": 0, "ready": 0,
         "unacked": 0, "consumers": 0},
        {"name": "service_publish_queue",       "messages": 0, "ready": 0,
         "unacked": 0, "consumers": 0},
        {"name": "service_incoming_queue",      "messages": 0, "ready": 0,
         "unacked": 0, "consumers": 0},
        {"name": "global",                      "messages": 0, "ready": 0,
         "unacked": 0, "consumers": 1},
    ],

    # PostgreSQL execution_entity
    "postgres": {
        "totals": {
            "total": 5074,
            "last_24h": 5049,
            "last_7d": 5069,
            "waiting": 257,
            "running": 0,
            "oldest": "2025-06-05T10:40:13-03:00",
            "newest": "2026-05-08T11:45:57-03:00",
        },
        "by_status_24h": [
            {"status": "success",  "mode": "webhook", "count": 4217, "avg_sec": -10322.50, "max_sec": 68.68},
            {"status": "success",  "mode": "trigger", "count": 312,  "avg_sec": -4078.71,  "max_sec": 744.91},
            {"status": "waiting",  "mode": "webhook", "count": 236,  "avg_sec": 10836.03,  "max_sec": 50529.10},
            {"status": "crashed",  "mode": "webhook", "count": 133,  "avg_sec": 15947.23,  "max_sec": 26874.96},
            {"status": "error",    "mode": "trigger", "count": 90,   "avg_sec": -6836.88,  "max_sec": 67.49},
            {"status": "error",    "mode": "webhook", "count": 41,   "avg_sec": -9414.66,  "max_sec": 11.87},
            {"status": "crashed",  "mode": "trigger", "count": 13,   "avg_sec": -2343.10,  "max_sec": 460.39},
            {"status": "success",  "mode": "manual",  "count": 4,    "avg_sec": -10799.36, "max_sec": -10799.03},
        ],
        "hourly_last_12h": [
            {"hour": "2026-05-08T11:00-03:00", "total": 115, "success": 59, "errors": 6},
            {"hour": "2026-05-08T10:00-03:00", "total": 112, "success": 34, "errors": 6},
            {"hour": "2026-05-08T09:00-03:00", "total": 141, "success": 64, "errors": 11},
            {"hour": "2026-05-08T08:00-03:00", "total": 112, "success": 96, "errors": 7},
            {"hour": "2026-05-08T07:00-03:00", "total": 27,  "success": 21, "errors": 6},
            {"hour": "2026-05-08T06:00-03:00", "total": 16,  "success": 12, "errors": 0},
            {"hour": "2026-05-08T05:00-03:00", "total": 12,  "success": 12, "errors": 0},
            {"hour": "2026-05-08T04:00-03:00", "total": 12,  "success": 12, "errors": 0},
            {"hour": "2026-05-08T03:00-03:00", "total": 13,  "success": 12, "errors": 0},
            {"hour": "2026-05-08T02:00-03:00", "total": 12,  "success": 12, "errors": 0},
            {"hour": "2026-05-08T01:00-03:00", "total": 18,  "success": 12, "errors": 0},
            {"hour": "2026-05-08T00:00-03:00", "total": 19,  "success": 14, "errors": 1},
            {"hour": "2026-05-07T23:00-03:00", "total": 2,   "success": 2,  "errors": 0},
        ],
        "waiting_by_workflow": [
            {
                "workflow": "hub-whatsapp-api-gateway-evolution-api",
                "count": 256,
                "oldest": "2026-05-04T18:59:09-03:00",
                "newest": "2026-05-08T11:44:36-03:00",
            },
            {
                "workflow": "contrato-licitacao",
                "count": 1,
                "oldest": "2025-10-23T12:05:33-03:00",
                "newest": "2025-10-23T12:05:33-03:00",
            },
        ],
    },

    # Prometheus
    "prometheus": {
        "version": "v3.2.1",
        "uptime_days": 3,
        "n8n_target_status": "down",
        "n8n_target_error": (
            "Get 'http://31.220.103.208:5678/metrics': dial tcp 31.220.103.208:5678: "
            "i/o timeout (firewall blocks external access to port 5678)"
        ),
        "available_targets_up": [
            "alertmanager", "cadvisor", "cadvisor-wf008", "docker", "docker-wf008",
            "grafana", "loki", "mysql-wfdb02", "node-exporter", "node-wf001",
            "node-wf008", "node-wfdb02", "postgres-exporter", "postgres-wfdb02",
            "prometheus", "promtail", "pushgateway_wfdb01", "victoriametrics",
        ],
        "available_targets_down": ["n8n", "traefik"],
    },
}


# ---------------------------------------------------------------------------
# Analise
# ---------------------------------------------------------------------------

def analyze(snap: dict) -> dict:
    """Processa snapshot e retorna dict com analise e alertas."""

    pg = snap["postgres"]
    totals = pg["totals"]
    by_status = pg["by_status_24h"]
    hourly = pg["hourly_last_12h"]
    stats_t1 = snap["docker_stats_t1"]
    eloop = snap["eventloop_p99_seconds"]
    metrics = snap["n8n_metrics_editor"]

    # ---- Taxa de sucesso 24h ----
    success_24h = sum(
        r["count"] for r in by_status if r["status"] == "success"
    )
    error_24h = sum(
        r["count"] for r in by_status if r["status"] in ("error", "crashed")
    )
    waiting_24h = sum(
        r["count"] for r in by_status if r["status"] == "waiting"
    )
    total_completed_24h = success_24h + error_24h
    error_rate_24h = (
        round(error_24h / total_completed_24h * 100, 2)
        if total_completed_24h > 0 else 0
    )

    # ---- Throughput peak ----
    peak_hour = max(hourly, key=lambda h: h["total"]) if hourly else {}
    avg_throughput_biz = round(
        sum(h["total"] for h in hourly if h["total"] > 20) /
        max(len([h for h in hourly if h["total"] > 20]), 1),
        1,
    )

    # ---- CPU workers ----
    workers = [s for s in stats_t1 if "worker" in s["name"]]
    max_worker_cpu = max(w["cpu_pct"] for w in workers) if workers else 0
    hot_worker = (
        max(workers, key=lambda w: w["cpu_pct"])["name"] if workers else "N/A"
    )

    # ---- Memoria total ----
    total_mem_mib = sum(s["mem_mib"] for s in stats_t1)

    # ---- Event loop ----
    max_eloop_p99 = max(eloop.values()) if eloop else 0
    eloop_container = max(eloop, key=eloop.get) if eloop else "N/A"

    # ---- Metricas editor (acumulado 13h uptime) ----
    exec_metrics = metrics["workflow_execution_duration_seconds"]
    trigger_success_count = exec_metrics["trigger"]["success"]["count"]
    trigger_success_avg = round(
        exec_metrics["trigger"]["success"]["sum_seconds"] / trigger_success_count, 2
    )
    trigger_failed_count = exec_metrics["trigger"]["failed"]["count"]

    # ---- Alertas ----
    alerts = []

    if waiting_24h > 50:
        alerts.append({
            "severity": "CRITICO",
            "category": "stuck_executions",
            "message": (
                f"{totals['waiting']} execucoes em 'waiting' (acumulado) — "
                f"256 do workflow 'hub-whatsapp-api-gateway-evolution-api' "
                f"paradas ha 4+ dias (desde 2026-05-04)"
            ),
            "impact": "Consumo de memoria/conexoes DB, risco de timeout progressivo",
            "action": (
                "Investigar e limpar execucoes stuck: "
                "verificar se webhook de retorno esta configurado; "
                "considerar N8N_EXECUTIONS_TIMEOUT para forcar finalizacao"
            ),
        })

    if max_worker_cpu > 80:
        alerts.append({
            "severity": "ALTO",
            "category": "cpu_spike",
            "message": (
                f"Worker com CPU {max_worker_cpu:.1f}% ({hot_worker}) — "
                "pico detectado; rotacao de hot-worker observada entre medicoes"
            ),
            "impact": "Potencial degradacao de throughput; risco de OOM sob carga",
            "action": (
                "Monitorar por 24h; se persistir, verificar workflow com loop "
                "infinito ou alto volume de execucoes concorrentes"
            ),
        })

    if error_rate_24h > 5:
        alerts.append({
            "severity": "MEDIO",
            "category": "error_rate",
            "message": (
                f"Taxa de erro {error_rate_24h:.1f}% nas ultimas 24h "
                f"({error_24h} erros em {total_completed_24h} execucoes)"
            ),
            "impact": "Execucoes de cliente falhando; pode haver impacto em SLA",
            "action": "Revisar logs de workflows com status error/crashed (modo webhook)",
        })

    if snap["prometheus"]["n8n_target_status"] == "down":
        alerts.append({
            "severity": "ALTO",
            "category": "observability_gap",
            "message": (
                "Prometheus NAO consegue raspar metricas N8N: "
                "porta 5678 de wf001 bloqueada por firewall para wfdb01"
            ),
            "impact": (
                "Sem series temporais de metricas N8N no Prometheus/VictoriaMetrics; "
                "avaliacao atual baseada em coleta pontual direta"
            ),
            "action": (
                "Solucao 1: Expor /metrics via Traefik com rota interna ou basicauth. "
                "Solucao 2: Adicionar UFW rule allow from wfdb01 to port 5678 em wf001. "
                "Solucao 3: Configurar PushGateway para N8N empurrar metricas"
            ),
        })

    webhook_failed_long = [
        r for r in by_status
        if r["status"] in ("error", "crashed") and r["mode"] == "webhook" and r.get("max_sec", 0) > 3600
    ]
    if webhook_failed_long:
        alerts.append({
            "severity": "MEDIO",
            "category": "long_failed_webhook",
            "message": (
                f"133 execucoes webhook crashed com duracao media 15947s (~4.4h) "
                f"e max 26874s (~7.5h)"
            ),
            "impact": "Execucoes mantidas em memoria por horas antes de crashar; pressao sobre DB",
            "action": "Configurar EXECUTIONS_TIMEOUT ou revisar workflows com timeout longo",
        })

    # ---- Nota sobre timestamps negativos ----
    notes = [
        "NOTA: avg_sec negativas em status 'success' sao artefato de fuso horario "
        "no PostgreSQL (startedAt e stoppedAt com timezone offset diferente). "
        "Duracao real deve ser inferida pelo endpoint /metrics ou logs.",

        "NOTA: Modo de fila alterado de Bull/Redis para RabbitMQ — "
        "feature F16 (queue metrics) precisa de revisao para suportar RabbitMQ. "
        "Metricas de fila Bull nao existem nesta configuracao.",

        f"NOTA: wfdb01 (teste) ainda roda N8N 2.19.1; wf001 (producao) em 2.19.5. "
        "Sem comparativo de metricas de versao anterior disponivel "
        "(Prometheus gap coincide com periodo do upgrade).",
    ]

    return {
        "summary": {
            "version": snap["n8n_version"],
            "collected_at": snap["collected_at"],
            "containers_uptime_hours": snap["containers_uptime_hours"],
            "active_workflows": metrics["active_workflow_count"],
            "queue_mode": snap["queue_mode"],
            "rabbitmq_queue_backlog": sum(
                q["messages"] for q in snap["rabbitmq_queues"]
            ),
        },
        "throughput": {
            "executions_last_24h": totals["last_24h"],
            "success_24h": success_24h,
            "error_24h": error_24h,
            "waiting_24h": waiting_24h,
            "error_rate_pct": error_rate_24h,
            "peak_hour": peak_hour.get("hour"),
            "peak_total": peak_hour.get("total"),
            "avg_throughput_business_hours_per_hour": avg_throughput_biz,
            "trigger_success_count_since_restart": trigger_success_count,
            "trigger_success_avg_duration_sec": trigger_success_avg,
            "trigger_failed_count_since_restart": trigger_failed_count,
        },
        "resources": {
            "total_n8n_memory_mib": round(total_mem_mib, 1),
            "host_total_memory_gib": 31.34,
            "n8n_memory_pct_host": round(total_mem_mib / (31.34 * 1024) * 100, 2),
            "max_worker_cpu_pct": max_worker_cpu,
            "hot_worker": hot_worker,
            "eventloop_p99_max_seconds": max_eloop_p99,
            "eventloop_p99_container": eloop_container,
            "eventloop_p99_by_container": eloop,
        },
        "stuck_executions": {
            "total_waiting": totals["waiting"],
            "by_workflow": pg["waiting_by_workflow"],
        },
        "observability": {
            "prometheus_n8n_target": snap["prometheus"]["n8n_target_status"],
            "prometheus_error": snap["prometheus"]["n8n_target_error"],
            "victoriametrics_n8n_data": False,
            "data_source_this_evaluation": "direct_ssh_docker_exec + postgresql",
        },
        "alerts": alerts,
        "notes": notes,
        "raw_snapshot": snap,
    }


def print_report(analysis: dict) -> None:
    """Imprime relatorio formatado."""
    s = analysis["summary"]
    t = analysis["throughput"]
    r = analysis["resources"]
    stuck = analysis["stuck_executions"]

    print()
    print("=" * 70)
    print(f"  N8N PERFORMANCE EVALUATION — v{s['version']}")
    print(f"  Coletado: {s['collected_at']}")
    print(f"  Uptime containers: {s['containers_uptime_hours']}h")
    print("=" * 70)

    print("\n--- THROUGHPUT (24h) ---")
    print(f"  Total execucoes : {t['executions_last_24h']:,}")
    print(f"  Sucesso         : {t['success_24h']:,}")
    print(f"  Erro/Crash      : {t['error_24h']:,}  ({t['error_rate_pct']:.1f}%)")
    print(f"  Waiting (24h)   : {t['waiting_24h']:,}")
    print(f"  Pico por hora   : {t['peak_total']} em {t['peak_hour']}")
    print(f"  Media biz hours : {t['avg_throughput_business_hours_per_hour']:.1f} exec/h")
    print(f"  Avg duracao trigger (desde restart): {t['trigger_success_avg_duration_sec']}s")

    print("\n--- RECURSOS ---")
    print(f"  Mem total N8N   : {r['total_n8n_memory_mib']:.0f} MiB ({r['n8n_memory_pct_host']:.1f}% host)")
    print(f"  CPU pico worker : {r['max_worker_cpu_pct']:.1f}% ({r['hot_worker']})")
    print(f"  Event loop P99  : {r['eventloop_p99_max_seconds']*1000:.1f}ms ({r['eventloop_p99_container']})")
    print(f"  RabbitMQ backlog: {analysis['summary']['rabbitmq_queue_backlog']} msgs")

    print("\n--- EXECUCOES STUCK ---")
    print(f"  Total waiting   : {stuck['total_waiting']}")
    for wf in stuck["by_workflow"]:
        print(f"  - {wf['workflow']}: {wf['count']} ({wf['oldest'][:10]} ate {wf['newest'][:10]})")

    print("\n--- ALERTAS ---")
    for a in analysis["alerts"]:
        print(f"  [{a['severity']}] {a['category']}")
        print(f"    {a['message'][:80]}")
        print(f"    Acao: {a['action'][:80]}")
        print()

    print("--- OBSERVABILIDADE ---")
    obs = analysis["observability"]
    print(f"  Prometheus n8n target: {obs['prometheus_n8n_target'].upper()}")
    print(f"  VictoriaMetrics n8n  : {'OK' if obs['victoriametrics_n8n_data'] else 'SEM DADOS'}")
    print(f"  Fonte desta avaliacao: {obs['data_source_this_evaluation']}")

    print("\n--- NOTAS ---")
    for note in analysis["notes"]:
        print(f"  * {note[:80]}")
        if len(note) > 80:
            print(f"    {note[80:160]}")
    print()


def main() -> None:
    if len(sys.argv) > 1:
        snap_path = Path(sys.argv[1])
        print(f"Carregando snapshot: {snap_path}")
        with open(snap_path, encoding="utf-8") as f:
            snap = json.load(f)
    else:
        snap = SNAPSHOT

    analysis = analyze(snap)

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(analysis, f, indent=2, default=str, ensure_ascii=False)

    print_report(analysis)
    print(f"[OK] Analise salva em: {OUTPUT}")


if __name__ == "__main__":
    main()

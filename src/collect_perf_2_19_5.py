"""
collect_perf_2_19_5.py
======================
Coleta e persiste snapshot de desempenho N8N 2.19.5 via SSH SPA.

Fontes:
  - Endpoint /metrics de cada container N8N (docker exec via SSH)
  - PostgreSQL execution_entity via docker run postgres:16-alpine
  - RabbitMQ rabbitmqctl via docker exec
  - docker stats snapshot

Saida: tmp/<nome>_YYYYMMDD_HHMMSS.json

Uso:
    uv run python src/collect_perf_2_19_5.py
"""

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
TMP = ROOT / "tmp"
TMP.mkdir(exist_ok=True)

TS = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
OUTPUT = TMP / f"perf_n8n_2_19_5_{TS}.json"

SSH_WF001 = ["~/.local/bin/ssh-wf001"]
SSH_WFDB01_KNOCK = "fwknop --rc-file ~/.fwknoprc -n wfdb01"
PGPASS = "cheYaStLphLstuzI6His"
PGHOST = "82.197.64.145"
PGPORT = "5432"
PGUSER = "n8n_user"
PGDB = "n8n_db"

N8N_CONTAINERS = [
    "n8n-n8n_editor-1",
    "n8n-n8n_worker-1",
    "n8n-n8n_worker-2",
    "n8n-n8n_worker-3",
    "n8n-n8n_webhook-1",
    "n8n-n8n_webhook-2",
    "n8n-n8n_webhook-3",
    "n8n-n8n_mcp-1",
]


def run_ssh(script: str, host: str = "wf001") -> str:
    """Executa comando via SSH SPA."""
    if host == "wf001":
        cmd = f"~/.local/bin/ssh-wf001 '{script}'"
    else:
        cmd = (
            f"fwknop --rc-file ~/.fwknoprc -n wfdb01 && sleep 4 && "
            f"ssh -p 5010 -i ~/.ssh/id_rsa -o StrictHostKeyChecking=no "
            f"archaris@wfdb01.vya.digital '{script}'"
        )
    result = subprocess.run(
        cmd, shell=True, capture_output=True, text=True, timeout=90
    )
    return result.stdout.strip()


def collect_metrics_container(container: str) -> dict:
    """Coleta metricas Prometheus de um container N8N."""
    script = (
        f"docker exec {container} wget -qO- http://localhost:5678/metrics 2>/dev/null"
        r" | grep -v '^#'"
    )
    raw = run_ssh(script)
    metrics = {}
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.rsplit(" ", 1)
        if len(parts) == 2:
            key, val = parts
            try:
                metrics[key] = float(val)
            except ValueError:
                metrics[key] = val
    return metrics


def collect_docker_stats() -> list:
    """Coleta docker stats snapshot de todos containers N8N."""
    script = (
        "docker stats --no-stream --format "
        '"{{.Name}}|{{.CPUPerc}}|{{.MemUsage}}|{{.MemPerc}}|{{.NetIO}}|{{.BlockIO}}" '
        "$(docker ps --filter 'name=n8n' --format '{{.Names}}')"
    )
    raw = run_ssh(script)
    stats = []
    for line in raw.splitlines():
        parts = line.split("|")
        if len(parts) == 6:
            stats.append(
                {
                    "name": parts[0],
                    "cpu_pct": parts[1],
                    "mem_usage": parts[2],
                    "mem_pct": parts[3],
                    "net_io": parts[4],
                    "block_io": parts[5],
                }
            )
    return stats


def collect_rabbitmq_queues() -> list:
    """Coleta estado das filas RabbitMQ."""
    script = (
        "docker exec rabbitmq rabbitmqctl list_queues -p / "
        "name messages messages_ready messages_unacknowledged consumers "
        "--no-table-headers 2>&1 | grep -v '^Timeout\\|^Listing'"
    )
    raw = run_ssh(script)
    queues = []
    for line in raw.splitlines():
        parts = line.strip().split()
        if len(parts) >= 5:
            queues.append(
                {
                    "name": parts[0],
                    "messages": int(parts[1]),
                    "ready": int(parts[2]),
                    "unacked": int(parts[3]),
                    "consumers": int(parts[4]),
                }
            )
    return queues


def collect_postgres_stats() -> dict:
    """Coleta estatisticas de execucoes via PostgreSQL."""
    base_cmd = (
        "docker run --rm --network host "
        f"-e PGPASSWORD={PGPASS} "
        "postgres:16-alpine "
        f"psql -h {PGHOST} -p {PGPORT} -U {PGUSER} -d {PGDB} -t -A -F'|' -c "
    )

    # Execucoes 24h por status/modo
    q_24h = (
        "\"SELECT status, mode, COUNT(*) as count, "
        "ROUND(AVG(EXTRACT(EPOCH FROM (\\\"stoppedAt\\\" - \\\"startedAt\\\")))::numeric,2) as avg_sec, "
        "ROUND(MAX(EXTRACT(EPOCH FROM (\\\"stoppedAt\\\" - \\\"startedAt\\\")))::numeric,2) as max_sec "
        "FROM execution_entity "
        "WHERE \\\"startedAt\\\" > NOW() - INTERVAL '24 hours' "
        "  AND \\\"stoppedAt\\\" IS NOT NULL "
        "GROUP BY status, mode ORDER BY count DESC;\""
    )

    # Totais gerais
    q_total = (
        "\"SELECT COUNT(*) as total, "
        "COUNT(*) FILTER (WHERE \\\"startedAt\\\" > NOW() - INTERVAL '24 hours') as h24, "
        "COUNT(*) FILTER (WHERE status = 'waiting') as waiting, "
        "COUNT(*) FILTER (WHERE status = 'running') as running, "
        "MIN(\\\"startedAt\\\") as oldest, MAX(\\\"startedAt\\\") as newest "
        "FROM execution_entity;\""
    )

    # Taxa horaria 12h
    q_hourly = (
        "\"SELECT DATE_TRUNC('hour', \\\"startedAt\\\") as hour, "
        "COUNT(*) as total, "
        "COUNT(*) FILTER (WHERE status = 'success') as success, "
        "COUNT(*) FILTER (WHERE status IN ('error','crashed')) as errors "
        "FROM execution_entity "
        "WHERE \\\"startedAt\\\" > NOW() - INTERVAL '12 hours' "
        "GROUP BY hour ORDER BY hour DESC;\""
    )

    # Workflows em waiting
    q_waiting = (
        "\"SELECT w.name, COUNT(e.id) as count, "
        "MIN(e.\\\"startedAt\\\") as oldest, MAX(e.\\\"startedAt\\\") as newest "
        "FROM execution_entity e "
        "JOIN workflow_entity w ON e.\\\"workflowId\\\" = w.id::text "
        "WHERE e.status = 'waiting' "
        "GROUP BY w.name ORDER BY count DESC LIMIT 10;\""
    )

    def run_query(q: str) -> str:
        script = base_cmd + q
        return run_ssh(script, host="wfdb01")

    def parse_rows(raw: str) -> list:
        rows = []
        for line in raw.splitlines():
            if "|" in line and not line.startswith("ERROR"):
                rows.append(line.strip().split("|"))
        return rows

    r24h_raw = run_query(q_24h)
    rtotal_raw = run_query(q_total)
    rhourly_raw = run_query(q_hourly)
    rwaiting_raw = run_query(q_waiting)

    by_status = []
    for row in parse_rows(r24h_raw):
        if len(row) >= 5:
            by_status.append(
                {
                    "status": row[0],
                    "mode": row[1],
                    "count": int(row[2]),
                    "avg_sec": float(row[3]) if row[3] else None,
                    "max_sec": float(row[4]) if row[4] else None,
                }
            )

    total = {}
    for row in parse_rows(rtotal_raw):
        if len(row) >= 6:
            total = {
                "total": int(row[0]),
                "last_24h": int(row[1]),
                "waiting": int(row[2]),
                "running": int(row[3]),
                "oldest": row[4],
                "newest": row[5],
            }

    hourly = []
    for row in parse_rows(rhourly_raw):
        if len(row) >= 4:
            hourly.append(
                {
                    "hour": row[0],
                    "total": int(row[1]),
                    "success": int(row[2]),
                    "errors": int(row[3]),
                }
            )

    waiting_wf = []
    for row in parse_rows(rwaiting_raw):
        if len(row) >= 4:
            waiting_wf.append(
                {
                    "workflow": row[0],
                    "count": int(row[1]),
                    "oldest": row[2],
                    "newest": row[3],
                }
            )

    return {
        "by_status_24h": by_status,
        "totals": total,
        "hourly_last_12h": hourly,
        "waiting_by_workflow": waiting_wf,
    }


def main() -> None:
    print(f"[collect_perf_2_19_5] Iniciando coleta — {TS}")

    result = {
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "n8n_version": "2.19.5",
        "host": "wf001.vya.digital",
        "queue_mode": "rabbitmq",
        "containers": {},
        "docker_stats": [],
        "rabbitmq_queues": [],
        "postgres": {},
    }

    print("  [1/4] Coletando metricas de containers...")
    for container in N8N_CONTAINERS:
        print(f"        {container}")
        result["containers"][container] = collect_metrics_container(container)

    print("  [2/4] Coletando docker stats...")
    result["docker_stats"] = collect_docker_stats()

    print("  [3/4] Coletando filas RabbitMQ...")
    result["rabbitmq_queues"] = collect_rabbitmq_queues()

    print("  [4/4] Coletando PostgreSQL...")
    result["postgres"] = collect_postgres_stats()

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, default=str, ensure_ascii=False)

    print(f"\n[OK] Salvo em: {OUTPUT}")
    print(f"     Tamanho: {OUTPUT.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    main()

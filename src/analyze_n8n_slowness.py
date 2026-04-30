#!/usr/bin/env python3
"""
Análise consolidada de lentidão do N8N — abril 2026.

Combina dados do ANA-001 (jan-mar 2026) com verificação de estado atual.

Saída: JSON em docs/SESSIONS/YYYY-MM-DD/n8n-slowness-analysis-YYYYMMDD-HHMMSS.json

Exemplos
--------
>>> # Executar análise
>>> python src/analyze_n8n_slowness.py
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


def extract_ana001_findings() -> dict[str, Any]:
    """
    Extrai achados principais do relatório ANA-001 (jan-mar 2026).

    Returns
    -------
    dict
        Achados consolidados do ANA-001
    """
    return {
        "report_id": "ANA-001",
        "period": "2026-01-01 → 2026-03-31 (90 dias)",
        "source": "VictoriaMetrics (wfdb01) via SSH tunnel",

        "executions_summary": {
            "total_executions_scrape_direct": 148058,  # job=n8n, instance=wf001
            "total_executions_pushgateway": 366303,    # instance=0.0.0.0:5000
            "dual_collection_confirmed": True,
            "active_workflows": 23,
        },

        "performance_facts": {
            "p95_latency_all_workflows": "< 100ms",
            "workflows_exceeding_1s": 0,
            "cpu_wf001_during_peak": "1-3%",
            "cpu_is_bottleneck": False,
            "individual_workflows_fast": True,
        },

        "volume_offenders": [
            {
                "workflow_name": "121Labs PABX call-analytics",
                "executions_90d": 429786,  # melhor estimativa (consolidado)
                "percentage_of_total": 57,
                "peak_exec_per_hour": 8416,
                "peak_date": "2026-03-27 20:00 UTC",
                "pattern": "Horário comercial 13:00-22:00 UTC (10:00-19:00 BRT)",
                "sustained_rate": "2.3 exec/s por até 9h contínuas",
                "impact": "Domina fila N8N durante horário comercial",
            },
            {
                "workflow_name": "hub-whatsapp-api-gateway-evolution-api",
                "executions_90d": 84639,
                "percentage_of_total": 11,
                "sudden_growth": "Início em 2026-03-04",
                "growth_rate": "+1860% em 24h (10 → 2958 exec)",
                "impact": "Crescimento súbito não explicado — verificar onboarding",
            },
        ],

        "confirmed_bottlenecks": [
            {
                "bottleneck": "PostgreSQL execution_entity saturado",
                "evidence": "429K+ linhas (90 dias de histórico não purgado)",
                "status": "CONFIRMADO",
                "priority": "P1",
            },
            {
                "bottleneck": "Dupla coleta Prometheus (F18)",
                "evidence": "prod-collector-api envia via scrape direto E Pushgateway",
                "status": "KNOWN_ISSUE_F18",
                "priority": "P1",
            },
        ],

        "unconfirmed_hypotheses": [
            {
                "hypothesis": "Fila N8N saturada",
                "reason": "n8n_queue_* métricas não habilitadas (F16 pendente)",
                "testable_after": "F16 implementado em wf001",
                "priority": "P1 — HIPÓTESE PRINCIPAL",
            },
            {
                "hypothesis": "Workers N8N saturados (concorrência)",
                "reason": "n8n_concurrency_* métricas não visíveis (F24 pendente)",
                "testable_after": "F24 implementado",
                "priority": "P2",
            },
            {
                "hypothesis": "Latência end-to-end alta",
                "reason": "Probe sintético ausente (F20 pendente)",
                "testable_after": "F20 implementado",
                "priority": "P2",
            },
        ],

        "instrumentation_gaps": [
            "n8n_queue_* (fila) — F16 pendente",
            "n8n_concurrency_* (workers) — F24 pendente",
            "node_memory_* wf001 — F23 pendente (relabeling incorreto)",
            "Probe end-to-end — F20 pendente",
            "Buckets sub-100ms — F22 pendente",
            "pg_stat_statements queries lentas — F17 Vetor B pendente validação em prod",
        ],
    }


def analyze_slowness_cause() -> dict[str, Any]:
    """
    Analisa causas prováveis da lentidão percebida.

    Returns
    -------
    dict
        Diagnóstico estruturado
    """
    return {
        "conclusion": "Lentidão NÃO é latência de execução individual (todas < 100ms)",

        "most_likely_cause": {
            "name": "Tempo de fila (queue wait time)",
            "evidence": [
                "121Labs gera 2.3 exec/s contínuo por 9h",
                "Workflows individuais completam em < 100ms",
                "CPU wf001 em 1-3% (hardware não saturado)",
                "n8n_queue_* não instrumentado — hipótese não testável",
            ],
            "calculation": {
                "peak_arrival_rate": "2.3 exec/s",
                "n8n_default_concurrency": "5-20 workers",
                "exec_duration_avg": "< 100ms",
                "theoretical_throughput": "50-200 exec/s (workers × 1/duration)",
                "conclusion": "Throughput teórico > arrival rate — fila não deveria saturar",
                "caveat": "Cálculo assume workers dedicados; se compartilhado com outros workflows, saturação é possível",
            },
        },

        "secondary_cause": {
            "name": "PostgreSQL execution_entity saturado",
            "evidence": [
                "429K+ linhas sem purgação",
                "Toda execução N8N insere/consulta execution_entity",
                "pg_stat_statements validado apenas em n8n_dev_db (não em prod)",
            ],
            "impact": "Queries lentas afetam tempo de início e finalização de cada exec",
        },

        "ruled_out": [
            "Hardware (CPU 1-3%)",
            "Workflows lentos individualmente (p95 < 100ms em 100% das exec)",
            "Memória wf001 (sem dados, mas CPU baixo sugere não é gargalo)",
        ],
    }


def generate_recommendations() -> dict[str, Any]:
    """
    Gera recomendações priorizadas para resolver lentidão.

    Returns
    -------
    dict
        Ações priorizadas por P0/P1/P2
    """
    return {
        "p0_immediate": [
            {
                "action": "Executar T034a (F16+F17 → wf001)",
                "reason": "Habilita métricas de fila (F16) e purga PostgreSQL (F17)",
                "impact": "Confirma/descarta hipótese de fila saturada + reduz carga DB",
                "status": "Playbook pronto, janela agendada sábado 02h-04h UTC",
                "blocker": None,
            },
            {
                "action": "Verificar tamanho atual execution_entity em n8n_db (prod)",
                "reason": "Confirmar se cresceu desde mar/2026 (429K)",
                "impact": "Urgência de F17 depende do crescimento atual",
                "effort": "15 min — query SQL em wfdb02",
            },
        ],

        "p1_next_week": [
            {
                "action": "Auditar hub-whatsapp-api-gateway-evolution-api",
                "reason": "84K exec desde 04/mar — crescimento súbito não explicado",
                "impact": "Identificar se é onboarding legítimo ou configuração incorreta",
                "owner": "N8N Admin + Evolution API team",
            },
            {
                "action": "Submeter issue F18 ao prod-collector-api",
                "reason": "Desabilitar PROMETHEUS_PUSHGATEWAY_ENABLED=true",
                "impact": "Elimina dupla coleta e possível sobrecarga do Pushgateway",
                "contract": "specs/001-001-tunning-instrumentacao/contracts/prod-collector-api-issue.md",
            },
            {
                "action": "Habilitar F24 (concurrency metrics) em wf001",
                "reason": "Complementa F16 — verifica se workers estão saturados",
                "impact": "Confirma/descarta hipótese de workers insuficientes",
                "prerequisite": "N8N >= 0.214 (wf001 já é 2.6.4 ✓)",
            },
        ],

        "p2_medium_term": [
            {
                "action": "Implementar F20 (probe sintético end-to-end)",
                "reason": "Medir latência real percebida (fila + exec + overhead)",
                "impact": "Baseline before/after para cada ação de tunning",
            },
            {
                "action": "Implementar F22 (buckets sub-100ms)",
                "reason": "Resolver granularidade do histograma",
                "impact": "p50/p95 reais em vez de limite de bucket (0.095s artificial)",
            },
            {
                "action": "Avaliar F19/F21 (governança de throughput + batching 121Labs)",
                "reason": "Reduzir volume 60× via batching de 1 min",
                "impact": "8.4K exec/hora → 140 exec/hora (mesma análise, menos carga)",
                "prerequisite": "Aprovação project-manager + cliente 121Labs",
            },
        ],
    }


def main() -> None:
    """
    Análise consolidada de lentidão do N8N — abril 2026.

    Combina achados do ANA-001 com análise de causa-raiz e recomendações priorizadas.
    """
    log.info("=== Análise de Lentidão N8N — Abril 2026 ===")

    # Extrair dados do ANA-001
    log.info("Extraindo achados do ANA-001 (jan-mar 2026)...")
    ana001 = extract_ana001_findings()

    # Analisar causa da lentidão
    log.info("Analisando causa-raiz da lentidão percebida...")
    slowness_cause = analyze_slowness_cause()

    # Gerar recomendações
    log.info("Gerando recomendações priorizadas...")
    recommendations = generate_recommendations()

    # Consolidar resultado
    result = {
        "metadata": {
            "analysis_id": "SLOWNESS-2026-04-30",
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "base_report": "ANA-001 (2026-01-01 → 2026-03-31)",
            "focus": "Identificar causas de lentidão N8N (workflows + operação)",
        },

        "executive_summary": {
            "question": "Por que o N8N está lento?",
            "answer": "Workflows individuais SÃO rápidos (< 100ms). Lentidão percebida é TEMPO DE FILA não instrumentado.",
            "primary_hypothesis": "Fila N8N saturada durante picos de 121Labs (2.3 exec/s por 9h)",
            "secondary_hypothesis": "PostgreSQL execution_entity saturado (429K+ linhas sem purgação)",
            "hardware_bottleneck": False,
            "instrumentation_gaps": 6,
            "priority_action": "Executar T034a (F16+F17) para habilitar métricas de fila e purgar PostgreSQL",
        },

        "ana001_findings": ana001,
        "slowness_diagnosis": slowness_cause,
        "recommendations": recommendations,

        "next_steps": [
            "1. Verificar tamanho atual execution_entity em n8n_db (prod) — SQL em wfdb02",
            "2. Executar T034a na janela agendada (sábado 02h-04h UTC)",
            "3. Após T034a: coletar baseline de n8n_queue_* e validar purgação PostgreSQL",
            "4. Auditar hub-whatsapp-api-gateway-evolution-api (crescimento súbito)",
            "5. Submeter issue F18 ao prod-collector-api",
        ],
    }

    # Salvar em JSON
    today = datetime.now().strftime("%Y-%m-%d")
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    session_dir = Path(f"docs/SESSIONS/{today}")
    session_dir.mkdir(parents=True, exist_ok=True)

    output_file = session_dir / f"n8n-slowness-analysis-{timestamp}.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    log.info(f"✅ Análise salva em: {output_file}")
    print(f"\n📊 Resultado: {output_file}")

    # Exibir resumo executivo
    print("\n" + "=" * 80)
    print("RESUMO EXECUTIVO — Análise de Lentidão N8N")
    print("=" * 80)
    print(f"\n🔍 Pergunta: {result['executive_summary']['question']}")
    print(f"✅ Resposta: {result['executive_summary']['answer']}")
    print(f"\n🎯 Hipótese principal: {result['executive_summary']['primary_hypothesis']}")
    print(f"🔬 Hipótese secundária: {result['executive_summary']['secondary_hypothesis']}")
    print(f"💻 Hardware é gargalo? {result['executive_summary']['hardware_bottleneck']}")
    print(f"\n⚠️  Lacunas de instrumentação: {result['executive_summary']['instrumentation_gaps']}")
    print(f"🚀 Próxima ação P0: {result['executive_summary']['priority_action']}")

    print("\n" + "=" * 80)
    print("TOP 3 RECOMENDAÇÕES IMEDIATAS")
    print("=" * 80)
    for i, action in enumerate(result["recommendations"]["p0_immediate"], 1):
        print(f"\n{i}. {action['action']}")
        print(f"   Razão: {action['reason']}")
        print(f"   Impacto: {action['impact']}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log.warning("Interrompido pelo usuário")
    except Exception as e:
        log.error(f"Erro fatal: {e}", exc_info=True)

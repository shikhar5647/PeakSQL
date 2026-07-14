"""Agent 10 · Query Pattern Analyzer — synthesizes the query shapes users will
run (metric × dimension × filter) from relationships + metrics, as reusable
templates for the text2sql runtime. Mines historical queries when provided."""
from __future__ import annotations

import uuid

from ..context import AgentContext

AID = "a10"


async def run(ctx: AgentContext, state: dict) -> dict:
    rels = state["a8"]["enriched_relationships"]
    metrics = state["a9"]["discovered_metrics"]
    historical = (state.get("options") or {}).get("historical_queries") or []

    if historical:
        ctx.think(AID, f"{len(historical)} historical queries provided — mining them for join/filter patterns…")
    else:
        ctx.think(AID, "No historical queries — synthesizing likely patterns from relationships × metrics.")

    patterns: list[dict] = []

    # metric-by-dimension: every SUM/COUNT metric grouped through each relationship of its base table
    rel_by_source: dict[str, list[dict]] = {}
    for r in rels:
        rel_by_source.setdefault(r["source_table"], []).append(r)

    for m in metrics:
        if m["calculation"]["aggregation_function"] not in ("SUM", "COUNT"):
            continue
        for r in rel_by_source.get(m["base_table"], []):
            patterns.append({
                "pattern_id": str(uuid.uuid4()),
                "pattern_name": f"{m['business_name']} by {r['target_table']}",
                "pattern_type": "aggregation",
                "frequency": None,
                "typical_structure": {
                    "select_columns": [m["calculation"]["formula"]],
                    "from_tables": [m["base_table"], r["target_table"]],
                    "join_path": [{"from_table": r["source_table"], "to_table": r["target_table"],
                                   "join_condition": r["join_path"]["join_condition"]}],
                    "common_filters": [{"column": f, "operator": ">=", "typical_values": ["<date>"]}
                                       for f in m["typical_filters"][:1]],
                    "group_by_columns": [f"{r['target_table']}.{r['target_column']}"],
                    "order_by_columns": [m["calculation"]["formula"] + " DESC"],
                },
                "natural_language_templates": [
                    f"Show me {m['business_name'].lower()} by {r['target_table'].replace('_', ' ')}",
                    f"Which {r['target_table'].replace('_', ' ')} have the highest "
                    f"{m['business_name'].lower()}?",
                ],
                "complexity_score": 0.4,
            })

    # date-range filter patterns per metric with a date filter
    for m in metrics:
        if not m["typical_filters"]:
            continue
        patterns.append({
            "pattern_id": str(uuid.uuid4()),
            "pattern_name": f"{m['business_name']} in date range",
            "pattern_type": "aggregation",
            "frequency": None,
            "typical_structure": {
                "select_columns": [m["calculation"]["formula"]],
                "from_tables": [m["base_table"]],
                "join_path": [],
                "common_filters": [{"column": f"{m['base_table']}.{m['typical_filters'][0]}",
                                    "operator": "BETWEEN", "typical_values": ["<start>", "<end>"]}],
                "group_by_columns": None,
                "order_by_columns": None,
            },
            "natural_language_templates": [
                f"What was the {m['business_name'].lower()} last month?",
                f"{m['business_name']} between <start> and <end>",
            ],
            "complexity_score": 0.2,
        })

    # common join paths (deduped from relationships)
    join_paths = [{
        "path_name": f"{r['source_table']} → {r['target_table']}",
        "tables_in_order": [r["source_table"], r["target_table"]],
        "join_sequence": [r["join_path"]["join_condition"]],
        "use_frequency": r["confidence_score"],
    } for r in rels]

    ctx.think(AID, f"Synthesized {len(patterns)} query templates and {len(join_paths)} canonical join paths.")
    for p in patterns[:4]:
        ctx.think(AID, f"Template: “{p['natural_language_templates'][0]}”")

    return {"query_patterns": patterns, "common_join_paths": join_paths,
            "_summary": f"{len(patterns)} templates · {len(join_paths)} join paths"}

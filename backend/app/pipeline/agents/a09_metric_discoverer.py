"""Agent 9 · Business Metric Discoverer — turns measure columns into named
business metrics with the natural-language variants users actually say
('revenue', 'total sales'…), plus KPI candidates."""
from __future__ import annotations

import uuid

from pydantic import BaseModel, Field

from ..context import AgentContext

AID = "a9"


class MetricNames(BaseModel):
    class Item(BaseModel):
        metric_id: str
        business_name: str
        natural_language_variants: list[str] = Field(default_factory=list)
        business_context: str = ""
    items: list[Item] = Field(default_factory=list)


async def run(ctx: AgentContext, state: dict) -> dict:
    schema, naming, descs = state["a1"], state["a3"], state["a4"]
    desc_by_table = {d["table_name"]: d for d in descs["descriptions"]}
    naming_by_table = {n["table_name"]: n for n in naming["naming_analysis"]}

    ctx.think(AID, "Scanning for measure columns and countable entities…")

    metrics: list[dict] = []
    for t in schema["tables"]:
        tname = t["table_name"]
        cols_naming = {c["column_name"]: c for c in naming_by_table.get(tname, {}).get("columns", [])}
        date_cols = [c["column_name"] for c in t["columns"]
                     if cols_naming.get(c["column_name"], {}).get("semantic_type") == "timestamp"]
        entity = desc_by_table.get(tname, {}).get("table_descriptions", {}).get("short", tname)

        for c in t["columns"]:
            n = cols_naming.get(c["column_name"], {})
            if n.get("semantic_type") != "measure":
                continue
            term = n.get("business_term", c["column_name"]).lower()
            for agg, prefix in (("SUM", "Total"), ("AVG", "Average")):
                metrics.append({
                    "metric_id": str(uuid.uuid4()),
                    "metric_name": f"{agg.lower()}_{tname}_{c['column_name']}",
                    "business_name": f"{prefix} {term}",
                    "metric_type": "aggregate",
                    "base_table": tname,
                    "base_column": c["column_name"],
                    "calculation": {
                        "aggregation_function": agg,
                        "formula": f"{agg}({tname}.{c['column_name']})",
                        "requires_grouping": False,
                        "group_by_dimensions": None,
                    },
                    "natural_language_variants": [f"{prefix.lower()} {term}", term],
                    "typical_filters": date_cols,
                    "common_comparisons": ["MoM", "YoY"] if date_cols else [],
                    "business_context": "",
                    "related_metrics": [],
                })
            ctx.think(AID, f"Measure `{tname}.{c['column_name']}` → metrics “Total {term}”, “Average {term}”.")

        # every transactional/master table is countable
        pk = next((c["column_name"] for c in t["columns"] if c["is_primary_key"]), None)
        if pk:
            metrics.append({
                "metric_id": str(uuid.uuid4()),
                "metric_name": f"count_{tname}",
                "business_name": f"{entity} count",
                "metric_type": "aggregate",
                "base_table": tname,
                "base_column": pk,
                "calculation": {"aggregation_function": "COUNT",
                                "formula": f"COUNT({tname}.{pk})",
                                "requires_grouping": False, "group_by_dimensions": None},
                "natural_language_variants": [f"number of {tname.replace('_', ' ')}",
                                              f"how many {tname.replace('_', ' ')}"],
                "typical_filters": date_cols,
                "common_comparisons": [],
                "business_context": "",
                "related_metrics": [],
            })

    # LLM refinement: better business names + NL variants + context
    if metrics:
        result = await ctx.llm.structured(
            agent_id=AID, label=f"name {len(metrics)} metrics in business language",
            system=("You name database metrics the way business users say them. For each metric, give the "
                    "best business_name, 3-5 natural_language_variants (e.g. 'revenue', 'sales'), "
                    "and one sentence of business_context."),
            user=str([{"metric_id": m["metric_id"], "formula": m["calculation"]["formula"],
                       "current_name": m["business_name"]} for m in metrics]),
            schema=MetricNames,
            fallback=lambda: MetricNames(items=[]),
        )
        by_id = {i.metric_id: i for i in result.items}
        renamed = 0
        for m in metrics:
            r = by_id.get(m["metric_id"])
            if r:
                m["business_name"] = r.business_name or m["business_name"]
                m["natural_language_variants"] = list(dict.fromkeys(
                    [v.lower() for v in r.natural_language_variants] + m["natural_language_variants"]))
                m["business_context"] = r.business_context
                renamed += 1
        if renamed:
            ctx.think(AID, f"LLM refined {renamed} metric names / variants.")

    # KPI candidates: tables with >=2 aggregate metrics
    by_table: dict[str, list[dict]] = {}
    for m in metrics:
        by_table.setdefault(m["base_table"], []).append(m)
    kpis = [{
        "kpi_name": f"{tname.replace('_', ' ').title()} performance",
        "component_metrics": [m["metric_id"] for m in ms[:4]],
        "business_importance": "important",
    } for tname, ms in by_table.items() if len(ms) >= 3]
    if kpis:
        ctx.think(AID, f"Proposed {len(kpis)} composite KPI candidate(s): {[k['kpi_name'] for k in kpis]}")

    return {"discovered_metrics": metrics, "kpi_candidates": kpis,
            "_summary": f"{len(metrics)} metrics · {len(kpis)} KPI candidates"}

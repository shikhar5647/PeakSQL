"""Agent 13 · Validation & QA — the gate (locked decision: gate, not report).

Cross-references the built KG against Agent 1's expected schema, computes
completeness/quality scores, and fails the run on critical gaps so a silently
broken KG never ships."""
from __future__ import annotations

import json
from datetime import datetime, timezone

from ..context import AgentContext

AID = "a13"

THRESHOLDS = {"tables_with_descriptions": 0.9, "columns_with_descriptions": 0.8,
              "relationship_confidence_avg": 0.5}


async def run(ctx: AgentContext, state: dict) -> dict:
    schema = state["a1"]
    kg_path = ctx.settings.runs_dir / ctx.run.run_id / "kg.json"
    kg = json.loads(kg_path.read_text())
    nodes, rels = kg["nodes"], kg["relationships"]
    ctx.think(AID, "Validating the freshly built KG against the expected schema and quality thresholds…")

    checks: list[dict] = []

    def check(name: str, ctype: str, passed: bool, severity: str, details: str,
              affected: list[str] | None = None) -> None:
        checks.append({"check_name": name, "check_type": ctype,
                       "status": "passed" if passed else "failed",
                       "severity": severity, "details": details,
                       "affected_entities": affected or []})
        icon = "✓" if passed else ("✗" if severity == "critical" else "⚠")
        ctx.think(AID, f"{icon} {name}: {details}")

    # --- completeness: every input table/column landed in the KG ---
    kg_tables = {n["properties"]["name"] for n in nodes if n["label"] == "Table"}
    expected_tables = {t["table_name"] for t in schema["tables"]}
    missing_tables = expected_tables - kg_tables
    check("all_tables_in_kg", "completeness", not missing_tables, "critical",
          f"{len(kg_tables)}/{len(expected_tables)} input tables present in KG"
          + (f" — MISSING: {sorted(missing_tables)}" if missing_tables else ""),
          sorted(missing_tables))

    kg_columns = {(n["properties"]["table"], n["properties"]["name"])
                  for n in nodes if n["label"] == "Column"}
    expected_columns = {(t["table_name"], c["column_name"])
                        for t in schema["tables"] for c in t["columns"]}
    missing_cols = expected_columns - kg_columns
    check("all_columns_in_kg", "completeness", not missing_cols, "critical",
          f"{len(kg_columns)}/{len(expected_columns)} input columns present in KG",
          [f"{t}.{c}" for t, c in sorted(missing_cols)])

    # --- description coverage ---
    tables_desc = [n for n in nodes if n["label"] == "Table" and n["properties"].get("description_short")]
    cols_desc = [n for n in nodes if n["label"] == "Column" and n["properties"].get("description_short")]
    n_tables = max(1, sum(1 for n in nodes if n["label"] == "Table"))
    n_cols = max(1, sum(1 for n in nodes if n["label"] == "Column"))
    t_score = len(tables_desc) / n_tables
    c_score = len(cols_desc) / n_cols
    check("table_description_coverage", "completeness",
          t_score >= THRESHOLDS["tables_with_descriptions"], "critical",
          f"{t_score:.0%} of tables have descriptions (threshold {THRESHOLDS['tables_with_descriptions']:.0%})")
    check("column_description_coverage", "completeness",
          c_score >= THRESHOLDS["columns_with_descriptions"], "warning",
          f"{c_score:.0%} of columns have descriptions (threshold {THRESHOLDS['columns_with_descriptions']:.0%})")

    # --- orphaned nodes (nothing referencing them) ---
    connected = {r["source"] for r in rels} | {r["target"] for r in rels}
    orphans = [n["id"] for n in nodes if n["id"] not in connected]
    check("no_orphaned_nodes", "consistency", not orphans, "warning",
          f"{len(orphans)} orphaned node(s)" if orphans else "every node is connected", orphans[:20])

    # --- relationship confidence audit ---
    rel_edges = [r for r in rels if r["type"] in ("FOREIGN_KEY", "IMPLICIT_RELATION")]
    confs = [r["properties"].get("confidence", 1.0) for r in rel_edges]
    conf_avg = sum(confs) / len(confs) if confs else 1.0
    low_conf = [f"{r['source']} → {r['target']}" for r in rel_edges
                if r["properties"].get("confidence", 1.0) < 0.6]
    check("relationship_confidence", "accuracy",
          conf_avg >= THRESHOLDS["relationship_confidence_avg"], "warning",
          f"avg confidence {conf_avg:.2f} across {len(rel_edges)} data relationships"
          + (f"; {len(low_conf)} low-confidence flagged for review" if low_conf else ""), low_conf)

    # --- synonym coverage ---
    syn_targets = {r["target"] for r in rels if r["type"] == "SYNONYM_OF"}
    entities = [n for n in nodes if n["label"] in ("Table", "Column", "Metric")]
    syn_cov = (sum(1 for n in entities if n["id"] in syn_targets) / max(1, len(entities)))
    check("synonym_coverage", "completeness", syn_cov >= 0.3, "info",
          f"{syn_cov:.0%} of entities have at least one synonym")

    # --- verdict (gate semantics) ---
    critical_failed = [c for c in checks if c["status"] == "failed" and c["severity"] == "critical"]
    warnings = [c for c in checks if c["status"] == "failed" and c["severity"] in ("warning", "info")]
    overall = "failed" if critical_failed else ("warning" if warnings else "passed")

    gaps = [{
        "gap_type": ("missing_description" if "description" in c["check_name"] else
                     "missing_relationship" if "relationship" in c["check_name"] else "low_confidence"),
        "entity": e, "recommendation": f"Review: {c['check_name']} — {c['details']}",
    } for c in checks if c["status"] == "failed" for e in (c["affected_entities"] or ["(global)"])[:10]]

    if overall == "failed":
        ctx.think(AID, f"🚫 GATE: {len(critical_failed)} critical check(s) failed — "
                       "this KG should NOT be published to production.")
    else:
        ctx.think(AID, f"Gate verdict: {overall.upper()} — KG is publishable"
                       + (f" ({len(warnings)} warning(s) for human review)." if warnings else "."))

    return {
        "validation_report": {
            "overall_status": overall,
            "validation_timestamp": datetime.now(timezone.utc).isoformat(),
            "checks": checks,
            "completeness_scores": {
                "tables_with_descriptions": round(t_score, 3),
                "columns_with_descriptions": round(c_score, 3),
                "relationships_mapped": round(len(rel_edges) / max(1, len(expected_tables)), 3),
                "synonyms_coverage": round(syn_cov, 3),
            },
            "quality_metrics": {
                "description_quality_avg": round((t_score + c_score) / 2, 3),
                "relationship_confidence_avg": round(conf_avg, 3),
                "semantic_coverage": round(syn_cov, 3),
            },
            "gaps_identified": gaps,
        },
        "_summary": f"{overall.upper()} · {sum(1 for c in checks if c['status'] == 'passed')}/{len(checks)} checks passed",
    }

"""Agent 12 · Neo4j Graph Builder 🔗 (the big join barrier) — materializes all
of A1–A11 as the knowledge graph.

The graph is always built in memory first (nodes + relationships JSON persisted
per run, so the UI and Stage 2 can consume it with zero infrastructure), then
flushed to Neo4j with idempotent MERGEs when PEAKSQL_NEO4J_URI is configured."""
from __future__ import annotations

import json
from datetime import datetime, timezone

from ..context import AgentContext

AID = "a12"


async def run(ctx: AgentContext, state: dict) -> dict:
    ctx.think(AID, "Join barrier reached — all upstream outputs available. Assembling the knowledge graph…")

    nodes: list[dict] = []
    rels: list[dict] = []

    def add_node(node_id: str, label: str, props: dict) -> str:
        nodes.append({"id": node_id, "label": label, "properties": props})
        return node_id

    def add_rel(rtype: str, source: str, target: str, props: dict | None = None) -> None:
        rels.append({"id": f"r{len(rels)}", "type": rtype, "source": source,
                     "target": target, "properties": props or {}})

    schema = state["a1"]
    db_name = schema["schema_metadata"]["database_name"]
    db_id = add_node(f"db:{db_name}", "Database", {"name": db_name,
                                                   "source_type": schema["schema_metadata"]["source_type"]})

    desc_by_table = {d["table_name"]: d for d in state["a4"]["descriptions"]}
    prof_by_table = {p["table_name"]: p for p in state["a2"].get("table_profiles", [])}
    domain_by_col = {(m["table_name"], c["column_name"]): c
                     for m in state["a5"]["domain_mappings"] for c in m["columns"]}
    naming_by_col = {(n["table_name"], c["column_name"]): c
                     for n in state["a3"]["naming_analysis"] for c in n["columns"]}

    # --- Table + Column nodes ---
    for t in schema["tables"]:
        tname = t["table_name"]
        d = desc_by_table.get(tname, {})
        td = d.get("table_descriptions", {})
        t_id = add_node(f"table:{tname}", "Table", {
            "name": tname, "row_count": t["row_count_estimate"],
            "description_technical": td.get("technical", ""),
            "description_business": td.get("business_friendly", ""),
            "description_short": td.get("short", ""),
            "entity_type": td.get("entity_type", ""),
            "update_frequency": d.get("update_frequency", ""),
            "synonyms": d.get("table_synonyms", []),
        })
        add_rel("HAS_TABLE", db_id, t_id)

        col_desc = {c["column_name"]: c for c in d.get("columns", [])}
        prof_cols = {c["column_name"]: c for c in prof_by_table.get(tname, {}).get("column_profiles", [])}
        for c in t["columns"]:
            cname = c["column_name"]
            cd = col_desc.get(cname, {})
            p = prof_cols.get(cname, {})
            nm = naming_by_col.get((tname, cname), {})
            dom = domain_by_col.get((tname, cname), {})
            c_id = add_node(f"col:{tname}.{cname}", "Column", {
                "name": cname, "table": tname, "data_type": c["data_type"],
                "is_primary_key": c["is_primary_key"], "is_foreign_key": c["is_foreign_key"],
                "is_nullable": c["is_nullable"],
                "description_short": cd.get("descriptions", {}).get("short", ""),
                "description_business": cd.get("descriptions", {}).get("business_friendly", ""),
                "semantic_type": nm.get("semantic_type", ""),
                "sample_values": p.get("sample_values", [])[:5],
                "enum_values": (p.get("value_patterns") or {}).get("enum_values"),
                "compliance_tags": dom.get("compliance_tags", []),
                "example_question": cd.get("example_question", ""),
            })
            add_rel("HAS_COLUMN", t_id, c_id)

    ctx.think(AID, f"Structural layer: {len(nodes)} nodes so far (Database, Table, Column) + HAS_* edges.")

    # --- BusinessConcept nodes ---
    for n in state["a3"]["naming_analysis"]:
        concept = n["decomposition"]["base_concept"]
        cid = f"concept:{concept}"
        if not any(x["id"] == cid for x in nodes):
            add_node(cid, "BusinessConcept", {"name": concept})
        add_rel("DESCRIBES", cid, f"table:{n['table_name']}")

    # --- Relationship edges from A8 ---
    for r in state["a8"]["enriched_relationships"]:
        rel_type = "FOREIGN_KEY" if r["origin"] == "explicit" else "IMPLICIT_RELATION"
        add_rel(rel_type, f"col:{r['source_table']}.{r['source_column']}",
                f"col:{r['target_table']}.{r['target_column']}", {
                    "semantic_type": r["semantic_type"],
                    "cardinality": r["cardinality"],
                    "business_meaning": r["business_meaning"],
                    "join_condition": r["join_path"]["join_condition"],
                    "confidence": r["confidence_score"],
                })

    # --- Metric nodes ---
    for m in state["a9"]["discovered_metrics"]:
        m_id = add_node(f"metric:{m['metric_id']}", "Metric", {
            "name": m["business_name"], "formula": m["calculation"]["formula"],
            "aggregation": m["calculation"]["aggregation_function"],
            "variants": m["natural_language_variants"],
            "business_context": m.get("business_context", ""),
        })
        add_rel("MEASURES", m_id, f"table:{m['base_table']}")
        if m["base_column"]:
            add_rel("MEASURES", m_id, f"col:{m['base_table']}.{m['base_column']}")

    # --- Synonym nodes ---
    n_syn = 0
    for sm in state["a11"]["synonym_mappings"]:
        target = _entity_node_id(sm)
        if target is None:
            continue
        for s in sm["synonyms"]:
            syn_id = f"syn:{s['synonym']}|{target}"
            add_node(syn_id, "Synonym", {"term": s["synonym"], "context": s["context"],
                                         "confidence": s["confidence"]})
            add_rel("SYNONYM_OF", syn_id, target)
            n_syn += 1

    # --- QueryPattern nodes ---
    for qp in state["a10"]["query_patterns"]:
        qp_id = add_node(f"pattern:{qp['pattern_id']}", "QueryPattern", {
            "name": qp["pattern_name"], "type": qp["pattern_type"],
            "nl_templates": qp["natural_language_templates"],
            "structure": json.dumps(qp["typical_structure"]),
        })
        for tbl in qp["typical_structure"]["from_tables"]:
            add_rel("MAPS_TO", qp_id, f"table:{tbl}")

    label_counts: dict[str, int] = {}
    for n in nodes:
        label_counts[n["label"]] = label_counts.get(n["label"], 0) + 1
    type_counts: dict[str, int] = {}
    for r in rels:
        type_counts[r["type"]] = type_counts.get(r["type"], 0) + 1

    ctx.think(AID, f"In-memory KG complete: {len(nodes)} nodes ({label_counts}), "
                   f"{len(rels)} relationships ({type_counts}).")

    # persist the graph for the UI + Stage 2
    run_dir = ctx.settings.runs_dir / ctx.run.run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "kg.json").write_text(json.dumps({"nodes": nodes, "relationships": rels}, default=str))

    # optional Neo4j flush
    neo4j_status = "skipped (PEAKSQL_NEO4J_URI not configured)"
    errors: list[str] = []
    if ctx.settings.neo4j_uri:
        try:
            _flush_to_neo4j(ctx, nodes, rels)
            neo4j_status = f"written to {ctx.settings.neo4j_uri}"
            ctx.think(AID, f"Flushed graph to Neo4j at {ctx.settings.neo4j_uri} (idempotent MERGEs, single transaction).")
        except Exception as e:  # noqa: BLE001
            neo4j_status = f"failed: {e}"
            errors.append(str(e))
            ctx.think(AID, f"⚠️ Neo4j write failed ({e}) — in-memory KG remains authoritative for this run.")
    else:
        ctx.think(AID, "Neo4j not configured — in-memory KG persisted to kg.json (fully queryable by the UI).")

    return {
        "graph_statistics": {
            "total_nodes": len(nodes),
            "total_relationships": len(rels),
            "node_counts_by_label": label_counts,
            "relationship_counts_by_type": type_counts,
        },
        "construction_log": {
            "build_timestamp": datetime.now(timezone.utc).isoformat(),
            "neo4j": neo4j_status,
            "errors": errors or None,
        },
        "_summary": f"{len(nodes)} nodes · {len(rels)} rels · neo4j: {neo4j_status.split(' ')[0]}",
    }


def _entity_node_id(sm: dict) -> str | None:
    ref = sm["entity_reference"]
    if sm["entity_type"] == "table":
        return f"table:{ref}"
    if sm["entity_type"] == "column":
        return f"col:{ref}"
    if sm["entity_type"] == "metric":
        return f"metric:{ref}"
    return None


def _flush_to_neo4j(ctx: AgentContext, nodes: list[dict], rels: list[dict]) -> None:
    from neo4j import GraphDatabase

    s = ctx.settings
    driver = GraphDatabase.driver(s.neo4j_uri, auth=(s.neo4j_user, s.neo4j_password))
    try:
        with driver.session(database=s.neo4j_database) as session:
            def tx_fn(tx):
                for n in nodes:
                    props = {k: (json.dumps(v) if isinstance(v, (dict, list)) else v)
                             for k, v in n["properties"].items() if v is not None}
                    tx.run(f"MERGE (x:`{n['label']}` {{uid: $uid}}) SET x += $props",
                           uid=n["id"], props=props)
                for r in rels:
                    props = {k: (json.dumps(v) if isinstance(v, (dict, list)) else v)
                             for k, v in r["properties"].items() if v is not None}
                    tx.run(f"MATCH (a {{uid: $src}}), (b {{uid: $tgt}}) "
                           f"MERGE (a)-[rel:`{r['type']}`]->(b) SET rel += $props",
                           src=r["source"], tgt=r["target"], props=props)
            session.execute_write(tx_fn)
    finally:
        driver.close()

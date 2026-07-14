"""Agent 7 · Implicit Relationship Detector — finds relationships the schema
never declared, via three signals: naming patterns, value overlap (from the
profiler), and semantic name similarity. Each candidate carries a confidence
score and a requires_validation flag."""
from __future__ import annotations

import uuid
from difflib import SequenceMatcher

from ..context import AgentContext
from .a03_naming_analyzer import expand, split_name

AID = "a7"


async def run(ctx: AgentContext, state: dict) -> dict:
    schema, profiles, naming = state["a1"], state["a2"], state["a3"]
    tables = schema["tables"]
    declared = {(r_t["table_name"], c["columns"][0], c["referenced_table"])
                for r_t in tables for c in r_t["constraints"]
                if c["constraint_type"] == "FK" and c["columns"]}

    ctx.think(AID, "Hunting for undeclared relationships via naming patterns, value overlap and semantic similarity…")
    found: list[dict] = []
    seen: set[tuple] = set()

    # --- signal 1: profiler value overlap ---
    for p in profiles.get("table_profiles", []):
        for rel in p.get("potential_relationships", []):
            key = (p["table_name"], rel["source_column"], rel["target_table"])
            if key in declared or key in seen:
                continue
            seen.add(key)
            conf = rel["confidence"]
            found.append(_mk(p["table_name"], rel["source_column"], rel["target_table"],
                             rel["target_column"], "value_overlap", conf,
                             overlap=rel["overlap_percentage"]))
            ctx.think(AID, f"Value overlap: `{p['table_name']}.{rel['source_column']}` → "
                           f"`{rel['target_table']}.{rel['target_column']}` "
                           f"({rel['overlap_percentage']}% contained, confidence {conf}).")

    # --- signal 2: naming pattern (same id-ish column name, one side is a PK) ---
    pk_index: dict[str, tuple[str, str]] = {}
    single_pk: dict[str, list[str]] = {}
    for t in tables:
        pk = next((c2["columns"] for c2 in t["constraints"] if c2["constraint_type"] == "PK"), [])
        single_pk[t["table_name"]] = pk
        for c in t["columns"]:
            if c["is_primary_key"] and len(pk) == 1:
                pk_index[c["column_name"].lower()] = (t["table_name"], c["column_name"])
    for t in tables:
        for c in t["columns"]:
            low = c["column_name"].lower()
            is_sole_pk = c["is_primary_key"] and len(single_pk[t["table_name"]]) == 1
            if is_sole_pk or not low.endswith(("_id", "id")):
                continue
            hit = pk_index.get(low)
            if not hit or hit[0] == t["table_name"]:
                continue
            key = (t["table_name"], c["column_name"], hit[0])
            if key in declared or key in seen:
                continue
            seen.add(key)
            found.append(_mk(t["table_name"], c["column_name"], hit[0], hit[1],
                             "naming_pattern", 0.75, naming_sim=1.0))
            ctx.think(AID, f"Naming pattern: `{t['table_name']}.{c['column_name']}` matches PK of "
                           f"`{hit[0]}` — likely joinable (confidence 0.75).")

    # --- signal 3: semantic similarity on expanded business terms ---
    expanded: list[tuple[str, str, str]] = []  # (table, column, expanded name)
    for a in naming["naming_analysis"]:
        for c in a["columns"]:
            if c["semantic_type"] == "identifier":
                expanded.append((a["table_name"], c["column_name"], " ".join(c["decomposed_terms"])))
    for i, (t1, c1, e1) in enumerate(expanded):
        for t2, c2, e2 in expanded[i + 1:]:
            if t1 == t2 or e1 == e2:
                continue
            sim = SequenceMatcher(None, e1, e2).ratio()
            if sim >= 0.85:
                key = (t1, c1, t2)
                if key in declared or key in seen:
                    continue
                seen.add(key)
                found.append(_mk(t1, c1, t2, c2, "semantic_similarity", round(0.5 + 0.3 * sim, 2),
                                 semantic_sim=round(sim, 2)))
                ctx.think(AID, f"Semantic similarity: `{t1}.{c1}` ~ `{t2}.{c2}` "
                               f"(“{e1}” vs “{e2}”, sim {sim:.2f}).")

    # --- hierarchies: self-referencing columns ---
    hierarchies = []
    for t in tables:
        pk = next((c["column_name"] for c in t["columns"] if c["is_primary_key"]), None)
        if not pk:
            continue
        for c in t["columns"]:
            low = c["column_name"].lower()
            terms = [expand(p) for p in split_name(c["column_name"])]
            if c["column_name"] != pk and low.endswith(("_id",)) and (
                    "parent" in terms or "manager" in terms
                    or low.replace("parent_", "").replace("manager_", "") == pk.lower()):
                hierarchies.append({"table_name": t["table_name"], "parent_column": c["column_name"],
                                    "child_column": pk, "hierarchy_type": "self_referencing",
                                    "levels": None})
                ctx.think(AID, f"Self-referencing hierarchy: `{t['table_name']}.{c['column_name']}` → own PK.")

    if not found and not hierarchies:
        ctx.think(AID, "No undeclared relationships found — schema constraints appear complete.")
    return {
        "implicit_relationships": found,
        "hierarchical_relationships": hierarchies,
        "_summary": f"{len(found)} implicit candidates · {len(hierarchies)} hierarchies",
    }


def _mk(st: str, sc: str, tt: str, tc: str, method: str, conf: float,
        overlap: float | None = None, naming_sim: float | None = None,
        semantic_sim: float | None = None) -> dict:
    return {
        "relationship_id": str(uuid.uuid4()),
        "source_table": st, "source_column": sc,
        "target_table": tt, "target_column": tc,
        "detection_method": method,
        "confidence_score": conf,
        "evidence": {"value_overlap_percentage": overlap,
                     "naming_similarity_score": naming_sim,
                     "semantic_similarity_score": semantic_sim},
        "suggested_cardinality": "1:N",
        "requires_validation": conf < 0.8,
    }

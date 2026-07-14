"""Agent 6 · Explicit Relationship Extractor — declared FKs, junction tables,
unique constraints. Ground truth: no inference, confidence 1.0."""
from __future__ import annotations

import uuid

from ..context import AgentContext

AID = "a6"


async def run(ctx: AgentContext, state: dict) -> dict:
    schema = state["a1"]
    tables = {t["table_name"]: t for t in schema["tables"]}
    ctx.think(AID, "Extracting declared constraints — these are ground truth (confidence 1.0).")

    relationships = []
    for t in schema["tables"]:
        for c in t["constraints"]:
            if c["constraint_type"] != "FK" or not c.get("referenced_table"):
                continue
            target = tables.get(c["referenced_table"])
            # 1:1 if the FK column is itself unique/PK on the source; else 1:N (target side is one)
            src_cols = c["columns"]
            src_pk = {col["column_name"] for col in t["columns"] if col["is_primary_key"]}
            cardinality = "1:1" if set(src_cols) == src_pk and len(src_pk) == len(src_cols) else "1:N"
            relationships.append({
                "relationship_id": str(uuid.uuid4()),
                "source_table": t["table_name"],
                "source_column": src_cols[0] if src_cols else "",
                "target_table": c["referenced_table"],
                "target_column": (c.get("referenced_columns") or [""])[0]
                                  or _pk_of(target),
                "relationship_type": "foreign_key",
                "cardinality": cardinality,
                "is_enforced": True,
                "constraint_name": None,
                "on_delete": None,
                "on_update": None,
            })
            ctx.think(AID, f"FK: `{t['table_name']}.{src_cols[0] if src_cols else '?'}` → "
                           f"`{c['referenced_table']}` ({cardinality}).")

    junctions = []
    for t in schema["tables"]:
        fk_constraints = [c for c in t["constraints"] if c["constraint_type"] == "FK"]
        pk_cols = next((c["columns"] for c in t["constraints"] if c["constraint_type"] == "PK"), [])
        fk_cols = {col for c in fk_constraints for col in c["columns"]}
        # composite PK made (mostly) of FK columns, or a small table with >=2 FKs → junction
        is_junction = (len(fk_constraints) >= 2
                       and ((len(pk_cols) >= 2 and set(pk_cols) <= fk_cols)
                            or len(t["columns"]) <= len(fk_cols) + 3))
        if is_junction:
            connects = [{"table": c["referenced_table"], "via_column": c["columns"][0]}
                        for c in fk_constraints]
            junctions.append({"table_name": t["table_name"], "connects": connects,
                              "relationship_type": "many_to_many"})
            ctx.think(AID, f"Junction table detected: `{t['table_name']}` bridges "
                           f"{[c['table'] for c in connects]} (many-to-many).")

    return {
        "explicit_relationships": relationships,
        "junction_tables": junctions,
        "_summary": f"{len(relationships)} declared FKs · {len(junctions)} junction tables",
    }


def _pk_of(table: dict | None) -> str:
    if not table:
        return ""
    return next((c["column_name"] for c in table["columns"] if c["is_primary_key"]), "")
